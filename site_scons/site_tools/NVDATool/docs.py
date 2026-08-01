import gettext
from pathlib import Path

import markdown

from .typings import AddonInfo


def md2html(
	source: str | Path,
	dest: str | Path,
	*,
	moFile: str | Path | None,
	mdExtensions: list[str],
	addon_info: AddonInfo,
) -> None:
	sourcePath = Path(source)
	destinationPath = Path(dest)
	translationPath = Path(moFile) if moFile else None
	try:
		with translationPath.open("rb") as translationFile:  # type: ignore[union-attr]
			translate = gettext.GNUTranslations(translationFile).gettext
	except Exception:
		summary = addon_info["addon_summary"]
	else:
		summary = translate(addon_info["addon_summary"])

	markdownText = sourcePath.read_text(encoding="utf-8")
	htmlText = markdown.markdown(markdownText, extensions=mdExtensions)
	language = sourcePath.parent.name.replace("_", "-")
	document = "\n".join(
		(
			"<!DOCTYPE html>",
			f'<html lang="{language}">',
			"<head>",
			'<meta charset="UTF-8">',
			'<meta name="viewport" content="width=device-width, initial-scale=1.0">',
			f"<title>{summary} {addon_info['addon_version']}</title>",
			"</head>",
			"<body>",
			htmlText,
			"</body>",
			"</html>",
		)
	)
	destinationPath.write_text(document, encoding="utf-8")
