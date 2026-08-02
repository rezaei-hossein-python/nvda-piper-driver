"""One-shot Piper child used only by the controlled Phase 2I driver."""

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


def _fail(message: str) -> None:
	# Fixed messages only: never write request text or native exception detail.
	sys.stderr.write(message)
	raise SystemExit(2)


def main() -> int:
	parser = argparse.ArgumentParser(add_help=False)
	parser.add_argument("--model", required=True)
	parser.add_argument("--config", required=True)
	args = parser.parse_args()
	model = Path(args.model).resolve(strict=False)
	config = Path(args.config).resolve(strict=False)
	if model.suffix.lower() != ".onnx" or not model.is_file():
		_fail("invalid model")
	if config.suffix.lower() != ".json" or not config.is_file():
		_fail("invalid configuration")
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

		voice = PiperVoice.load(str(model), config_path=str(config), use_cuda=False)
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
