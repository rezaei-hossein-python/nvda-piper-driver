"""Build metadata for the development-only NVDA add-on package."""

from typing import Any, TypeAlias
import os


AddonInfo: TypeAlias = dict[str, Any]
BrailleTables: TypeAlias = dict[str, Any]
SpeechDictionaries: TypeAlias = dict[str, Any]
SymbolDictionaries: TypeAlias = dict[str, Any]


def _(argument: str) -> str:
	"""Mark build metadata text without importing the SCons build tool at test time."""
	return argument


if os.environ.get("NVDA_PIPER_AUDIO_OPTIMIZED_PACKAGE") == "1":
	_packageName, _packageSummary = "nvdaPiperDriverAudioOptimized", "NVDA Piper Driver (audio optimized experiment)"
elif os.environ.get("NVDA_PIPER_EVENT_FIDELITY_PACKAGE") == "1":
	_packageName, _packageSummary = "nvdaPiperDriverEventFidelity", "NVDA Piper Driver (event fidelity experiment)"
elif os.environ.get("NVDA_PIPER_EXPERIMENTAL_PACKAGE") == "1":
	_packageName, _packageSummary = "nvdaPiperDriverExperimental", "NVDA Piper Driver (experimental short speech)"
else:
	_packageName, _packageSummary = "nvdaPiperDriver", "NVDA Piper Driver"

addon_info = AddonInfo(
	addon_name=_packageName,
	# Translators: Summary shown in NVDA's add-on management interface.
	addon_summary=_(_packageSummary),
	# Translators: Description shown in NVDA's add-on management interface.
	addon_description=_(
		"Development-only Piper speech prototype requiring explicit local runtime and model paths. "
		"Not intended for normal NVDA installations."
	),
	addon_version=("0.1.0" if os.environ.get("NVDA_PIPER_EXPERIMENTAL_PACKAGE") == "1" else "0.1.0"),
	# Translators: Changes in this development package.
	addon_changelog=_("Replaces blocking synthesis with one bounded background request for Phase 2J validation."),
	addon_author="Hosein Rezaei",
	addon_url="https://github.com/rezaei-hossein-python/nvda-piper-driver",
	addon_sourceURL="https://github.com/rezaei-hossein-python/nvda-piper-driver",
	addon_docFileName="readme.html",
	addon_minimumNVDAVersion="2026.1.0",
	addon_lastTestedNVDAVersion="2026.1.0",
	addon_updateChannel="dev",
	addon_license="GPL-2.0-or-later",
	addon_licenseURL="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
)

# Phase 2J adds only project-owned controller/bridge/worker code; runtime and model assets stay external.
pythonSources: list[str] = [
	"addon/synthDrivers/nvdaPiperDriver.py",
	"addon/synthDrivers/_nvdaPiperDriver/*.py",
]
i18nSources: list[str] = ["buildVars.py"]

# Markdown is a build input; only generated HTML belongs in the package.
excludedFiles: list[str] = ["doc/**/*.md", "**/__pycache__/**", "**/*.pyc"]
baseLanguage: str = "en"
markdownExtensions: list[str] = []
brailleTables: BrailleTables = {}
symbolDictionaries: SymbolDictionaries = {}
speechDictionaries: SpeechDictionaries = {}
