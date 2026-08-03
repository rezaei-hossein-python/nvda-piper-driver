"""Isolated tests for Phase 2J driver gating, background submission, playback, and teardown."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import sys
import time
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

	def notify(self, *, synth: object, index: int | None = None) -> None:
		self.calls.append((synth, index) if index is not None else synth)


class StubSynthDriver(ABC):
	supportedSettings = ()
	supportedCommands = frozenset()
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
class StubIndexItem:
	index: int


@dataclass(frozen=True)
class StubBreakItem:
	durationMs: int


@dataclass(frozen=True)
class StubCharacterModeItem:
	state: bool


@dataclass(frozen=True)
class StubLanguageChangeItem:
	language: str | None


@dataclass(frozen=True)
class StubProsodyItem:
	commandType: str
	offset: int
	multiplier: int | float
	isDefault: bool


@dataclass(frozen=True)
class StubPhonemeItem:
	ipa: str
	fallbackText: str | None


class HostileUnsupportedItem:
	def __repr__(self) -> str:
		raise AssertionError("hostile representation must not be read")


@dataclass(frozen=True)
class StubJob:
	jobId: int
	generationId: int
	items: tuple[object, ...]


class StubSpeechJobConverter:
	def __init__(self) -> None:
		self.job: StubJob | None = StubJob(1, 1, (StubTextItem("private fixture"),))
		self.convertCalls = 0

	def convert(self, speechSequence, *, voiceId, rate):
		self.convertCalls += 1
		if type(speechSequence) is not list:
			raise TypeError("speechSequence must be a list")
		if self.job is None:
			raise AssertionError("test speech job was not supplied")
		job = self.job
		self.job = None
		return job


class StubBridge:
	instances: list["StubBridge"] = []

	def __init__(self, *paths: str) -> None:
		self.paths = paths
		self.stopped = 0
		self.texts: list[str] = []
		StubBridge.instances.append(self)

	def synthesize(self, text: str, generationId: int, jobId: int, **kwargs):
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

	def interrupt(self) -> None:
		self.stopped += 1


@dataclass(frozen=True)
class StubBackgroundRequest:
	generationId: int
	jobId: int
	segments: tuple[object, ...]
	trace: object | None = None

	@property
	def text(self) -> str:
		return "".join(segment.text for segment in self.segments)


class StubController:
	instances: list["StubController"] = []

	def __init__(self, bridge, playResult, dispatch, onComplete, onIndex, onError) -> None:
		self.bridge = bridge
		self.playResult = playResult
		self.dispatch = dispatch
		self.onComplete = onComplete
		self.onIndex = onIndex
		self.onError = onError
		self.requests: list[StubBackgroundRequest] = []
		self.current: int | None = None
		self.cancelCalls = self.shutdownCalls = 0
		StubController.instances.append(self)

	def submit(self, request: StubBackgroundRequest) -> None:
		self.requests[:] = [request]
		self.current = request.generationId

	def isCurrent(self, generationId: int) -> bool:
		return self.current == generationId

	def cancel(self) -> None:
		self.cancelCalls += 1
		self.current = None
		self.requests.clear()

	def shutdown(self) -> bool:
		self.shutdownCalls += 1
		self.current = None
		return True

	def runLatest(self) -> None:
		request = self.requests.pop()
		for segment in request.segments:
			if segment.text:
				result = self.bridge.synthesize(segment.text, request.generationId, request.jobId)
				if not self.isCurrent(request.generationId) or not self.playResult(result):
					return
			for index in segment.indexesAfter:
				self.onIndex(index)
		if self.isCurrent(request.generationId):
			self.onComplete()


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
	StubController.instances.clear()
	StubWavePlayer.instances.clear()
	stubHandler = types.ModuleType("synthDriverHandler")
	stubHandler.SynthDriver = StubSynthDriver  # type: ignore[attr-defined]
	stubHandler.synthDoneSpeaking = StubNotification()  # type: ignore[attr-defined]
	stubHandler.synthIndexReached = StubNotification()  # type: ignore[attr-defined]
	stubHandler.VoiceInfo = lambda identifier, displayName, language: types.SimpleNamespace(  # type: ignore[attr-defined]
		id=identifier, displayName=displayName, language=language,
	)
	stubConversion = types.ModuleType("synthDrivers._nvdaPiperDriver.conversion")
	stubConversion.SpeechJobConverter = StubSpeechJobConverter  # type: ignore[attr-defined]
	stubJobs = types.ModuleType("synthDrivers._nvdaPiperDriver.jobs")
	stubJobs.SpeechJob = StubJob  # type: ignore[attr-defined]
	stubJobs.TextItem = StubTextItem  # type: ignore[attr-defined]
	stubJobs.IndexItem = StubIndexItem  # type: ignore[attr-defined]
	stubJobs.LanguageChangeItem = StubLanguageChangeItem  # type: ignore[attr-defined]
	stubJobs.CharacterModeItem = StubCharacterModeItem  # type: ignore[attr-defined]
	stubJobs.BreakItem = StubBreakItem  # type: ignore[attr-defined]
	stubJobs.ProsodyItem = StubProsodyItem  # type: ignore[attr-defined]
	stubBridge = types.ModuleType("synthDrivers._nvdaPiperDriver.runtimeBridge")
	stubBridge.PersistentRuntimeBridge = StubBridge  # type: ignore[attr-defined]
	stubBridge.readModelLanguage = lambda path: "und_TEST"  # type: ignore[attr-defined]
	def validateRuntimePaths(*paths):
		if any(type(path) is not str or not path for path in paths):
			raise ValueError("missing path")
		return paths
	stubBridge.validateRuntimePaths = validateRuntimePaths  # type: ignore[attr-defined]
	stubController = types.ModuleType("synthDrivers._nvdaPiperDriver.backgroundController")
	stubController.BackgroundController = StubController  # type: ignore[attr-defined]
	stubController.BackgroundRequest = StubBackgroundRequest  # type: ignore[attr-defined]
	stubController.SynthesisSegment = lambda text, characterMode=False, indexesAfter=(): types.SimpleNamespace(text=text, characterMode=characterMode, indexesAfter=indexesAfter)  # type: ignore[attr-defined]
	stubConfig = types.ModuleType("config")
	stubConfig.conf = {"audio": {"outputDevice": "default"}}  # type: ignore[attr-defined]
	stubNvwave = types.ModuleType("nvwave")
	stubNvwave.WavePlayer = StubWavePlayer  # type: ignore[attr-defined]
	stubLogHandler = types.ModuleType("logHandler")
	stubLogHandler.log = types.SimpleNamespace(  # type: ignore[attr-defined]
		errorCalls=[],
		warningCalls=[],
		error=lambda *args: stubLogHandler.log.errorCalls.append(args),
		warning=lambda *args: stubLogHandler.log.warningCalls.append(args),
	)
	stubQueueHandler = types.ModuleType("queueHandler")
	stubQueueHandler.eventQueue = object()  # type: ignore[attr-defined]
	stubQueueHandler.queueFunction = lambda queue, callback: callback()  # type: ignore[attr-defined]
	spec = importlib.util.spec_from_file_location(MODULE_NAME, DRIVER_PATH)
	if spec is None or spec.loader is None:
		raise AssertionError("Unable to load driver")
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		"config": stubConfig,
		"nvwave": stubNvwave,
		"logHandler": stubLogHandler,
		"queueHandler": stubQueueHandler,
		"synthDrivers._nvdaPiperDriver.backgroundController": stubController,
		"synthDriverHandler": stubHandler,
		"synthDrivers._nvdaPiperDriver.conversion": stubConversion,
		"synthDrivers._nvdaPiperDriver.jobs": stubJobs,
		"synthDrivers._nvdaPiperDriver.runtimeBridge": stubBridge,
		"synthDrivers._nvdaPiperDriver.latencyMetrics": types.SimpleNamespace(
			LatencyRecorder=lambda: types.SimpleNamespace(record=lambda trace: None),
			LatencyTrace=type("LatencyTrace", (), {"__init__": lambda self, *args: None, "mark": lambda self, *args: None}),
		),
		MODULE_NAME: module,
	}):
		spec.loader.exec_module(module)
	return module


class DriverPhase2JTests(unittest.TestCase):
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
			driver._jobConverter.job = StubJob(
				1,
				1,
				(StubLanguageChangeItem("arbitrary_LOCALE"), StubTextItem("private fixture"), StubIndexItem(7)),
			)
			driver.speak(["private fixture"])
			self.assertEqual([], StubBridge.instances[-1].texts)
			self.assertEqual([], StubWavePlayer.instances)
			StubController.instances[-1].runLatest()
		bridge = StubBridge.instances[-1]
		player = StubWavePlayer.instances[-1]
		self.assertEqual(["private fixture"], bridge.texts)
		self.assertEqual([b"\x01\x00" * 20], player.fed)
		self.assertEqual((1, 16_000, 16, "default"), (player.channels, player.samplesPerSec, player.bitsPerSample, player.outputDevice))
		self.assertEqual(1, player.idleCalls)
		self.assertEqual([driver], self.module.synthDriverHandler.synthDoneSpeaking.calls)

	def test_speak_and_cancel_do_not_wait_for_runtime_or_playback(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(
				1,
				1,
				(StubLanguageChangeItem(None), StubTextItem("private fixture"), StubIndexItem(1)),
			)
			start = time.perf_counter()
			driver.speak(["private fixture"])
			self.assertLess(time.perf_counter() - start, 0.1)
			self.assertEqual([], StubBridge.instances[-1].texts)
			start = time.perf_counter()
			driver.cancel()
			self.assertLess(time.perf_counter() - start, 0.1)
			self.assertEqual([], StubController.instances[-1].requests)
			self.assertEqual([], self.module.synthDriverHandler.synthDoneSpeaking.calls)

	def test_index_only_job_is_rejected_as_empty_without_worker_or_player(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(1, 1, (StubIndexItem((1 << 63) - 1),))
			driver.speak([])
		self.assertEqual([], StubController.instances[-1].requests)
		self.assertEqual([], StubBridge.instances[-1].texts)
		self.assertEqual([], StubWavePlayer.instances)
		self.assertEqual(
			[("NVDA Piper speech request rejected: %s", "emptySpeech")],
			self.module.log.warningCalls,
		)

	def test_text_and_mandatory_indexes_preserve_exact_order_without_retention(self) -> None:
		cases = (
			((StubTextItem("text"), StubIndexItem(0)), "text"),
			((StubIndexItem(1), StubTextItem(" text")), " text"),
			((StubTextItem("متن "), StubIndexItem(2), StubTextItem("English\u200f\n")), "متن English\u200f\n"),
			((StubTextItem("a"), StubIndexItem(3), StubIndexItem((1 << 63) - 1), StubTextItem(" b")), "a b"),
		)
		for items, expected in cases:
			with self.subTest(items=tuple(type(item).__name__ for item in items)), patch.dict(
				os.environ,
				self.environment,
				clear=True,
			):
				driver = self.module.SynthDriver()
				self.module.synthDriverHandler.synthIndexReached.calls.clear()
				doneCallsBefore = len(self.module.synthDriverHandler.synthDoneSpeaking.calls)
				sourceJob = StubJob(1, 1, items)
				driver._jobConverter.job = sourceJob
				driver.speak(["unused"])
				request = StubController.instances[-1].requests[-1]
				self.assertEqual(expected, request.text)
				self.assertFalse(hasattr(request, "index"))
				self.assertIsNone(driver._jobConverter.job)
				self.assertEqual(items, sourceJob.items)
				StubController.instances[-1].runLatest()
				self.assertEqual(
					[segment.text for segment in request.segments if segment.text],
					StubBridge.instances[-1].texts,
				)
				self.assertEqual(
					doneCallsBefore + 1,
					len(self.module.synthDriverHandler.synthDoneSpeaking.calls),
				)
				self.assertIs(driver, self.module.synthDriverHandler.synthDoneSpeaking.calls[-1])
				self.assertEqual([index for item in items if isinstance(item, StubIndexItem) for index in (item.index,)], [call[1] for call in self.module.synthDriverHandler.synthIndexReached.calls])

	def test_character_mode_creates_isolated_segments_and_real_index_callback(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(
			1,
			1,
			(
				StubCharacterModeItem(True),
				StubTextItem("A"),
				StubCharacterModeItem(False),
				StubTextItem(" word"),
				StubIndexItem(17),
			),
		)
			driver.speak(["unused"])
			request = StubController.instances[-1].requests[-1]
			self.assertEqual(["A", " word"], [segment.text for segment in request.segments])
			self.assertEqual([True, False], [segment.characterMode for segment in request.segments])
			StubController.instances[-1].runLatest()
		self.assertEqual(["A", " word"], StubBridge.instances[-1].texts)
		self.assertEqual([(driver, 17)], self.module.synthDriverHandler.synthIndexReached.calls)
		self.assertEqual([driver], self.module.synthDriverHandler.synthDoneSpeaking.calls)
		self.assertEqual({self.module.synthDriverHandler.synthDoneSpeaking, self.module.synthDriverHandler.synthIndexReached}, driver.supportedNotifications)

	def test_language_and_index_metadata_preserve_language_neutral_text(self) -> None:
		cases = (
			((StubLanguageChangeItem("before"), StubTextItem("English")), "English"),
			((StubTextItem("text"), StubLanguageChangeItem("after")), "text"),
			((StubTextItem("a"), StubLanguageChangeItem("between"), StubTextItem(" b")), "a b"),
			(
				(
					StubLanguageChangeItem(None),
					StubIndexItem(1),
					StubTextItem("English | فارسی | العربية | français | e\u0301 | \u200fABC\u200e"),
					StubLanguageChangeItem("second"),
					StubIndexItem(2),
					StubTextItem("\nnext"),
					StubLanguageChangeItem("after"),
				),
				"English | فارسی | العربية | français | e\u0301 | \u200fABC\u200e\nnext",
			),
		)
		for items, expected in cases:
			with self.subTest(items=tuple(type(item).__name__ for item in items)), patch.dict(
				os.environ,
				self.environment,
				clear=True,
			):
				driver = self.module.SynthDriver()
				sourceJob = StubJob(1, 1, items)
				driver._jobConverter.job = sourceJob
				driver.speak(["unused"])
				request = StubController.instances[-1].requests[-1]
				self.assertEqual(expected, request.text)
				self.assertFalse(hasattr(request, "index"))
				self.assertFalse(hasattr(request, "language"))
				self.assertEqual(items, sourceJob.items)
				self.assertIsNone(driver._jobConverter.job)
				self.assertFalse(
					any(
						type(value) is str and value in {"before", "after", "between", "second"}
						for value in vars(driver).values()
					),
				)
				StubController.instances[-1].runLatest()
				self.assertEqual([segment.text for segment in request.segments if segment.text], StubBridge.instances[-1].texts)

	def test_language_and_index_only_jobs_are_rejected_as_empty(self) -> None:
		cases = (
			(StubLanguageChangeItem("private_LOCALE"),),
			(StubIndexItem(4),),
			(StubLanguageChangeItem(None), StubIndexItem(5)),
			(StubLanguageChangeItem("private_LOCALE"), StubIndexItem(6), StubLanguageChangeItem(None)),
		)
		for items in cases:
			with self.subTest(items=tuple(type(item).__name__ for item in items)), patch.dict(
				os.environ,
				self.environment,
				clear=True,
			):
				self.module.log.warningCalls.clear()
				driver = self.module.SynthDriver()
				driver._jobConverter.job = StubJob(1, 1, items)
				driver.speak([])
				self.assertEqual([], StubController.instances[-1].requests)
				self.assertEqual([], self.module.synthDriverHandler.synthDoneSpeaking.calls)
				self.assertEqual(
					[("NVDA Piper speech request rejected: %s", "emptySpeech")],
					self.module.log.warningCalls,
				)

	def test_all_non_text_non_metadata_items_remain_rejected_once(self) -> None:
		compatibleMetadata = (
			("break", StubBreakItem(100)),
			("rate", StubProsodyItem("rate", 10, 1, False)),
			("pitch", StubProsodyItem("pitch", -5, 1, False)),
			("volume", StubProsodyItem("volume", 20, 1, False)),
		)
		for label, metadata in compatibleMetadata:
			with self.subTest(itemType=label), patch.dict(os.environ, self.environment, clear=True):
				driver = self.module.SynthDriver()
				driver._jobConverter.job = StubJob(1, 1, (metadata, StubTextItem("text")))
				driver.speak(["unused"])
				self.assertEqual("text", StubController.instances[-1].requests[-1].text)

		unsupportedItems = (("phoneme", StubPhonemeItem("private", "fallback")), ("arbitrary", HostileUnsupportedItem()))
		for label, unsupported in unsupportedItems:
			with self.subTest(itemType=label), patch.dict(os.environ, self.environment, clear=True):
				self.module.log.warningCalls.clear()
				driver = self.module.SynthDriver()
				driver._jobConverter.job = StubJob(1, 1, (unsupported,))
				driver.speak(["unused"])
				self.assertEqual(1, driver._jobConverter.convertCalls)
				self.assertEqual([], StubController.instances[-1].requests)
				self.assertEqual([], StubBridge.instances[-1].texts)
				self.assertEqual([], self.module.synthDriverHandler.synthDoneSpeaking.calls)
				self.assertEqual([], self.module.log.errorCalls)
				self.assertEqual(
					[("NVDA Piper speech request rejected: %s", "unsupportedItem")],
					self.module.log.warningCalls,
				)

	def test_unsupported_failure_does_not_retry_or_block_later_valid_speech(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(1, 1, (StubPhonemeItem("private", "fallback"),))
			driver.speak(["unused"])
			driver._jobConverter.job = StubJob(2, 2, (StubCharacterModeItem(True),))
			driver.speak(["another unused value"])
			self.assertEqual(2, driver._jobConverter.convertCalls)
			self.assertEqual([], StubController.instances[-1].requests)
			self.assertEqual([], self.module.log.errorCalls)
			driver._jobConverter.job = StubJob(
				3,
				3,
				(StubLanguageChangeItem("private_LOCALE"), StubTextItem("later valid"), StubIndexItem(2)),
			)
			driver.speak(["unused"])
			self.assertEqual(3, driver._jobConverter.convertCalls)
			self.assertEqual(["later valid"], [request.text for request in StubController.instances[-1].requests])
			self.assertEqual(
				[("NVDA Piper speech request rejected: %s", "unsupportedItem")],
				self.module.log.warningCalls,
			)
			StubController.instances[-1].runLatest()
			self.assertEqual(["later valid"], StubBridge.instances[-1].texts)
			self.assertEqual([driver], self.module.synthDriverHandler.synthDoneSpeaking.calls)
			driver._jobConverter.job = StubJob(4, 4, (StubCharacterModeItem(False),))
			driver.speak(["unused"])
			self.assertEqual(
				[
					("NVDA Piper speech request rejected: %s", "unsupportedItem"),
					("NVDA Piper speech request rejected: %s", "emptySpeech"),
				],
				self.module.log.warningCalls,
			)

	def test_text_item_exact_type_is_required(self) -> None:
		class TextSubclass(StubTextItem):
			pass

		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(1, 1, (TextSubclass("private"),))
			driver.speak(["unused"])
		self.assertEqual([], StubController.instances[-1].requests)
		self.assertEqual([("NVDA Piper speech request rejected: %s", "unsupportedItem")], self.module.log.warningCalls)

	def test_language_item_exact_type_is_required(self) -> None:
		class LanguageSubclass(StubLanguageChangeItem):
			pass

		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(1, 1, (StubTextItem("text"), LanguageSubclass("private")))
			driver.speak(["unused"])
		self.assertEqual([], StubController.instances[-1].requests)
		self.assertEqual([("NVDA Piper speech request rejected: %s", "unsupportedItem")], self.module.log.warningCalls)

	def test_metadata_support_is_neither_advertised_nor_retained(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver._jobConverter.job = StubJob(
				1,
				1,
				(StubLanguageChangeItem("private_LOCALE"), StubTextItem("text"), StubIndexItem(9)),
			)
			driver.speak(["unused"])
		self.assertEqual(frozenset(), driver.supportedCommands)
		self.assertEqual({self.module.synthDriverHandler.synthDoneSpeaking, self.module.synthDriverHandler.synthIndexReached}, driver.supportedNotifications)
		self.assertEqual("configuredModel", driver.voice)
		self.assertEqual(
			(
				self.environment[self.module._RUNTIME_PATH_ENV],
				self.environment[self.module._MODEL_PATH_ENV],
				self.environment[self.module._CONFIG_PATH_ENV],
			),
			StubBridge.instances[-1].paths[:3],
		)
		self.assertFalse(any("index" in name.lower() for name in vars(driver)))
		self.assertNotIn("private_LOCALE", vars(driver).values())
		self.assertFalse(hasattr(StubController.instances[-1].requests[-1], "index"))
		self.assertFalse(hasattr(StubController.instances[-1].requests[-1], "language"))
		self.assertEqual([], self.module.log.errorCalls)

	def test_stale_pcm_is_not_played(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver.speak(["private fixture"])
			StubController.instances[-1].current = 2
			StubController.instances[-1].runLatest()
		self.assertEqual([], StubWavePlayer.instances)

	def test_cancel_and_terminate_stop_owned_resources(self) -> None:
		with patch.dict(os.environ, self.environment, clear=True):
			driver = self.module.SynthDriver()
			driver.speak(["private fixture"])
			StubController.instances[-1].runLatest()
			bridge = StubBridge.instances[-1]
			player = StubWavePlayer.instances[-1]
			driver.cancel()
			driver.terminate()
			driver.terminate()
		self.assertGreaterEqual(StubController.instances[-1].cancelCalls, 2)
		self.assertEqual(1, StubController.instances[-1].shutdownCalls)
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
