"""Safety-first helpers for disposable portable NVDA validation.

This module never launches NVDA by itself. It validates the exact D:\\NVDA
portable root, refuses unrelated running NVDA processes, extracts only a
verified add-on archive, and produces content-free reports.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import shutil
import time
import zipfile


PORTABLE_ROOT = Path(r"D:\NVDA")
ADDON_NAME = "nvdaPiperDriver"
ALLOWED_ARCHIVE_FILES = {
	"doc/en/readme.html", "manifest.ini",
	"synthDrivers/nvdaPiperDriver.py",
	"synthDrivers/_nvdaPiperDriver/__init__.py",
	"synthDrivers/_nvdaPiperDriver/backgroundController.py",
	"synthDrivers/_nvdaPiperDriver/conversion.py",
	"synthDrivers/_nvdaPiperDriver/fakeWorker.py",
	"synthDrivers/_nvdaPiperDriver/jobs.py",
	"synthDrivers/_nvdaPiperDriver/latencyMetrics.py",
	"synthDrivers/_nvdaPiperDriver/protocol.py",
	"synthDrivers/_nvdaPiperDriver/runtimeBridge.py",
	"synthDrivers/_nvdaPiperDriver/runtimeWorker.py",
}


class HarnessError(RuntimeError):
	pass


def sha256(path: Path) -> str:
	hashObject = hashlib.sha256()
	with path.open("rb") as stream:
		for block in iter(lambda: stream.read(1024 * 1024), b""):
			hashObject.update(block)
	return hashObject.hexdigest()


def requirePortablePath(path: Path, *, mustExist: bool = False) -> Path:
	resolved = path.resolve(strict=False)
	root = PORTABLE_ROOT.resolve(strict=False)
	if resolved != root and root not in resolved.parents:
		raise HarnessError("portable paths must remain below D:\\NVDA")
	if mustExist and not resolved.exists():
		raise HarnessError(f"required portable path is missing: {resolved.name}")
	return resolved


def runningNvdaPids() -> tuple[int, ...]:
	result = subprocess.run(
		["tasklist", "/FI", "IMAGENAME eq nvda.exe", "/FO", "CSV", "/NH"],
		check=True, capture_output=True, text=True,
	)
	pids: list[int] = []
	for line in result.stdout.splitlines():
		parts = [part.strip('"') for part in line.split('","')]
		if len(parts) >= 2 and parts[0].lower() == "nvda.exe":
			try:
				pids.append(int(parts[1]))
			except ValueError:
				continue
	return tuple(sorted(set(pids)))


def refuseIfNvdaRunning() -> None:
	pids = runningNvdaPids()
	if pids:
		raise HarnessError(f"NVDA is already running (PIDs: {','.join(map(str, pids))}); close it manually")


def validateArchive(package: Path) -> dict[str, str]:
	if package.suffix.lower() != ".nvda-addon" or not package.is_file():
		raise HarnessError("package must be an existing .nvda-addon file")
	with zipfile.ZipFile(package) as archive:
		names = {name for name in archive.namelist() if not name.endswith("/")}
		if names != ALLOWED_ARCHIVE_FILES:
			raise HarnessError("package members do not match the approved allowlist")
		for name in names:
			parts = PurePosixPath(name).parts
			if PurePosixPath(name).is_absolute() or ".." in parts:
				raise HarnessError("archive traversal path rejected")
	with zipfile.ZipFile(package) as archive:
		manifest = archive.read("manifest.ini").decode("utf-8")
	if "name = nvdaPiperDriver" not in manifest or "version = 0.1.0" not in manifest:
		raise HarnessError("unexpected add-on manifest identity")
	return {"sha256": sha256(package), "memberCount": str(len(names))}


def installArchive(package: Path, configPath: Path) -> None:
	configPath = requirePortablePath(configPath)
	configPath.mkdir(parents=True, exist_ok=True)
	marker = configPath / ".phase2l-harness-owned.json"
	if marker.exists():
		try:
			owner = json.loads(marker.read_text(encoding="utf-8"))
		except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
			raise HarnessError("portable config ownership marker is invalid") from error
		if owner.get("owner") != "nvda-piper-phase2l-harness-v1":
			raise HarnessError("portable config is not owned by this harness")
	elif any(configPath.iterdir()):
		raise HarnessError("refusing to overwrite a non-harness portable config")
	marker.write_text(json.dumps({"owner": "nvda-piper-phase2l-harness-v1"}, sort_keys=True), encoding="utf-8")
	addonPath = configPath / "addons" / ADDON_NAME
	if addonPath.exists():
		shutil.rmtree(addonPath)
	addonPath.mkdir(parents=True, exist_ok=True)
	with zipfile.ZipFile(package) as archive:
		for name in sorted(ALLOWED_ARCHIVE_FILES):
			destination = addonPath / Path(*PurePosixPath(name).parts)
			destination.parent.mkdir(parents=True, exist_ok=True)
			destination.write_bytes(archive.read(name))


def installAdapter(adapterSource: Path, configPath: Path) -> Path:
	"""Install only the two adapter modules into an owned config."""
	configPath = requirePortablePath(configPath, mustExist=True)
	if not adapterSource.is_dir():
		raise HarnessError("adapter source directory is missing")
	destination = configPath / "globalPlugins" / "nvdaValidationAdapter"
	if destination.exists():
		shutil.rmtree(destination)
	destination.mkdir(parents=True, exist_ok=True)
	for name in ("adapterProtocol.py", "nvdaValidationAdapter.py"):
		source = adapterSource / name
		if not source.is_file():
			raise HarnessError(f"adapter source file is missing: {name}")
		(destination / name).write_bytes(source.read_bytes())
	return destination


def removeAdapter(configPath: Path) -> None:
	path = requirePortablePath(configPath, mustExist=True) / "globalPlugins" / "nvdaValidationAdapter"
	if path.exists():
		shutil.rmtree(path)


@dataclass(frozen=True, slots=True)
class RunMetadata:
	mode: str
	packageSha256: str
	configPath: str
	startedNs: int
	pid: int | None = None
	verdict: str = "not-run"


def writeReport(path: Path, metadata: RunMetadata, *, scenarios: dict[str, object], errors: list[str]) -> None:
	report = {"metadata": asdict(metadata), "scenarios": scenarios, "errors": errors}
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
