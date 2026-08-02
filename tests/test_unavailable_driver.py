"""Isolated tests for Phase 2I driver gating, playback, and teardown."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "addon" / "synthDrivers" / "nvdaPiperDriver.py"
MODULE_NAME = "phase2i_test_nvdaPiperDriver"


class StubSetting:
	def __init__(self, identifier: str, defaultValue) -> None:
		self.id = identifier
		self.defaultVal = defaultValue
		self.useConfig = True


class StubNotification:
	def __init__(self) -> None:
		self.calls: list[object] = []

	def notify(self, *, synth: object) -> None:
		self.calls.append(synth)


class StubSynthDriver(ABC):
	supportedSettings = ()
	failTermination = False

	@classmethod
	def VoiceSetting(cls) -> StubSetting:
		return StubSetting("voice", None)

	@classmethod
	def RateSetting(cls) -> StubSetting:
		return StubSetting("rate", 50)

	def __init__(self) -> None:
		self.baseTerminateCalls = 0

	def terminate(self) -> None:
		self.voice
		self.rate
		self.baseTerminateCalls += 1
		if self.failTermination:
			raise RuntimeError("inherited cleanup failed")

	@property
	def availableVoices(self):
		if not hasattr(self, "_availableVoices"):
			self._availableVoices = self._getAvailableVoices()
		return self._availableVoices

	voice = property(lambda self: self._get_voice(), lambda self, value: self._set_voice(value))
	rate = property(lambda self: self._get_rate(), lambda self, value: self._set_rate(value))

	@abstractmethod
	def speak(self, speechSequence) -> None:
		raise NotImplementedError


@dataclass(frozen=True)
class StubTextItem:
	text: str


@dataclass(frozen=True)
class StubPhonemeItem:
	ipa: str
	fallbackText: str | None


@dataclass(frozen=True)
class StubLanguageChangeItem:
	language: str | None


@dataclass(frozen=True)
class StubJob:
	jobId: int
	generationId: int
	items: tuple[object, ...]


class StubSpeechJobConverter:
	def __init__(self) -> None:
		self.job = StubJob(1, 1, (StubTextItem("private fixture"),))

	def convert(self, speechSequence, *, voiceId, rate):
		if type(speechSequence) is not list:
			raise TypeError("speechSequence must be a list")
		return self.job


class StubBridge:
	instances: list["StubBridge"] = []

	def __init__(self, *paths: str) -> None:
		self.paths = paths
		self.stopped = 0
		self.texts: list[str] = []
		StubBridge.instances.append(self)

	def synthesize(self, text: str, generationId: int, jobId: int):
		self.texts.append(text)
		return types.SimpleNamespace(
			generationId=generationId,
			jobId=jobId,
			sampleRate=16_000,
			channels=1,
			sampleWidth=2,
			pcm=b"\x01\x00" * 20,
		)

	def stop(self) -> None:
		self.stopped += 1


class StubWavePlayer:
	instances: list["StubWavePlayer"] = []

	def __init__(self, *, channels, samplesPerSec, bitsPerSample, outputDevice) -> None:
		self.channels = channels
		self.samplesPerSec = samplesPerSec
		self.bitsPerSample = bitsPerSample
		self.outputDevice = outputDevice
		self.fed: list[bytes] = []
		self.idleCalls = self.stopCalls = self.closeCalls = 0
		StubWavePlayer.instances.append(self)

	def feed(self, pcm: bytes) -> None:
		self.fed.append(pcm)

	def idle(self) -> None:
		self.idleCalls += 1

	def stop(self) -> None:
		self.stopCalls += 1

	def close(self) -> None:
		self.closeCalls += 1


def loadDriverModule() -> types.ModuleType:
	StubBridge.instances.clear()
	StubWavePlayer.instances.clear()
	stubHandler = types.ModuleType("synthDriverHandler")
	stubHandler.SynthDriver = StubSynthDriver  # type: ignore[attr-defined]
	stubHandler.synthDoneSpeaking = StubNotification()  # type: ignore[attr-defined]
	stubHandler.VoiceInfo = lambda identifier, displayName, language: types.SimpleNamespace(  # type: ignore[attr-defined]
		id=identifier, displayName=displayName, language=language,
	)
	stubConversion = types.ModuleType("synthDrivers._nvdaPiperDriver.conversion")
	stubConversion.SpeechJobConverter = StubSpeechJobConverter  # type: ignore[attr-defined]
	stubJobs = types.ModuleType("synthDrivers._nvdaPiperDriver.jobs")
	stubJobs.SpeechJob = StubJob  # type: ignore[attr-defined]
	stubJobs.TextItem = StubTextItem  # type: ignore[attr-defined]
	stubJobs.PhonemeItem = StubPhonemeItem  # type: ignore[attr-defined]
	stubJobs.LanguageChangeItem = StubLanguageChangeItem  # type: ignore[attr-defined]
	stubBridge = types.ModuleType("synthDrivers._nvdaPiperDriver.runtimeBridge")
	stubBridge.OneShotRuntimeBridge = StubBridge  # type: ignore[attr-defined]
	stubBridge.readModelLanguage = lambda path: "und_TEST"  # type: ignore[attr-defined]
	def validateRuntimePaths(*paths):
		if any(type(path) is not str or not path for path in paths):
			raise ValueError("missing path")
		return paths
	stubBridge.validateRuntimePaths = validateRuntimePaths  # type: ignore[attr-defined]
	stubConfig = types.ModuleType("config")
	stubConfig.conf = {"audio": {"outputDevice": "default"}}  # type: ignore[attr-defined]
	stubNvwave = types.ModuleType("nvwave")
	stubNvwave.WavePlayer = StubWavePlayer  # type: ignore[attr-defined]
	spec = importlib.util.spec_from_file_location(MODULE_NAME, DRIVER_PATH)
	if spec is None or spec.loader is None:
		raise AssertionError("Unable to load driver")
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		"config": stubConfig,
		"nvwave": stubNvwave,
		"synthDriverHandler": stubHandler,
		"synthDrivers._nvdaPiperDriver.conversion": stubConversion,
		"synthDrivers._nvdaPiperDriver.jobs": stubJobs,
		"synthDrivers._nvdaPiperDriver.runtimeBridge": stubBridge,
		MODULE_NAME: module,
	}):
		spec.loader.exec_module(module)
	return module


class DriverPhase2ITests(unittest.TestCase):
	def setUp(self) -> None:
		self.module = loadDriverModule()
		self.environment = {
			self.module._TEST_ONLY_MARKER_ENV: self.module._TEST_ONLY_MARKER_VALUE,
			self.module._RUNTIME_PATH_ENV: "runtime.exe",
			self.module._MODEL_PATH_ENV: "voice.onnx",
			self.module._CONFIG_PATH_ENV: "voice.onnx.json",
		}

	def test_check_requires_exact_marker_and_all_explicit_paths(self) -> None:
		with patch.dict(os.environ, {}, clear=True):
			self.assertIs(self.module.SynthDriver.check(), False)
		for missing in self.environment:
			environment = dict(self.environment)
			environment.pop(missing)
			with self.subTest(missing=missing), patch.dict(os.environ, environment, clear=True):
				self.assertIs(self.module.SynthDriver.check(), False)
		with patch.dict(os.environ, self.environment, clear=True):
			self.assertIs(self.module.SynthDriver.check(), True)

	def test_one_job_reaches_pcm_player_and_completion(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver.speak(["private fixture"])
		bridge = StubBridge.instances[-1]
		player = StubWavePlayer.instances[-1]
		self.assertEqual(["private fixture"], bridge.texts)
		self.assertEqual([b"\x01\x00" * 20], player.fed)
		self.assertEqual((1, 16_000, 16, "default"), (player.channels, player.samplesPerSec, player.bitsPerSample, player.outputDevice))
		self.assertEqual(1, player.idleCalls)
		self.assertEqual([driver], self.module.synthDriverHandler.synthDoneSpeaking.calls)

	def test_empty_job_completes_without_worker_or_player(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(1, 1, ())
			driver.speak([])
		self.assertEqual([], StubBridge.instances[-1].texts)
		self.assertEqual([], StubWavePlayer.instances)

	def test_only_documented_job_items_reach_worker(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(
				1,
				1,
				(StubLanguageChangeItem("arbitrary_LOCALE"), StubTextItem("text"), StubPhonemeItem("private", " fallback")),
			)
			driver.speak(["unused"])
			self.assertEqual(["text fallback"], StubBridge.instances[-1].texts)
		for unsupported in (object(), StubPhonemeItem("private", None)):
			with self.subTest(itemType=type(unsupported).__name__), patch.dict(os.environ, self.environment, clear=True):
				driver = self.module.SynthDriver()
				driver._jobConverter.job = StubJob(1, 1, (unsupported,))
				with self.assertRaisesRegex(RuntimeError, "speech item is unsupported"):
					driver.speak(["unused"])
				self.assertEqual([], StubBridge.instances[-1].texts)

	def test_stale_pcm_is_not_played(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			bridge = StubBridge.instances[-1]
			original = bridge.synthesize
			def stale(text, generationId, jobId):
				result = original(text, generationId, jobId)
				result.generationId = generationId + 1
				return result
			bridge.synthesize = stale
			driver.speak(["private fixture"])
		self.assertEqual([], StubWavePlayer.instances)

	def test_cancel_and_terminate_stop_owned_resources(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver.speak(["private fixture"])
			bridge = StubBridge.instances[-1]
			player = StubWavePlayer.instances[-1]
			driver.cancel()
			driver.terminate()
			driver.terminate()
		self.assertGreaterEqual(bridge.stopped, 2)
		self.assertGreaterEqual(player.stopCalls, 2)
		self.assertEqual(1, player.closeCalls)
		self.assertEqual(1, driver.baseTerminateCalls)

	def test_voice_and_rate_contract_remains_bounded(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
		self.assertEqual("configuredModel", driver.voice)
		self.assertEqual("Configured Piper model", driver.availableVoices[driver.voice].displayName)
		self.assertEqual("und_TEST", driver.availableVoices[driver.voice].language)
		for value in (0, 50, 100):
			driver.rate = value
		for value in (False, 1.0, "50"):
			with self.assertRaises(TypeError):
				driver.rate = value
		with self.assertRaises(LookupError):
			driver.voice = "other"


if __name__ == "__main__":
	unittest.main()
