"""Unit tests for the development-only portable validation harness."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools" / "portableNvdaValidation"
spec = importlib.util.spec_from_file_location("validationCore", HARNESS / "validationCore.py")
assert spec and spec.loader
validationCore = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validationCore
spec.loader.exec_module(validationCore)


class PortableHarnessTests(unittest.TestCase):
	def test_portable_path_rejects_primary_paths(self) -> None:
		with self.assertRaises(validationCore.HarnessError):
			validationCore.requirePortablePath(Path(r"C:\Program Files\NVDA"))

	def test_archive_traversal_is_rejected(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			package = Path(directory) / "bad.nvda-addon"
			with zipfile.ZipFile(package, "w") as archive:
				archive.writestr("../outside.txt", "x")
			with self.assertRaises(validationCore.HarnessError):
				validationCore.validateArchive(package)

	def test_report_contains_no_fixture_text(self) -> None:
		metadata = validationCore.RunMetadata("control", "abc", r"D:\NVDA\phase2lControl", 1)
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "result.json"
			validationCore.writeReport(path, metadata, scenarios={"character": {"status": "pass"}}, errors=[])
			self.assertNotIn("hello", path.read_text(encoding="utf-8"))

	def test_archive_allowlist_is_nonempty_and_excludes_harness(self) -> None:
		self.assertIn("manifest.ini", validationCore.ALLOWED_ARCHIVE_FILES)
		self.assertFalse(any("portableNvdaValidation" in name for name in validationCore.ALLOWED_ARCHIVE_FILES))

	def test_running_nvda_is_refused(self) -> None:
		original = validationCore.runningNvdaPids
		validationCore.runningNvdaPids = lambda: (1234,)
		try:
			with self.assertRaises(validationCore.HarnessError):
				validationCore.refuseIfNvdaRunning()
		finally:
			validationCore.runningNvdaPids = original

	def test_pinned_system_test_components_exist(self) -> None:
		reference = ROOT / "references" / "nvda-source"
		for relative in (
			"tests/system/libraries/NvdaLib.py",
			"tests/system/libraries/SystemTestSpy/speechSpyGlobalPlugin.py",
			"tests/system/libraries/SystemTestSpy/speechSpySynthDriver.py",
		):
			self.assertTrue((reference / relative).is_file(), relative)


if __name__ == "__main__":
	unittest.main()
