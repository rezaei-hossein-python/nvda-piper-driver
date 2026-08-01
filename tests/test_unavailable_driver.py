"""Isolated tests for the controlled Phase 2C availability gate."""

import ast
from abc import ABC, abstractmethod
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "addon" / "synthDrivers" / "nvdaPiperDriver.py"
MODULE_NAME = "phase2c_test_nvdaPiperDriver"
FORBIDDEN_IMPORT_ROOTS = {
	"http",
	"onnxruntime",
	"piper",
	"requests",
	"socket",
	"subprocess",
	"threading",
	"urllib",
	"winsound",
	"wave",
}


class StubSetting:
	def __init__(self, identifier: str, defaultValue) -> None:
		self.id = identifier
		self.defaultVal = defaultValue
		self.useConfig = True


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
		self.baseInitialized = True
		self.baseTerminateCalls = 0

	def terminate(self) -> None:
		# Pinned NVDA saves advertised settings before unregistering its callback.
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

	@property
	def voice(self):
		return self._get_voice()

	@voice.setter
	def voice(self, value) -> None:
		self._set_voice(value)

	@property
	def rate(self):
		return self._get_rate()

	@rate.setter
	def rate(self, value) -> None:
		self._set_rate(value)

	@abstractmethod
	def speak(self, speechSequence) -> None:
		raise NotImplementedError


class StubSpeechJobConverter:
	def convert(self, speechSequence, *, voiceId, rate):
		raise AssertionError("Phase 2D tests must not convert speech")


def loadDriverModule() -> types.ModuleType:
	stubHandler = types.ModuleType("synthDriverHandler")
	stubHandler.SynthDriver = StubSynthDriver  # type: ignore[attr-defined]
	stubHandler.VoiceInfo = lambda identifier, displayName, language: types.SimpleNamespace(  # type: ignore[attr-defined]
		id=identifier,
		displayName=displayName,
		language=language,
	)
	stubConversion = types.ModuleType("synthDrivers._nvdaPiperDriver.conversion")
	stubConversion.SpeechJobConverter = StubSpeechJobConverter  # type: ignore[attr-defined]
	stubJobs = types.ModuleType("synthDrivers._nvdaPiperDriver.jobs")
	stubJobs.SpeechJob = object  # type: ignore[attr-defined]
	spec = importlib.util.spec_from_file_location(MODULE_NAME, DRIVER_PATH)
	if spec is None or spec.loader is None:
		raise AssertionError("Unable to create driver import specification")
	module = importlib.util.module_from_spec(spec)
	with patch.dict(
		sys.modules,
		{
			"synthDriverHandler": stubHandler,
			"synthDrivers._nvdaPiperDriver.conversion": stubConversion,
			"synthDrivers._nvdaPiperDriver.jobs": stubJobs,
			MODULE_NAME: module,
		},
	):
		spec.loader.exec_module(module)
	return module


