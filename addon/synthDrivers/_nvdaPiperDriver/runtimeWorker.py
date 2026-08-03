"""Bounded Piper child supporting one-shot and persistent development requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys


MAX_REQUEST_BYTES = 65_536
MAX_TEXT_CODE_POINTS = 16_384
MAX_PCM_BYTES = 32 * 1024 * 1024
_HEADER_LENGTH = struct.Struct("<I")
_PERSISTENT_REQUEST_LENGTH = struct.Struct("<I")


def _fail(message: str) -> None:
	# Fixed messages only: never write request text or native exception detail.
	sys.stderr.write(message)
	raise SystemExit(2)


def _readExact(stream, length: int) -> bytes:
	parts: list[bytes] = []
	remaining = length
	while remaining:
		part = stream.read(remaining)
		if not part:
			return b""
		parts.append(part)
		remaining -= len(part)
	return b"".join(parts)


def _loadVoice(model: Path, config: Path):
	try:
		from piper import PiperVoice
	except Exception:
		_fail("runtime initialization failed")
	try:
		return PiperVoice.load(str(model), config_path=str(config), use_cuda=False)
	except Exception:
		_fail("model load failed")


def _synthesize(voice, text: str, synConfig) -> tuple[bytes, int]:
	try:
		parts: list[bytes] = []
		total = 0
		for chunk in voice.synthesize(text, syn_config=synConfig):
			audio = chunk.audio_int16_bytes
			total += len(audio)
			if total > MAX_PCM_BYTES:
				_fail("audio limit exceeded")
			parts.append(audio)
		return b"".join(parts), voice.config.sample_rate
	except SystemExit:
		raise
	except Exception:
		_fail("synthesis failed")
	return b"", 0


def _warmVoice(voice, synConfig) -> None:
	"""Initialize backend execution without producing user-visible audio."""
	try:
		# Piper accepts an empty synthesis request and yields no audio. This is
		# deliberately language-neutral and warms phonemizer/ORT execution only.
		for _ in voice.synthesize("", syn_config=synConfig):
			_fail("warm-up produced audio")
	except SystemExit:
		raise
	except Exception:
		_fail("runtime warm-up failed")


def _writePersistentFrame(header: dict[str, object], pcm: bytes = b"") -> None:
	headerBytes = json.dumps(header, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
	if len(headerBytes) > 4_096:
		_fail("protocol failure")
	sys.stdout.buffer.write(_HEADER_LENGTH.pack(len(headerBytes)))
	sys.stdout.buffer.write(headerBytes)
	sys.stdout.buffer.write(pcm)
	sys.stdout.buffer.flush()


def _persistentMain(model: Path, config: Path) -> int:
	voice = _loadVoice(model, config)
	try:
		from piper import SynthesisConfig
		synConfig = SynthesisConfig()
	except Exception:
		_fail("runtime initialization failed")
	_warmVoice(voice, synConfig)
	_writePersistentFrame({"type": "ready", "sampleRate": voice.config.sample_rate})
	while True:
		lengthBytes = _readExact(sys.stdin.buffer, _PERSISTENT_REQUEST_LENGTH.size)
		if not lengthBytes:
			return 0
		length = _PERSISTENT_REQUEST_LENGTH.unpack(lengthBytes)[0]
		if not 1 <= length <= MAX_REQUEST_BYTES:
			_fail("invalid request")
		payload = _readExact(sys.stdin.buffer, length)
		if not payload:
			_fail("invalid request")
		try:
			request = json.loads(payload.decode("utf-8"))
		except (UnicodeDecodeError, json.JSONDecodeError):
			_fail("invalid request")
		if type(request) is not dict or set(request) != {"generationId", "jobId", "text", "segmentNumber", "characterMode", "indexesAfter"}:
			_fail("invalid request")
		if type(request["text"]) is not str or not request["text"] or len(request["text"]) > MAX_TEXT_CODE_POINTS:
			_fail("invalid request")
		for name in ("generationId", "jobId", "segmentNumber"):
			value = request[name]
			if type(value) is not int or not 1 <= value <= (1 << 63) - 1:
				_fail("invalid request")
		if type(request["characterMode"]) is not bool or type(request["indexesAfter"]) is not list:
			_fail("invalid request")
		if any(type(index) is not int or not 0 <= index <= (1 << 63) - 1 for index in request["indexesAfter"]):
			_fail("invalid request")
		try:
			pcm, sampleRate = _synthesize(voice, request["text"], synConfig)
			if not pcm or len(pcm) % 2 or type(sampleRate) is not int:
				_fail("invalid audio")
			_writePersistentFrame({"channels": 1, "generationId": request["generationId"], "jobId": request["jobId"], "sampleRate": sampleRate, "sampleWidth": 2, "pcmBytes": len(pcm), "segmentNumber": request["segmentNumber"], "indexesAfter": request["indexesAfter"]}, pcm)
		except SystemExit:
			raise
		except Exception:
			_fail("synthesis failed")


def main() -> int:
	parser = argparse.ArgumentParser(add_help=False)
	parser.add_argument("--model", required=True)
	parser.add_argument("--config", required=True)
	parser.add_argument("--persistent", action="store_true")
	args = parser.parse_args()
	model = Path(args.model).resolve(strict=False)
	config = Path(args.config).resolve(strict=False)
	if model.suffix.lower() != ".onnx" or not model.is_file():
		_fail("invalid model")
	if config.suffix.lower() != ".json" or not config.is_file():
		_fail("invalid configuration")
	if args.persistent:
		return _persistentMain(model, config)
	requestBytes = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
	if not requestBytes or len(requestBytes) > MAX_REQUEST_BYTES:
		_fail("invalid request")
	try:
		request = json.loads(requestBytes.decode("utf-8"))
	except (UnicodeDecodeError, json.JSONDecodeError):
		_fail("invalid request")
	if type(request) is not dict or set(request) != {"generationId", "jobId", "text"}:
		_fail("invalid request")
	text = request["text"]
	if type(text) is not str or not text or len(text) > MAX_TEXT_CODE_POINTS:
		_fail("invalid request")
	for name in ("generationId", "jobId"):
		value = request[name]
		if type(value) is not int or not 1 <= value <= (1 << 63) - 1:
			_fail("invalid request")
	try:
		from piper import PiperVoice, SynthesisConfig
	except Exception:
		_fail("runtime initialization failed")
	try:
		voice = PiperVoice.load(str(model), config_path=str(config), use_cuda=False)
	except Exception:
		_fail("model load failed")
	try:
		pcmParts: list[bytes] = []
		pcmBytes = 0
		for chunk in voice.synthesize(text, syn_config=SynthesisConfig()):
			audio = chunk.audio_int16_bytes
			pcmBytes += len(audio)
			if pcmBytes > MAX_PCM_BYTES:
				_fail("audio limit exceeded")
			pcmParts.append(audio)
		sampleRate = voice.config.sample_rate
	except SystemExit:
		raise
	except Exception:
		_fail("synthesis failed")
	pcm = b"".join(pcmParts)
	if not pcm or len(pcm) % 2 or type(sampleRate) is not int:
		_fail("invalid audio")
	header = json.dumps(
		{
			"channels": 1,
			"generationId": request["generationId"],
			"jobId": request["jobId"],
			"sampleRate": sampleRate,
			"sampleWidth": 2,
		},
		allow_nan=False,
		separators=(",", ":"),
		sort_keys=True,
	).encode("utf-8")
	sys.stdout.buffer.write(_HEADER_LENGTH.pack(len(header)))
	sys.stdout.buffer.write(header)
	sys.stdout.buffer.write(pcm)
	sys.stdout.buffer.flush()
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
