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


class StubSynthDriver(ABC):
	def __init__(self) -> None:
		self.baseInitialized = True
		self.baseTerminateCalls = 0

	def terminate(self) -> None:
		self.baseTerminateCalls += 1

	@abstractmethod
	def speak(self, speechSequence) -> None:
		raise NotImplementedError


def loadDriverModule() -> types.ModuleType:
	stubHandler = types.ModuleType("synthDriverHandler")
	stubHandler.SynthDriver = StubSynthDriver  # type: ignore[attr-defined]
	spec = importlib.util.spec_from_file_location(MODULE_NAME, DRIVER_PATH)
	if spec is None or spec.loader is None:
		raise AssertionError("Unable to create driver import specification")
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {"synthDriverHandler": stubHandler, MODULE_NAME: module}):
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
		self.assertEqual({"os", "synthDriverHandler"}, imports)
		self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORT_ROOTS))

	def test_construction_requires_marker_and_owns_no_runtime_resources(self) -> None:
		with patch.dict(os.environ, {}, clear=True):
			with self.assertRaisesRegex(RuntimeError, "test availability marker"):
				self.module.SynthDriver()
		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		self.assertEqual(
			{"baseInitialized": True, "baseTerminateCalls": 0, "_isTerminated": False},
			driver.__dict__,
		)

	def test_termination_delegates_once(self) -> None:
		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		driver.terminate()
		driver.terminate()
		self.assertTrue(driver._isTerminated)
		self.assertEqual(1, driver.baseTerminateCalls)

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

		with self._availableEnvironment():
			driver = self.module.SynthDriver()
		with self.assertRaisesRegex(RuntimeError, "test-only NVDA Piper Driver"):
			driver.speak(PrivateSpeechSequence())


if __name__ == "__main__":
	unittest.main()
