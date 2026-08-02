"""Development-only, synchronous child-process bridge for one Piper utterance."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import struct
import subprocess
from typing import Final


MAX_TEXT_CODE_POINTS: Final = 16_384
MAX_PCM_BYTES: Final = 32 * 1024 * 1024
MAX_HEADER_BYTES: Final = 4_096
MAX_ERROR_BYTES: Final = 4_096
MAX_CONFIG_BYTES: Final = 1_048_576
WORKER_TIMEOUT_SECONDS: Final = 60
_HEADER_LENGTH = struct.Struct("<I")


class RuntimeBridgeError(Exception):
	"""A bounded, content-free development runtime failure."""


@dataclass(frozen=True, slots=True)
class PcmResult:
	generationId: int
	jobId: int
	sampleRate: int
	channels: int
	sampleWidth: int
	pcm: bytes


def _requireFile(value: object, suffix: str, label: str) -> Path:
	if type(value) is not str or not value:
		raise RuntimeBridgeError(f"{label} path is not configured")
	path = Path(value).resolve(strict=False)
	if path.suffix.lower() != suffix or not path.is_file():
		raise RuntimeBridgeError(f"{label} path is invalid")
	return path


def validateRuntimePaths(runtimePath: object, modelPath: object, configPath: object) -> tuple[Path, Path, Path]:
	"""Validate only explicit local files; never discover or download assets."""
	runtime = _requireFile(runtimePath, ".exe", "runtime")
	model = _requireFile(modelPath, ".onnx", "model")
	config = _requireFile(configPath, ".json", "configuration")
	return runtime, model, config


def readModelLanguage(configPath: str | Path) -> str:
	"""Read only the model-provided language code used for NVDA voice metadata."""
	config = Path(configPath).resolve(strict=False)
	try:
		if config.stat().st_size > MAX_CONFIG_BYTES:
			raise RuntimeBridgeError("configuration metadata exceeds the development limit")
		data = json.loads(config.read_bytes().decode("utf-8"))
		language = data["language"]["code"]
	except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
		raise RuntimeBridgeError("configuration language metadata is invalid") from error
	if type(language) is not str or not language or len(language) > 64:
		raise RuntimeBridgeError("configuration language metadata is invalid")
	return language


class OneShotRuntimeBridge:
	"""Own at most one synchronous, one-request worker process."""

	def __init__(self, runtimePath: str, modelPath: str, configPath: str, workerPath: str) -> None:
		self._runtimePath, self._modelPath, self._configPath = validateRuntimePaths(
			runtimePath,
			modelPath,
			configPath,
		)
		self._workerPath = _requireFile(workerPath, ".py", "worker")
		self._process: subprocess.Popen[bytes] | None = None

	@property
	def processId(self) -> int | None:
		process = self._process
		return process.pid if process is not None and process.poll() is None else None

	def synthesize(self, text: str, generationId: int, jobId: int) -> PcmResult:
		if type(text) is not str or not text or len(text) > MAX_TEXT_CODE_POINTS:
			raise RuntimeBridgeError("speech text is empty or exceeds the development limit")
		for value, label in ((generationId, "generation"), (jobId, "job")):
			if type(value) is not int or not 1 <= value <= (1 << 63) - 1:
				raise RuntimeBridgeError(f"{label} identifier is invalid")
		if self.processId is not None:
			raise RuntimeBridgeError("the development worker is already active")
		request = json.dumps(
			{"generationId": generationId, "jobId": jobId, "text": text},
			ensure_ascii=False,
			allow_nan=False,
			separators=(",", ":"),
			sort_keys=True,
		).encode("utf-8")
		command = [
			str(self._runtimePath),
			"-I",
			str(self._workerPath),
			"--model",
			str(self._modelPath),
			"--config",
			str(self._configPath),
		]
		environment = os.environ.copy()
		for name in tuple(environment):
			if name.upper().startswith("PYTHON"):
				environment.pop(name, None)
		try:
			process = subprocess.Popen(
				command,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				shell=False,
				env=environment,
				creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
			)
			self._process = process
			stdout, stderr = process.communicate(input=request, timeout=WORKER_TIMEOUT_SECONDS)
		except subprocess.TimeoutExpired as error:
			process.terminate()
			try:
				process.wait(timeout=5)
			except subprocess.TimeoutExpired:
				process.kill()
				process.wait(timeout=5)
			raise RuntimeBridgeError("the development worker timed out") from error
		except OSError as error:
			raise RuntimeBridgeError("the development worker could not be started") from error
		finally:
			self._process = None
		if process.returncode != 0:
			# Never decode or expose worker stderr because native dependencies may include paths.
			_ = stderr[:MAX_ERROR_BYTES]
			raise RuntimeBridgeError("the development worker failed")
		return self._decodeResponse(stdout, generationId, jobId)

	@staticmethod
	def _decodeResponse(payload: bytes, generationId: int, jobId: int) -> PcmResult:
		if len(payload) < _HEADER_LENGTH.size:
			raise RuntimeBridgeError("the development worker returned a malformed response")
		headerLength = _HEADER_LENGTH.unpack_from(payload)[0]
		if not 1 <= headerLength <= MAX_HEADER_BYTES:
			raise RuntimeBridgeError("the development worker returned an invalid header")
		headerEnd = _HEADER_LENGTH.size + headerLength
		if headerEnd > len(payload) or len(payload) - headerEnd > MAX_PCM_BYTES:
			raise RuntimeBridgeError("the development worker response exceeds its bounds")
		try:
			header = json.loads(payload[_HEADER_LENGTH.size:headerEnd].decode("utf-8"))
		except (UnicodeDecodeError, json.JSONDecodeError) as error:
			raise RuntimeBridgeError("the development worker returned an invalid header") from error
		expectedFields = {"channels", "generationId", "jobId", "sampleRate", "sampleWidth"}
		if type(header) is not dict or set(header) != expectedFields:
			raise RuntimeBridgeError("the development worker returned an invalid header")
		for name in expectedFields:
			if type(header[name]) is not int:
				raise RuntimeBridgeError("the development worker returned invalid metadata")
		if header["generationId"] != generationId or header["jobId"] != jobId:
			raise RuntimeBridgeError("the development worker returned stale PCM")
		if header["channels"] != 1 or header["sampleWidth"] != 2 or not 8_000 <= header["sampleRate"] <= 192_000:
			raise RuntimeBridgeError("the development worker returned an unsupported PCM format")
		pcm = payload[headerEnd:]
		if not pcm or len(pcm) % 2:
			raise RuntimeBridgeError("the development worker returned invalid PCM")
		return PcmResult(generationId, jobId, header["sampleRate"], 1, 2, pcm)

	def stop(self) -> None:
		process = self._process
		if process is None or process.poll() is not None:
			return
		process.terminate()
		try:
			process.wait(timeout=5)
		except subprocess.TimeoutExpired:
			process.kill()
			process.wait(timeout=5)
