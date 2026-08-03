"""Development-only blocking child bridge, owned only by the background controller."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import struct
import subprocess
import threading
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

	def __init__(self, code: str, message: str) -> None:
		self.code = code
		super().__init__(message)


class RuntimeBridgeCancelled(RuntimeBridgeError):
	def __init__(self) -> None:
		super().__init__("cancelled", "the development worker was cancelled")


def _error(code: str, message: str) -> RuntimeBridgeError:
	return RuntimeBridgeError(code, message)


@dataclass(frozen=True, slots=True)
class PcmResult:
	generationId: int
	jobId: int
	sampleRate: int
	channels: int
	sampleWidth: int
	pcm: bytes
	latencyTrace: object | None = None


def _requireFile(value: object, suffix: str, label: str) -> Path:
	if type(value) is not str or not value:
		raise _error("invalidPath", f"{label} path is not configured")
	path = Path(value).resolve(strict=False)
	if path.suffix.lower() != suffix or not path.is_file():
		raise _error("invalidPath", f"{label} path is invalid")
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
			raise _error("invalidConfiguration", "configuration metadata exceeds the development limit")
		data = json.loads(config.read_bytes().decode("utf-8"))
		language = data["language"]["code"]
	except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
		raise _error("invalidConfiguration", "configuration language metadata is invalid") from error
	if type(language) is not str or not language or len(language) > 64:
		raise _error("invalidConfiguration", "configuration language metadata is invalid")
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
		self._processLock = threading.Lock()
		self._cancellationToken = 0

	@property
	def processId(self) -> int | None:
		with self._processLock:
			process = self._process
		return process.pid if process is not None and process.poll() is None else None

	@property
	def cancellationToken(self) -> int:
		with self._processLock:
			return self._cancellationToken

	def synthesize(self, text: str, generationId: int, jobId: int, *, cancellationToken: int | None = None) -> PcmResult:
		if type(text) is not str or not text or len(text) > MAX_TEXT_CODE_POINTS:
			raise _error("invalidRequest", "speech text is empty or exceeds the development limit")
		for value, label in ((generationId, "generation"), (jobId, "job")):
			if type(value) is not int or not 1 <= value <= (1 << 63) - 1:
				raise _error("invalidRequest", f"{label} identifier is invalid")
		with self._processLock:
			token = self._cancellationToken if cancellationToken is None else cancellationToken
			if token != self._cancellationToken:
				raise RuntimeBridgeCancelled()
			if self._process is not None:
				raise _error("workerBusy", "the development worker is already active")
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
		process: subprocess.Popen[bytes] | None = None
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
			with self._processLock:
				self._process = process
				cancelled = token != self._cancellationToken
			if cancelled:
				process.terminate()
			stdout, stderr = process.communicate(input=request, timeout=WORKER_TIMEOUT_SECONDS)
		except subprocess.TimeoutExpired as error:
			process.terminate()
			try:
				process.wait(timeout=5)
			except subprocess.TimeoutExpired:
				process.kill()
				process.wait(timeout=5)
			raise _error("workerHang", "the development worker timed out") from error
		except OSError as error:
			raise _error("workerStartupFailure", "the development worker could not be started") from error
		finally:
			with self._processLock:
				if process is not None and self._process is process:
					self._process = None
		if process is None:
			raise _error("workerStartupFailure", "the development worker could not be started")
		if token != self.cancellationToken:
			raise RuntimeBridgeCancelled()
		if process.returncode != 0:
			fixedError = stderr[:MAX_ERROR_BYTES]
			code = {
				b"runtime initialization failed": "runtimeInitializationFailure",
				b"model load failed": "modelLoadFailure",
			}.get(fixedError, "workerCrash")
			raise _error(code, "the development worker failed")
		return self._decodeResponse(stdout, generationId, jobId)

	@staticmethod
	def _decodeResponse(payload: bytes, generationId: int, jobId: int) -> PcmResult:
		if len(payload) < _HEADER_LENGTH.size:
			raise _error("protocolFailure", "the development worker returned a malformed response")
		headerLength = _HEADER_LENGTH.unpack_from(payload)[0]
		if not 1 <= headerLength <= MAX_HEADER_BYTES:
			raise _error("protocolFailure", "the development worker returned an invalid header")
		headerEnd = _HEADER_LENGTH.size + headerLength
		if headerEnd > len(payload) or len(payload) - headerEnd > MAX_PCM_BYTES:
			raise _error("protocolFailure", "the development worker response exceeds its bounds")
		try:
			header = json.loads(payload[_HEADER_LENGTH.size:headerEnd].decode("utf-8"))
		except (UnicodeDecodeError, json.JSONDecodeError) as error:
			raise _error("protocolFailure", "the development worker returned an invalid header") from error
		expectedFields = {"channels", "generationId", "jobId", "sampleRate", "sampleWidth"}
		if type(header) is not dict or set(header) != expectedFields:
			raise _error("protocolFailure", "the development worker returned an invalid header")
		for name in expectedFields:
			if type(header[name]) is not int:
				raise _error("protocolFailure", "the development worker returned invalid metadata")
		if header["generationId"] != generationId or header["jobId"] != jobId:
			raise _error("staleResult", "the development worker returned stale PCM")
		if header["channels"] != 1 or header["sampleWidth"] != 2 or not 8_000 <= header["sampleRate"] <= 192_000:
			raise _error("invalidPcm", "the development worker returned an unsupported PCM format")
		pcm = payload[headerEnd:]
		if not pcm or len(pcm) % 2:
			raise _error("invalidPcm", "the development worker returned invalid PCM")
		return PcmResult(generationId, jobId, header["sampleRate"], 1, 2, pcm)

	def interrupt(self) -> None:
		"""Invalidate current work and request termination without waiting."""
		with self._processLock:
			self._cancellationToken += 1
			process = self._process
			self._restartCount = 0
		if process is None or process.poll() is not None:
			return
		try:
			process.terminate()
		except OSError:
			pass

	def stop(self) -> None:
		self.interrupt()
		with self._processLock:
			process = self._process
		if process is None or process.poll() is not None:
			return
		try:
			process.wait(timeout=5)
		except subprocess.TimeoutExpired:
			process.kill()
			process.wait(timeout=5)

	def forceStop(self) -> None:
		"""Use the bounded shutdown fallback without waiting on the caller."""
		with self._processLock:
			self._cancellationToken += 1
			process = self._process
		if process is None or process.poll() is not None:
			return
		try:
			process.kill()
		except OSError:
			pass


class PersistentRuntimeBridge:
	"""A single framed child that loads one model and serves bounded requests."""

	MAX_RESTARTS: Final = 3

	def __init__(self, runtimePath: str, modelPath: str, configPath: str, workerPath: str) -> None:
		self._runtimePath, self._modelPath, self._configPath = validateRuntimePaths(runtimePath, modelPath, configPath)
		self._workerPath = _requireFile(workerPath, ".py", "worker")
		self._process: subprocess.Popen[bytes] | None = None
		self._processLock = threading.Lock()
		self._cancellationToken = 0
		self._restartCount = 0

	@property
	def processId(self) -> int | None:
		with self._processLock:
			process = self._process
		return process.pid if process is not None and process.poll() is None else None

	@property
	def cancellationToken(self) -> int:
		with self._processLock:
			return self._cancellationToken

	@staticmethod
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

	def _start(self) -> subprocess.Popen[bytes]:
		with self._processLock:
			if self._process is not None and self._process.poll() is None:
				return self._process
			if self._restartCount >= self.MAX_RESTARTS:
				raise _error("restartLimit", "the development worker restart limit was reached")
			self._restartCount += 1
		environment = os.environ.copy()
		for name in tuple(environment):
			if name.upper().startswith("PYTHON"):
				environment.pop(name, None)
		command = [str(self._runtimePath), "-I", str(self._workerPath), "--persistent", "--model", str(self._modelPath), "--config", str(self._configPath)]
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
		except OSError as error:
			raise _error("workerStartupFailure", "the development worker could not be started") from error
		with self._processLock:
			self._process = process
		try:
			header = self._readFrame(process, readyOnly=True)
			if header.get("type") != "ready" or type(header.get("sampleRate")) is not int:
				raise _error("protocolFailure", "the development worker handshake was invalid")
			# A successfully initialized worker clears consecutive-start failures;
			# the limit still bounds repeated failed starts in one session.
			self._restartCount = 0
			return process
		except Exception as error:
			self._terminateProcess(process)
			with self._processLock:
				if self._process is process:
					self._process = None
			if isinstance(error, RuntimeBridgeError):
				raise
			raise _error("workerStartupFailure", "the development worker handshake failed") from error

	@classmethod
	def _readFrame(cls, process: subprocess.Popen[bytes], readyOnly: bool = False) -> dict[str, object]:
		assert process.stdout is not None
		lengthBytes = cls._readExact(process.stdout, _HEADER_LENGTH.size)
		if len(lengthBytes) != _HEADER_LENGTH.size:
			raise _error("workerCrash", "the development worker closed unexpectedly")
		length = _HEADER_LENGTH.unpack(lengthBytes)[0]
		if not 1 <= length <= MAX_HEADER_BYTES:
			raise _error("protocolFailure", "the development worker returned an invalid header")
		headerBytes = cls._readExact(process.stdout, length)
		try:
			header = json.loads(headerBytes.decode("utf-8"))
		except (UnicodeDecodeError, json.JSONDecodeError) as error:
			raise _error("protocolFailure", "the development worker returned an invalid header") from error
		if type(header) is not dict:
			raise _error("protocolFailure", "the development worker returned an invalid header")
		if readyOnly:
			return header
		pcmBytes = header.get("pcmBytes")
		if type(pcmBytes) is not int or not 0 < pcmBytes <= MAX_PCM_BYTES or pcmBytes % 2:
			raise _error("invalidPcm", "the development worker returned invalid PCM metadata")
		pcm = cls._readExact(process.stdout, pcmBytes)
		if len(pcm) != pcmBytes:
			header["pcm"] = pcm
			raise _error("workerCrash", "the development worker returned incomplete PCM")
		header["pcm"] = pcm
		return header

	@staticmethod
	def _terminateProcess(process: subprocess.Popen[bytes]) -> None:
		try:
			process.terminate()
			process.wait(timeout=5)
		except (OSError, subprocess.TimeoutExpired):
			try:
				process.kill()
				process.wait(timeout=5)
			except (OSError, subprocess.TimeoutExpired):
				pass

	@staticmethod
	def _reapDetachedProcess(process: subprocess.Popen[bytes]) -> None:
		"""Reap an asynchronously terminated replacement process off-thread."""
		try:
			process.wait(timeout=5)
		except (OSError, subprocess.TimeoutExpired):
			try:
				process.kill()
				process.wait(timeout=5)
			except (OSError, subprocess.TimeoutExpired):
				pass
		for stream in (process.stdin, process.stdout, process.stderr):
			if stream is not None:
				try:
					stream.close()
				except OSError:
					pass

	def _discardProcess(self, process: subprocess.Popen[bytes]) -> None:
		with self._processLock:
			if self._process is process:
				self._process = None
		for stream in (process.stdin, process.stdout, process.stderr):
			if stream is not None:
				try:
					stream.close()
				except OSError:
					pass
		try:
			process.wait(timeout=5)
		except (OSError, subprocess.TimeoutExpired):
			pass

	def synthesize(self, text: str, generationId: int, jobId: int, *, cancellationToken: int | None = None, characterMode: bool = False, indexesAfter: tuple[int, ...] = (), segmentNumber: int = 1) -> PcmResult:
		if type(text) is not str or not text or len(text) > MAX_TEXT_CODE_POINTS:
			raise _error("invalidRequest", "speech text is empty or exceeds the development limit")
		if type(characterMode) is not bool or type(indexesAfter) is not tuple:
			raise _error("invalidRequest", "speech segment metadata is invalid")
		for value, label in ((generationId, "generation"), (jobId, "job"), (segmentNumber, "segment")):
			if type(value) is not int or not 1 <= value <= (1 << 63) - 1:
				raise _error("invalidRequest", f"{label} identifier is invalid")
		with self._processLock:
			token = self._cancellationToken if cancellationToken is None else cancellationToken
			if token != self._cancellationToken:
				raise RuntimeBridgeCancelled()
		process = self._process if self._process is not None and self._process.poll() is None else None
		if process is None:
			process = self._start()
		request = json.dumps(
			{"characterMode": characterMode, "generationId": generationId, "indexesAfter": list(indexesAfter), "jobId": jobId, "segmentNumber": segmentNumber, "text": text},
			ensure_ascii=False,
			allow_nan=False,
			separators=(",", ":"),
			sort_keys=True,
		).encode("utf-8")
		if len(request) > 65_536:
			raise _error("invalidRequest", "speech request exceeds the development limit")
		try:
			assert process.stdin is not None
			process.stdin.write(struct.pack("<I", len(request)) + request)
			process.stdin.flush()
			header = self._readFrame(process)
		except RuntimeBridgeError:
			self._discardProcess(process)
			raise
		except (BrokenPipeError, OSError) as error:
			self._discardProcess(process)
			raise _error("workerCrash", "the development worker failed") from error
		if token != self.cancellationToken:
			raise RuntimeBridgeCancelled()
		if header.get("generationId") != generationId or header.get("jobId") != jobId or header.get("segmentNumber") != segmentNumber:
			raise _error("staleResult", "the development worker returned stale PCM")
		if header.get("indexesAfter") != list(indexesAfter):
			raise _error("protocolFailure", "the development worker returned invalid index metadata")
		pcm = header.get("pcm")
		sampleRate = header.get("sampleRate")
		channels = header.get("channels")
		sampleWidth = header.get("sampleWidth")
		if type(pcm) is not bytes or type(sampleRate) is not int or type(channels) is not int or type(sampleWidth) is not int:
			raise _error("invalidPcm", "the development worker returned invalid PCM")
		if channels != 1 or sampleWidth != 2 or not 8_000 <= sampleRate <= 192_000 or not pcm or len(pcm) % 2:
			raise _error("invalidPcm", "the development worker returned invalid PCM")
		return PcmResult(generationId, jobId, sampleRate, channels, sampleWidth, pcm)

	def interrupt(self) -> None:
		with self._processLock:
			self._cancellationToken += 1
			process = self._process
			if process is not None and process.poll() is None:
				self._restartCount = 0
		if process is not None and process.poll() is None:
			try:
				process.terminate()
			except OSError:
				pass

	def stop(self) -> None:
		self.interrupt()
		with self._processLock:
			process = self._process
		if process is None:
			return
		try:
			process.wait(timeout=5)
		except subprocess.TimeoutExpired:
			try:
				process.kill()
				process.wait(timeout=5)
			except (OSError, subprocess.TimeoutExpired):
				pass
		self._discardProcess(process)

	def forceStop(self) -> None:
		self.interrupt()
