"""Build metadata for the metadata-only NVDA add-on package."""

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SpeechDictionaries, SymbolDictionaries
from site_scons.site_tools.NVDATool.utils import _


addon_info = AddonInfo(
	addon_name="nvdaPiperDriver",
	# Translators: Summary shown in NVDA's add-on management interface.
	addon_summary=_("NVDA Piper Driver"),
	# Translators: Description shown in NVDA's add-on management interface.
	addon_description=_(
		"Provides the project foundation for an offline NVDA synthesizer driver using Piper-compatible neural "
		"voices. Speech functionality is not included in this development package yet."
	),
	addon_version="0.1.0",
	# Translators: Changes in this development package.
	addon_changelog=_("Metadata and documentation package only; no synthesizer functionality is included."),
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

# Phase 2G packages the unavailable driver plus pure conversion/protocol test support.
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
