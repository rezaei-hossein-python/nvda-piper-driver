"""Focused metadata and archive checks for the NVDA add-on package."""

import configparser
import os
from pathlib import Path, PurePosixPath
import unittest
import zipfile

import buildVars


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ARCHIVE_FILES = {
	"doc/en/readme.html",
	"manifest.ini",
	"synthDrivers/_nvdaPiperDriver/__init__.py",
	"synthDrivers/_nvdaPiperDriver/conversion.py",
	"synthDrivers/_nvdaPiperDriver/fakeWorker.py",
	"synthDrivers/_nvdaPiperDriver/jobs.py",
	"synthDrivers/_nvdaPiperDriver/protocol.py",
	"synthDrivers/nvdaPiperDriver.py",
}
FORBIDDEN_EXTENSIONS = {".dll", ".exe", ".nvda-addon", ".onnx", ".pyc", ".wav"}
REQUIRED_MANIFEST_FIELDS = {
	"author",
	"description",
	"docfilename",
	"lasttestednvdaversion",
	"minimumnvdaversion",
	"name",
	"summary",
	"updatechannel",
	"url",
	"version",
}


def _read_manifest(archive: zipfile.ZipFile) -> configparser.SectionProxy:
	text = archive.read("manifest.ini").decode("utf-8")
	parser = configparser.ConfigParser()
	parser.read_string("[manifest]\n" + text)
	return parser["manifest"]


class SourceMetadataTests(unittest.TestCase):
	def test_internal_name_and_version_are_valid(self) -> None:
		info = buildVars.addon_info
		self.assertRegex(info["addon_name"], r"^[A-Za-z0-9_-]+$")
		self.assertRegex(info["addon_version"], r"^\d+\.\d+(?:\.\d+)?$")

	def test_required_metadata_is_present(self) -> None:
		info = buildVars.addon_info
		for key in (
			"addon_name",
			"addon_summary",
			"addon_description",
			"addon_author",
			"addon_url",
			"addon_version",
			"addon_docFileName",
			"addon_minimumNVDAVersion",
			"addon_lastTestedNVDAVersion",
			"addon_updateChannel",
		):
			self.assertTrue(info[key], key)

	def test_help_source_exists(self) -> None:
		self.assertTrue((ROOT / "addon" / "doc" / "en" / "readme.md").is_file())

	def test_only_expected_python_sources_exist(self) -> None:
		pythonFiles = sorted(path.relative_to(ROOT / "addon").as_posix() for path in (ROOT / "addon").rglob("*.py"))
		self.assertEqual(sorted(EXPECTED_ARCHIVE_FILES - {"doc/en/readme.html", "manifest.ini"}), pythonFiles)
		supportPackage = ROOT / "addon" / "synthDrivers" / "_nvdaPiperDriver"
		self.assertTrue(supportPackage.name.startswith("_"))
		self.assertTrue((supportPackage / "__init__.py").is_file())


class BuiltArchiveTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		package = os.environ.get("NVDA_ADDON_PACKAGE")
		if not package:
			raise unittest.SkipTest("Set NVDA_ADDON_PACKAGE to validate a built archive")
		cls.packagePath = Path(package).resolve()

	def test_archive_allowlist(self) -> None:
		with zipfile.ZipFile(self.packagePath) as archive:
			files = {name for name in archive.namelist() if not name.endswith("/")}
		self.assertEqual(EXPECTED_ARCHIVE_FILES, files)

	def test_archive_has_no_forbidden_paths_or_extensions(self) -> None:
		with zipfile.ZipFile(self.packagePath) as archive:
			for name in archive.namelist():
				path = PurePosixPath(name)
				self.assertNotIn("..", path.parts)
				self.assertFalse(path.is_absolute())
				self.assertNotIn(path.suffix.lower(), FORBIDDEN_EXTENSIONS)
				self.assertFalse(any(part in {".git", "references", "tests"} for part in path.parts))

	def test_built_manifest(self) -> None:
		with zipfile.ZipFile(self.packagePath) as archive:
			manifest = _read_manifest(archive)
			self.assertTrue(REQUIRED_MANIFEST_FIELDS.issubset(manifest.keys()))
			self.assertEqual("nvdaPiperDriver", manifest["name"])
			self.assertEqual("NVDA Piper Driver", manifest["summary"].strip('"'))
			self.assertEqual("0.1.0", manifest["version"])
			self.assertEqual("2026.1.0", manifest["minimumNVDAVersion"])
			self.assertEqual("2026.1.0", manifest["lastTestedNVDAVersion"])
			self.assertEqual("dev", manifest["updateChannel"])
			self.assertEqual("readme.html", manifest["docFileName"])
			self.assertRegex(manifest["url"], r"^https://")

	def test_help_is_accessible_html(self) -> None:
		with zipfile.ZipFile(self.packagePath) as archive:
			helpText = archive.read("doc/en/readme.html").decode("utf-8")
		self.assertIn('<html lang="en">', helpText)
		self.assertIn("<h1>", helpText)
		self.assertIn("unavailable by default", helpText.lower())


if __name__ == "__main__":
	unittest.main()
