import zipfile
from collections.abc import Iterable
from pathlib import Path


def matchesNoPatterns(path: Path, patterns: Iterable[str]) -> bool:
	return not any(path.match(pattern) for pattern in patterns)


def createAddonBundleFromPath(path: str | Path, dest: str, excludePatterns: Iterable[str]):
	if isinstance(path, str):
		path = Path(path)
	baseDirectory = path.absolute()
	with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
		for candidate in baseDirectory.rglob("*"):
			if candidate.is_dir():
				continue
			pathInBundle = candidate.relative_to(baseDirectory)
			if matchesNoPatterns(pathInBundle, excludePatterns):
				archive.write(candidate, pathInBundle)
	return dest
