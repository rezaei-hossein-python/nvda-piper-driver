"""Pure Phase 2E speech-job conversion tests using narrow NVDA command stubs."""

import importlib
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from dataclasses import FrozenInstanceError

from tests.test_unavailable_driver import StubBridge, StubNotification, StubSynthDriver, StubWavePlayer


ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = ROOT / "addon"
DRIVER_PATH = ADDON_ROOT / "synthDrivers" / "nvdaPiperDriver.py"


class SpeechCommand:
	pass


class IndexCommand(SpeechCommand):
	def __init__(self, index) -> None:
		self.index = index


class CharacterModeCommand(SpeechCommand):
	def __init__(self, state) -> None:
		self.state = state
		self.isDefault = not state


class LangChangeCommand(SpeechCommand):
	def __init__(self, lang) -> None:
		self.lang = lang
		self.isDefault = not lang


class BreakCommand(SpeechCommand):
	def __init__(self, time=0) -> None:
		self.time = time


class _ProsodyCommand(SpeechCommand):
	def __init__(self, offset=0, multiplier=1) -> None:
		self._offset = offset
		self._multiplier = multiplier
		self.isDefault = offset == 0 and multiplier == 1

	@property
	def offset(self):
		raise AssertionError("derived offset property must not be read")

	@property
	def multiplier(self):
		raise AssertionError("derived multiplier property must not be read")


class RateCommand(_ProsodyCommand):
	pass


class PitchCommand(_ProsodyCommand):
	pass


class VolumeCommand(_ProsodyCommand):
	pass


class PhonemeCommand(SpeechCommand):
	def __init__(self, ipa, text=None) -> None:
		self.ipa = ipa
		self.text = text


class CallbackCommand(SpeechCommand):
	pass


class ConfigProfileTriggerCommand(SpeechCommand):
	pass


class EndUtteranceCommand(SpeechCommand):
	pass


class SuppressUnicodeNormalizationCommand(SpeechCommand):
	pass


def _commandModule() -> types.ModuleType:
	module = types.ModuleType("speech.commands")
	for commandType in (
		IndexCommand,
		CharacterModeCommand,
		LangChangeCommand,
		BreakCommand,
		RateCommand,
		PitchCommand,
		VolumeCommand,
		PhonemeCommand,
		CallbackCommand,
		ConfigProfileTriggerCommand,
		EndUtteranceCommand,
		SuppressUnicodeNormalizationCommand,
	):
		setattr(module, commandType.__name__, commandType)
	return module


def setUpModule() -> None:
	global conversion, jobs
	speechModule = types.ModuleType("speech")
	commandsModule = _commandModule()
	speechModule.commands = commandsModule  # type: ignore[attr-defined]
	synthDriversModule = types.ModuleType("synthDrivers")
	synthDriversModule.__path__ = [str(ADDON_ROOT / "synthDrivers")]  # type: ignore[attr-defined]
	modulePatch = patch.dict(
		sys.modules,
		{"speech": speechModule, "speech.commands": commandsModule, "synthDrivers": synthDriversModule},
	)
	modulePatch.start()
	globals()["_modulePatch"] = modulePatch
	conversion = importlib.import_module("synthDrivers._nvdaPiperDriver.conversion")
	jobs = importlib.import_module("synthDrivers._nvdaPiperDriver.jobs")


def tearDownModule() -> None:
	for name in tuple(sys.modules):
		if name.startswith("synthDrivers._nvdaPiperDriver"):
			sys.modules.pop(name, None)
	globals()["_modulePatch"].stop()


def _loadDriverModule() -> types.ModuleType:
	stubHandler = types.ModuleType("synthDriverHandler")
	stubHandler.SynthDriver = StubSynthDriver  # type: ignore[attr-defined]
	stubHandler.synthDoneSpeaking = StubNotification()  # type: ignore[attr-defined]
	stubHandler.VoiceInfo = lambda identifier, displayName, language: types.SimpleNamespace(  # type: ignore[attr-defined]
		id=identifier,
		displayName=displayName,
		language=language,
	)
	spec = importlib.util.spec_from_file_location("phase2e_driver", DRIVER_PATH)
	if spec is None or spec.loader is None:
		raise AssertionError("Unable to load driver module")
	module = importlib.util.module_from_spec(spec)
	stubConfig = types.ModuleType("config")
	stubConfig.conf = {"audio": {"outputDevice": "default"}}  # type: ignore[attr-defined]
	stubNvwave = types.ModuleType("nvwave")
	stubNvwave.WavePlayer = StubWavePlayer  # type: ignore[attr-defined]
	stubBridge = types.ModuleType("synthDrivers._nvdaPiperDriver.runtimeBridge")
	stubBridge.OneShotRuntimeBridge = StubBridge  # type: ignore[attr-defined]
	stubBridge.readModelLanguage = lambda path: "und_TEST"  # type: ignore[attr-defined]
	stubBridge.validateRuntimePaths = lambda *paths: paths if all(paths) else (_ for _ in ()).throw(ValueError())  # type: ignore[attr-defined]
	with patch.dict(sys.modules, {
		"config": stubConfig,
		"nvwave": stubNvwave,
		"synthDriverHandler": stubHandler,
		"synthDrivers._nvdaPiperDriver.runtimeBridge": stubBridge,
		"phase2e_driver": module,
	}):
		spec.loader.exec_module(module)
	return module