class UnavailableDriverTests(unittest.TestCase):
	def setUp(self) -> None:
		self.module = loadDriverModule()
		self.markerName = self.module._TEST_ONLY_MARKER_ENV
		self.markerValue = self.module._TEST_ONLY_MARKER_VALUE

	def _availableEnvironment(self):
		return patch.dict(os.environ, {self.markerName: self.markerValue}, clear=True)

	def test_module_path_and_identity(self) -> None:
		self.assertTrue(DRIVER_PATH.is_file())
		self.assertTrue(issubclass(self.module.SynthDriver, StubSynthDriver))
		self.assertEqual(DRIVER_PATH.stem, self.module.SynthDriver.name)
		self.assertEqual("NVDA Piper Driver", self.module.SynthDriver.description)

	def test_check_is_false_without_exact_marker(self) -> None:
		for environment in (
			{},
			{self.markerName: ""},
			{self.markerName: self.markerValue.upper()},
			{self.markerName: f"{self.markerValue}-near-match"},
			{self.markerName: "1"},
			{self.markerName: "yes"},
			{self.markerName: "true"},
			{self.markerName: "enabled"},
			{"ENABLE_PIPER": self.markerValue},
		):
			with self.subTest(environment=environment), patch.dict(os.environ, environment, clear=True):
				self.assertIs(self.module.SynthDriver.check(), False)
				self.assertIs(self.module.SynthDriver.check(), False)

	def test_check_is_true_only_with_exact_marker(self) -> None:
		with self._availableEnvironment():
			self.assertIs(self.module.SynthDriver.check(), True)
			self.assertIs(self.module.SynthDriver.check(), True)

	def test_loader_outcome_follows_check(self) -> None:
		def listedDrivers() -> list[tuple[str, str]]:
			cls = self.module.SynthDriver
			return [(cls.name, cls.description)] if cls.check() else []

		with patch.dict(os.environ, {}, clear=True):
			self.assertEqual([], listedDrivers())
		with self._availableEnvironment():
			self.assertEqual([("nvdaPiperDriver", "NVDA Piper Driver")], listedDrivers())

	def test_import_has_no_external_side_effects(self) -> None:
		moduleNamesBefore = set(sys.modules)
		with (
			patch("builtins.open", side_effect=AssertionError("driver import attempted file access")),
			patch("pathlib.Path.open", side_effect=AssertionError("driver import attempted file access")),
		):
			loadDriverModule()
		self.assertEqual(moduleNamesBefore, set(sys.modules))

	def test_only_permitted_import_is_present(self) -> None:
		tree = ast.parse(DRIVER_PATH.read_text(encoding="utf-8"), filename=str(DRIVER_PATH))
		imports = {
			alias.name.split(".")[0]
			for node in ast.walk(tree)
			if isinstance(node, ast.Import)
			for alias in node.names
		}
		imports.update(
			node.module.split(".")[0]
			for node in ast.walk(tree)
			if isinstance(node, ast.ImportFrom) and node.module
		)
		self.assertEqual({"collections", "enum", "os", "synthDriverHandler", "synthDrivers"}, imports)
		self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORT_ROOTS))

	def test_construction_requires_marker_and_owns_no_runtime_resources(self) -> None:
		with patch.dict(os.environ, {}, clear=True):
			with self.assertRaisesRegex(RuntimeError, "test availability marker"):
				self.module.SynthDriver()
		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		self.assertEqual(self.module._MockLifecycleState.READY, driver._state)
		self.assertEqual(
			{"_state", "_voice", "_rate", "_jobConverter", "baseInitialized", "baseTerminateCalls"},
			set(driver.__dict__),
		)

	def test_lifecycle_has_only_three_states(self) -> None:
		self.assertEqual(
			{"initializing", "ready", "terminated"},
			{state.value for state in self.module._MockLifecycleState},
		)

	def test_termination_delegates_once(self) -> None:
		with self._availableEnvironment():
			markerValue = os.environ[self.module._TEST_ONLY_MARKER_ENV]
			driver = self.module.SynthDriver()
			driver.terminate()
			driver.terminate()
			self.assertEqual(markerValue, os.environ[self.module._TEST_ONLY_MARKER_ENV])
		self.assertIs(self.module._MockLifecycleState.TERMINATED, driver._state)
		self.assertEqual(1, driver.baseTerminateCalls)
		with self.assertRaisesRegex(RuntimeError, "terminated"):
			_ = driver.voice
		with self.assertRaisesRegex(RuntimeError, "terminated"):
			driver.voice = "mockVoice"
		with self.assertRaisesRegex(RuntimeError, "terminated"):
			_ = driver.rate
		with self.assertRaisesRegex(RuntimeError, "terminated"):
			driver.rate = 50
		self.assertIs(self.module._MockLifecycleState.TERMINATED, driver._state)
		with self._availableEnvironment():
			failingDriver = self.module.SynthDriver()
			failingDriver.failTermination = True
			with self.assertRaisesRegex(RuntimeError, "inherited cleanup failed"):
				failingDriver.terminate()
			failingDriver.terminate()
		self.assertIs(self.module._MockLifecycleState.TERMINATED, failingDriver._state)
		self.assertEqual(1, failingDriver.baseTerminateCalls)

	def test_supported_settings_are_exactly_voice_and_rate(self) -> None:
		self.assertEqual(["voice", "rate"], [setting.id for setting in self.module.SynthDriver.supportedSettings])

	def test_fixed_mock_voice(self) -> None:
		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		self.assertEqual("mockVoice", driver.voice)
		self.assertEqual(["mockVoice"], list(driver.availableVoices))
		voice = driver.availableVoices["mockVoice"]
		self.assertEqual("Mock Voice — No Speech", voice.displayName)
		self.assertIsNone(voice.language)
		driver.voice = "mockVoice"
		with self.assertRaises(LookupError):
			driver.voice = "unknown"

	def test_mock_rate_validation_and_round_trip(self) -> None:
		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		self.assertEqual(50, driver.rate)
		for value in (0, 37, 100):
			driver.rate = value
			self.assertEqual(value, driver.rate)
		for value in (-1, 101):
			with self.assertRaises(ValueError):
				driver.rate = value
		for value in (False, True, 1.0, "50", None):
			with self.assertRaises(TypeError):
				driver.rate = value

	def test_unexpected_speak_fails_without_using_sequence(self) -> None:
		class PrivateSpeechSequence:
			def __iter__(self):
				raise AssertionError("speech sequence was iterated")

			def __repr__(self) -> str:
				raise AssertionError("speech sequence was represented")

			def __str__(self) -> str:
				raise AssertionError("speech sequence was converted to text")

			def __eq__(self, other) -> bool:
				raise AssertionError("speech sequence was compared")

			def __len__(self) -> int:
				raise AssertionError("speech sequence length was inspected")

			def __contains__(self, item) -> bool:
				raise AssertionError("speech sequence membership was inspected")

			def __format__(self, formatSpec: str) -> str:
				raise AssertionError("speech sequence was formatted")

			def __copy__(self):
				raise AssertionError("speech sequence was copied")

			def __deepcopy__(self, memo):
				raise AssertionError("speech sequence was deep-copied")

		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		initialState = driver._state
		with self.assertRaisesRegex(RuntimeError, "Phase 2E has no speech implementation"):
			driver.speak(PrivateSpeechSequence())
		self.assertIs(initialState, driver._state)
		driver.terminate()
		with self.assertRaisesRegex(RuntimeError, "terminated"):
			driver.speak(PrivateSpeechSequence())


if __name__ == "__main__":
	unittest.main()
