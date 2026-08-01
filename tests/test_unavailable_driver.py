"""Isolated tests for the deliberately unavailable Phase 2B driver."""

import ast
from abc import ABC, abstractmethod
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "addon" / "synthDrivers" / "nvdaPiperDriver.py"
MODULE_NAME = "phase2b_test_nvdaPiperDriver"
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
	def test_module_path_and_identity(self) -> None:
		self.assertTrue(DRIVER_PATH.is_file())
		module = loadDriverModule()
		self.assertTrue(issubclass(module.SynthDriver, StubSynthDriver))
		self.assertEqual(DRIVER_PATH.stem, module.SynthDriver.name)
		self.assertEqual("NVDA Piper Driver", module.SynthDriver.description)

	def test_check_returns_exactly_false(self) -> None:
		module = loadDriverModule()
		self.assertIs(module.SynthDriver.check(), False)

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
		self.assertEqual({"synthDriverHandler"}, imports)
		self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORT_ROOTS))

	def test_unexpected_speak_fails_without_using_sequence(self) -> None:
		module = loadDriverModule()
		driver = object.__new__(module.SynthDriver)
		with self.assertRaisesRegex(RuntimeError, "unavailable NVDA Piper Driver"):
			driver.speak(["private sentinel text"])


if __name__ == "__main__":
	unittest.main()