class SpeechJobConversionTests(unittest.TestCase):
	def setUp(self) -> None:
		self.converter = conversion.SpeechJobConverter()

	def test_job_items_and_collection_are_immutable(self) -> None:
		source = ["original", IndexCommand(3)]
		job = self.converter.convert(source, voiceId="mockVoice", rate=50)
		source[:] = ["changed"]
		self.assertEqual((jobs.TextItem("original"), jobs.IndexItem(3)), job.items)
		self.assertIsInstance(job.items, tuple)
		self.assertNotIn("original", repr(job))
		with self.assertRaises(FrozenInstanceError):
			job.rate = 60
		with self.assertRaises(FrozenInstanceError):
			job.items[0].text = "changed"

	def test_mixed_sequence_preserves_order_and_fields(self) -> None:
		sequence = [
			"first",
			IndexCommand(8),
			"second",
			RateCommand(offset=12),
			BreakCommand(35),
			LangChangeCommand("fa_IR"),
			PhonemeCommand("tɛst", "test"),
			"last",
		]
		job = self.converter.convert(sequence, voiceId="mockVoice", rate=50)
		self.assertEqual(
			(
				jobs.TextItem("first"),
				jobs.IndexItem(8),
				jobs.TextItem("second"),
				jobs.ProsodyItem(jobs.ProsodyCommandType.RATE, 12, 1, False),
				jobs.BreakItem(35),
				jobs.LanguageChangeItem("fa_IR"),
				jobs.PhonemeItem("tɛst", "test"),
				jobs.TextItem("last"),
			),
			job.items,
		)

	def test_text_is_preserved_exactly(self) -> None:
		texts = [
			"",
			"  whitespace\t",
			"فارسی",
			"English",
			"فارسی and English!",
			"line one\nline two",
			"e\u0301",
			"a\u200cb\u200fd",
		]
		job = self.converter.convert(texts, voiceId="mockVoice", rate=50)
		self.assertEqual(tuple(texts), tuple(item.text for item in job.items))

	def test_each_supported_command_is_preserved(self) -> None:
		sequence = [
			IndexCommand(0),
			CharacterModeCommand(True),
			CharacterModeCommand(False),
			LangChangeCommand(None),
			BreakCommand(0),
			RateCommand(multiplier=1.25),
			PitchCommand(offset=-4),
			VolumeCommand(),
			PhonemeCommand("private-ipa", None),
		]
		items = self.converter.convert(sequence, voiceId="mockVoice", rate=50).items
		self.assertEqual(jobs.IndexItem(0), items[0])
		self.assertEqual(jobs.CharacterModeItem(True), items[1])
		self.assertEqual(jobs.CharacterModeItem(False), items[2])
		self.assertEqual(jobs.LanguageChangeItem(None), items[3])
		self.assertEqual(jobs.BreakItem(0), items[4])
		self.assertEqual(jobs.ProsodyItem(jobs.ProsodyCommandType.RATE, 0, 1.25, False), items[5])
		self.assertEqual(jobs.ProsodyItem(jobs.ProsodyCommandType.PITCH, -4, 1, False), items[6])
		self.assertEqual(jobs.ProsodyItem(jobs.ProsodyCommandType.VOLUME, 0, 1, True), items[7])
		self.assertEqual(jobs.PhonemeItem("private-ipa", None), items[8])
		self.assertNotIn("private-ipa", repr(items[8]))

	def test_top_level_contract_accepts_only_exact_list(self) -> None:
		for value in (("text",), {"text": 1}, b"text", (item for item in ["text"])):
			with self.subTest(valueType=type(value)), self.assertRaises(TypeError):
				self.converter.convert(value, voiceId="mockVoice", rate=50)
		class ListSubclass(list):
			pass
		with self.assertRaises(TypeError):
			self.converter.convert(ListSubclass(["text"]), voiceId="mockVoice", rate=50)

	def test_unsupported_items_do_not_leak_or_consume_identifiers(self) -> None:
		class Hostile:
			def __repr__(self):
				raise AssertionError("unsupported item was represented")
			def __str__(self):
				raise AssertionError("unsupported item was converted to text")
			def __iter__(self):
				raise AssertionError("unsupported item was iterated")
			def __eq__(self, other):
				raise AssertionError("unsupported item was compared")
			def __format__(self, formatSpec):
				raise AssertionError("unsupported item was formatted")
			def __reduce__(self):
				raise AssertionError("unsupported item was serialized")
		first = self.converter.convert([], voiceId="mockVoice", rate=50)
		for item in (
			Hostile(),
			CallbackCommand(),
			ConfigProfileTriggerCommand(),
			EndUtteranceCommand(),
			SuppressUnicodeNormalizationCommand(),
			42,
			b"private",
			IndexCommand,
		):
			with self.subTest(itemType=type(item)), self.assertRaises(conversion.UnsupportedSpeechItemError) as error:
				self.converter.convert([item], voiceId="mockVoice", rate=50)
			self.assertNotIn("private", str(error.exception))
		second = self.converter.convert([], voiceId="mockVoice", rate=50)
		self.assertEqual((1, 1, 1), (first.jobId, first.generationId, first.requestNumber))
		self.assertEqual((2, 2, 2), (second.jobId, second.generationId, second.requestNumber))

	def test_subclasses_and_malformed_commands_are_rejected_atomically(self) -> None:
		class IndexSubclass(IndexCommand):
			pass
		malformedIndex = IndexCommand.__new__(IndexCommand)
		malformedIndex.index = True
		malformedBreak = BreakCommand.__new__(BreakCommand)
		malformedBreak.time = False
		malformedLanguage = LangChangeCommand.__new__(LangChangeCommand)
		malformedLanguage.lang = 1
		malformedLanguage.isDefault = False
		malformedPhoneme = PhonemeCommand(b"ipa", "fallback")
		for item, errorType in (
			(IndexSubclass(1), conversion.UnsupportedSpeechItemError),
			(malformedIndex, TypeError),
			(malformedBreak, TypeError),
			(malformedLanguage, TypeError),
			(malformedPhoneme, TypeError),
		):
			with self.subTest(itemType=type(item)), self.assertRaises(errorType):
				self.converter.convert(["private", item], voiceId="mockVoice", rate=50)
		job = self.converter.convert(["after"], voiceId="mockVoice", rate=50)
		self.assertEqual(1, job.jobId)

	def test_malformed_prosody_is_rejected_without_derived_properties(self) -> None:
		for item in (RateCommand(offset=True), PitchCommand(offset=2, multiplier=3)):
			with self.subTest(itemType=type(item)), self.assertRaises((TypeError, ValueError)):
				self.converter.convert([item], voiceId="mockVoice", rate=50)

	def test_settings_are_validated_before_identifier_assignment(self) -> None:
		for voice, rate, errorType in (("", 50, ValueError), (None, 50, ValueError), ("mockVoice", True, TypeError), ("mockVoice", 101, ValueError)):
			with self.subTest(voice=voice, rate=rate), self.assertRaises(errorType):
				self.converter.convert([], voiceId=voice, rate=rate)
		self.assertEqual(1, self.converter.convert([], voiceId="mockVoice", rate=50).jobId)

	def test_new_converter_has_deterministic_bounded_ids(self) -> None:
		first = conversion.SpeechJobConverter().convert([], voiceId="mockVoice", rate=50)
		secondConverter = conversion.SpeechJobConverter()
		self.assertEqual((1, 1, 1), (first.jobId, first.generationId, first.requestNumber))
		secondConverter._nextGenerationId = 7
		secondConverter._nextRequestNumber = 9
		separate = secondConverter.convert([], voiceId="mockVoice", rate=50)
		self.assertEqual((1, 7, 9), (separate.jobId, separate.generationId, separate.requestNumber))
		secondConverter._nextJobId = conversion._MAX_IDENTIFIER + 1
		with self.assertRaises(OverflowError):
			secondConverter.convert([], voiceId="mockVoice", rate=50)

	def test_driver_boundary_snapshots_settings_and_respects_lifecycle(self) -> None:
		driverModule = _loadDriverModule()
		marker = {
			driverModule._TEST_ONLY_MARKER_ENV: driverModule._TEST_ONLY_MARKER_VALUE,
			driverModule._RUNTIME_PATH_ENV: "runtime.exe",
			driverModule._MODEL_PATH_ENV: "voice.onnx",
			driverModule._CONFIG_PATH_ENV: "voice.onnx.json",
		}
		with patch.dict(os.environ, marker, clear=True):
			driver = driverModule.SynthDriver()
			source = ["private text"]
			job = driver._createSpeechJob(source)
			driver.rate = 75
			source[0] = "changed"
			self.assertEqual("private text", job.items[0].text)
			self.assertEqual("configuredModel", job.voiceId)
			self.assertEqual(50, job.rate)
			driver._voice = "unknown"
			with self.assertRaisesRegex(LookupError, "active voice ID"):
				driver._createSpeechJob([])
			driver._voice = "configuredModel"
			driver._rate = True
			with self.assertRaises(TypeError):
				driver._createSpeechJob([])
			driver._rate = 75
			self.assertEqual(2, driver._createSpeechJob([]).jobId)
			driver.terminate()
			self.assertEqual("private text", job.items[0].text)
			with self.assertRaisesRegex(RuntimeError, "terminated"):
				driver._createSpeechJob([])


if __name__ == "__main__":
	unittest.main()
