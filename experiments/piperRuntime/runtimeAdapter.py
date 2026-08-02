"""Standalone, language-neutral adapter for a locally installed Piper runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.metadata
import json
from pathlib import Path
import time
from typing import Any, Final
import wave


MAX_TEXT_CODE_POINTS: Final = 16_384
MAX_CONFIG_BYTES: Final = 1_048_576
MAX_MODEL_BYTES: Final = 1_073_741_824
MIN_SAMPLE_RATE: Final = 8_000
MAX_SAMPLE_RATE: Final = 192_000
MAX_SPEAKERS: Final = 10_000
EXPECTED_RUNTIME_DISTRIBUTION: Final = "piper-tts"
EXPECTED_RUNTIME_VERSION: Final = "1.5.0"


class RuntimeAdapterError(Exception):
	"""A bounded, content-free standalone adapter failure."""

	def __init__(self, code: str, message: str) -> None:
		super().__init__(message)
		self.code = code
		self.message = message


@dataclass(frozen=True)
class VoiceMetadata:
	sampleRate: int
	numSpeakers: int
	speakerIds: tuple[int, ...]
	phonemeType: str
	piperVersion: str | None


@dataclass(frozen=True)
class LoadResult:
	runtimeVersion: str
	loadSeconds: float
	metadata: VoiceMetadata
	executionProviders: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisResult:
	elapsedSeconds: float
	firstChunkSeconds: float | None
	sampleRate: int
	channels: int
	sampleWidth: int
	frameCount: int
	audioBytes: int
	audioDurationSeconds: float
	realTimeFactor: float
	chunkCount: int

	def toDict(self) -> dict[str, Any]:
		return asdict(self)


def _requirePlainInt(value: object, field: str, minimum: int, maximum: int) -> int:
	if type(value) is not int:
		raise RuntimeAdapterError("invalidConfig", f"{field} must be an integer")
	if not minimum <= value <= maximum:
		raise RuntimeAdapterError("invalidConfig", f"{field} is outside the supported range")
	return value


def _requireFile(path: str | Path, suffix: str, code: str, maximumBytes: int) -> Path:
	if not isinstance(path, (str, Path)) or isinstance(path, bytes):
		raise RuntimeAdapterError(code, "A filesystem path is required")
	resolved = Path(path).expanduser().resolve(strict=False)
	if resolved.suffix.lower() != suffix or not resolved.is_file():
		raise RuntimeAdapterError(code, "The supplied file is missing or has the wrong type")
	try:
		size = resolved.stat().st_size
	except OSError as error:
		raise RuntimeAdapterError(code, "The supplied file cannot be inspected") from error
	if size <= 0 or size > maximumBytes:
		raise RuntimeAdapterError(code, "The supplied file size is outside the supported range")
	return resolved


def validateVoiceFiles(modelPath: str | Path, configPath: str | Path) -> tuple[Path, Path, VoiceMetadata]:
	"""Validate explicit local paths and the bounded subset of model metadata used here."""
	model = _requireFile(modelPath, ".onnx", "invalidModel", MAX_MODEL_BYTES)
	config = _requireFile(configPath, ".json", "invalidConfig", MAX_CONFIG_BYTES)
	try:
		raw = config.read_bytes()
		if raw.startswith(b"\xef\xbb\xbf"):
			raise RuntimeAdapterError("invalidConfig", "The configuration must be BOM-free UTF-8 JSON")
		data = json.loads(raw.decode("utf-8"))
	except RuntimeAdapterError:
		raise
	except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
		raise RuntimeAdapterError("invalidConfig", "The configuration is not valid UTF-8 JSON") from error
	if not isinstance(data, dict):
		raise RuntimeAdapterError("invalidConfig", "The configuration root must be an object")
	try:
		audio = data["audio"]
		if not isinstance(audio, dict):
			raise TypeError
		sampleRate = _requirePlainInt(audio["sample_rate"], "sample rate", MIN_SAMPLE_RATE, MAX_SAMPLE_RATE)
		numSpeakers = _requirePlainInt(data["num_speakers"], "speaker count", 1, MAX_SPEAKERS)
	except (KeyError, TypeError) as error:
		raise RuntimeAdapterError("invalidConfig", "Required voice metadata is missing or invalid") from error
	speakerMap = data.get("speaker_id_map", {})
	if not isinstance(speakerMap, dict):
		raise RuntimeAdapterError("invalidConfig", "Speaker metadata must be an object")
	speakerIds: list[int] = []
	for speakerId in speakerMap.values():
		speakerIds.append(_requirePlainInt(speakerId, "speaker ID", 0, numSpeakers - 1))
	phonemeType = data.get("phoneme_type", "espeak")
	if not isinstance(phonemeType, str) or not phonemeType or len(phonemeType) > 32:
		raise RuntimeAdapterError("invalidConfig", "Phoneme metadata is invalid")
	piperVersion = data.get("piper_version")
	if piperVersion is not None and (not isinstance(piperVersion, str) or len(piperVersion) > 64):
		raise RuntimeAdapterError("invalidConfig", "Piper version metadata is invalid")
	metadata = VoiceMetadata(sampleRate, numSpeakers, tuple(sorted(set(speakerIds))), phonemeType, piperVersion)
	return model, config, metadata


def validateText(text: object) -> str:
	if not isinstance(text, str):
		raise RuntimeAdapterError("invalidText", "Text must be a Unicode string")
	if not text:
		raise RuntimeAdapterError("emptyText", "Text must not be empty")
	if len(text) > MAX_TEXT_CODE_POINTS:
		raise RuntimeAdapterError("textLimitExceeded", "Text exceeds the standalone experiment limit")
	return text


def validateOutputPath(outputPath: str | Path, overwrite: bool = False) -> Path:
	if not isinstance(outputPath, (str, Path)) or isinstance(outputPath, bytes):
		raise RuntimeAdapterError("invalidOutput", "An output path is required")
	output = Path(outputPath).expanduser().resolve(strict=False)
	if output.suffix.lower() != ".wav" or not output.parent.is_dir():
		raise RuntimeAdapterError("invalidOutput", "Output must be a WAV file in an existing directory")
	if output.exists() and not overwrite:
		raise RuntimeAdapterError("outputExists", "Output already exists")
	return output


class PiperRuntimeAdapter:
	"""Own one in-process Piper voice for standalone, offline experimentation."""

	def __init__(self, modelPath: str | Path, configPath: str | Path, useCuda: bool = False) -> None:
		self.modelPath, self.configPath, self.metadata = validateVoiceFiles(modelPath, configPath)
		if type(useCuda) is not bool:
			raise RuntimeAdapterError("invalidProvider", "The provider selection must be Boolean")
		self.useCuda = useCuda
		self._voice: Any | None = None
		self.loadResult: LoadResult | None = None

	def load(self) -> LoadResult:
		if self._voice is not None:
			return self.loadResult  # type: ignore[return-value]
		try:
			runtimeVersion = importlib.metadata.version(EXPECTED_RUNTIME_DISTRIBUTION)
		except importlib.metadata.PackageNotFoundError as error:
			raise RuntimeAdapterError("runtimeUnavailable", "The pinned Piper runtime is not installed") from error
		if runtimeVersion != EXPECTED_RUNTIME_VERSION:
			raise RuntimeAdapterError("runtimeVersionMismatch", "The installed Piper runtime version is unsupported")
		try:
			from piper import PiperVoice
			started = time.perf_counter()
			voice = PiperVoice.load(str(self.modelPath), config_path=str(self.configPath), use_cuda=self.useCuda)
			elapsed = time.perf_counter() - started
		except Exception as error:
			raise RuntimeAdapterError("modelLoadFailed", "The runtime could not load the supplied voice") from error
		providers = tuple(str(provider) for provider in voice.session.get_providers())
		self._voice = voice
		self.loadResult = LoadResult(runtimeVersion, elapsed, self.metadata, providers)
		return self.loadResult

	def synthesize(self, text: str, outputPath: str | Path, speakerId: int | None = None, overwrite: bool = False) -> SynthesisResult:
		validatedText = validateText(text)
		output = validateOutputPath(outputPath, overwrite)
		if speakerId is not None:
			if type(speakerId) is not int or not 0 <= speakerId < self.metadata.numSpeakers:
				raise RuntimeAdapterError("invalidSpeaker", "Speaker ID is outside the model metadata range")
		voice = self._voice
		if voice is None:
			self.load()
			voice = self._voice
		assert voice is not None
		try:
			from piper import SynthesisConfig
			synConfig = SynthesisConfig(speaker_id=speakerId)
			started = time.perf_counter()
			firstChunk: float | None = None
			frameCount = 0
			chunkCount = 0
			mode = "wb" if overwrite else "xb"
			with output.open(mode) as outputFile, wave.open(outputFile, "wb") as wavFile:
				wavFile.setframerate(self.metadata.sampleRate)
				wavFile.setsampwidth(2)
				wavFile.setnchannels(1)
				for chunk in voice.synthesize(validatedText, syn_config=synConfig):
					if firstChunk is None:
						firstChunk = time.perf_counter() - started
					audio = chunk.audio_int16_bytes
					wavFile.writeframes(audio)
					frameCount += len(audio) // 2
					chunkCount += 1
			elapsed = time.perf_counter() - started
		except FileExistsError as error:
			raise RuntimeAdapterError("outputExists", "Output already exists") from error
		except RuntimeAdapterError:
			raise
		except Exception as error:
			try:
				output.unlink(missing_ok=True)
			except OSError:
				pass
			raise RuntimeAdapterError("synthesisFailed", "The runtime could not synthesize the supplied input") from error
		if frameCount <= 0:
			output.unlink(missing_ok=True)
			raise RuntimeAdapterError("emptyAudio", "The runtime produced no audio frames")
		duration = frameCount / self.metadata.sampleRate
		return SynthesisResult(elapsed, firstChunk, self.metadata.sampleRate, 1, 2, frameCount, frameCount * 2, duration, elapsed / duration, chunkCount)

	def close(self) -> None:
		self._voice = None

	def __enter__(self) -> "PiperRuntimeAdapter":
		self.load()
		return self

	def __exit__(self, excType: object, excValue: object, traceback: object) -> None:
		self.close()


def inspectWav(path: str | Path) -> dict[str, int | float]:
	output = _requireFile(path, ".wav", "invalidOutput", MAX_MODEL_BYTES)
	try:
		with wave.open(str(output), "rb") as wavFile:
			frameCount = wavFile.getnframes()
			sampleRate = wavFile.getframerate()
			channels = wavFile.getnchannels()
			sampleWidth = wavFile.getsampwidth()
	except (OSError, EOFError, wave.Error) as error:
		raise RuntimeAdapterError("invalidAudio", "Output is not a valid WAV file") from error
	if frameCount <= 0 or sampleRate <= 0:
		raise RuntimeAdapterError("invalidAudio", "Output contains no valid audio frames")
	return {"sampleRate": sampleRate, "channels": channels, "sampleWidth": sampleWidth, "frameCount": frameCount, "durationSeconds": frameCount / sampleRate}
