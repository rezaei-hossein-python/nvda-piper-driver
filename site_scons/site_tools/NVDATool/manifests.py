import codecs
import gettext
from functools import partial

from .typings import AddonInfo, BrailleTables, SpeechDictionaries, SymbolDictionaries
from .utils import format_nested_section


def generateManifest(
	source: str,
	dest: str,
	addon_info: AddonInfo,
	brailleTables: BrailleTables,
	symbolDictionaries: SymbolDictionaries,
	speechDictionaries: SpeechDictionaries,
) -> None:
	with codecs.open(source, "r", "utf-8") as sourceFile:
		manifest = sourceFile.read().format(**addon_info)
	if brailleTables:
		manifest += format_nested_section("brailleTables", brailleTables)
	if symbolDictionaries:
		manifest += format_nested_section("symbolDictionaries", symbolDictionaries)
	if speechDictionaries:
		manifest += format_nested_section("speechDictionaries", speechDictionaries)
	with codecs.open(dest, "w", "utf-8") as destinationFile:
		destinationFile.write(manifest)


def generateTranslatedManifest(
	source: str,
	dest: str,
	*,
	mo: str,
	addon_info: AddonInfo,
	brailleTables: BrailleTables,
	symbolDictionaries: SymbolDictionaries,
	speechDictionaries: SpeechDictionaries,
) -> None:
	with open(mo, "rb") as translationFile:
		translate = gettext.GNUTranslations(translationFile).gettext
	variables = {
		key: translate(addon_info[key])
		for key in ("addon_summary", "addon_description", "addon_changelog")
	}
	with codecs.open(source, "r", "utf-8") as sourceFile:
		manifest = sourceFile.read().format(**variables)
	formatDisplayNames = partial(format_nested_section, include_only_keys=("displayName",), _=translate)
	if brailleTables:
		manifest += formatDisplayNames("brailleTables", brailleTables)
	if symbolDictionaries:
		manifest += formatDisplayNames("symbolDictionaries", symbolDictionaries)
	if speechDictionaries:
		manifest += formatDisplayNames("speechDictionaries", speechDictionaries)
	with codecs.open(dest, "w", "utf-8") as destinationFile:
		destinationFile.write(manifest)
