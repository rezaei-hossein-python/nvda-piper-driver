"""Run preflight, installation, optional portable launch, and reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import os
import secrets
import subprocess
import time

from validationCore import HarnessError, PORTABLE_ROOT, RunMetadata, installAdapter, installArchive, removeAdapter, refuseIfNvdaRunning, validateArchive, writeReport


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / ".phase2h-assets" / "en_US-lessac-low" / "en_US-lessac-low.onnx"
CONFIG = ROOT / ".phase2h-assets" / "en_US-lessac-low" / "en_US-lessac-low.onnx.json"
RUNTIME = ROOT / ".phase2h-runtime" / "Scripts" / "python.exe"


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--mode", choices=("Control", "Cache", "All", "Functional", "Performance"), default="All")
	parser.add_argument("--package", type=Path, default=ROOT / "nvdaPiperDriver-0.1.0.nvda-addon")
	parser.add_argument("--approve-launch", action="store_true")
	parser.add_argument("--results", type=Path, default=ROOT / "validation-results")
	args = parser.parse_args()
	if not PORTABLE_ROOT.is_dir():
		raise HarnessError("D:\\NVDA is not available")
	for path in (MODEL, CONFIG, RUNTIME, args.package):
		if not path.is_file():
			raise HarnessError(f"required validation asset is missing: {path.name}")
	packageInfo = validateArchive(args.package)
	refuseIfNvdaRunning()
	modes = ("control", "cache") if args.mode == "All" else (args.mode.lower(),)
	for mode in modes:
		configPath = PORTABLE_ROOT / ("phase2lCache" if mode == "cache" else "phase2lControl")
		installArchive(args.package, configPath)
		installAdapter(Path(__file__).with_name("testAdapter"), configPath)
		logPath = configPath / f"phase2l-{mode}.log"
		metadata = RunMetadata(mode, packageInfo["sha256"], configPath.name, time.monotonic_ns())
		errors: list[str] = []
		scenarios: dict[str, object] = {}
		if mode == "cache":
			errors.append("cache backend is not implemented in the production package; this run is preparation-only")
		process = None
		if not args.approve_launch:
			errors.append("launch not approved; preflight and installation completed")
		else:
			env = os.environ.copy()
			env.update({
				"NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME": "phase-2c-explicit-local-mock-runtime-6f4d1c8a",
				"NVDA_PIPER_RUNTIME_PYTHON": str(RUNTIME),
				"NVDA_PIPER_MODEL_PATH": str(MODEL),
				"NVDA_PIPER_CONFIG_PATH": str(CONFIG),
				"NVDA_PIPER_LATENCY_TRACE": "1",
				"NVDA_PIPER_EXPERIMENTAL_CACHE": "1" if mode == "cache" else "0",
				"NVDA_PIPER_VALIDATION_ADAPTER": "1",
			})
			runId = secrets.token_hex(16)
			token = secrets.token_urlsafe(32)
			portFile = configPath / ".validation-port"
			if portFile.exists(): portFile.unlink()
			env["NVDA_PIPER_VALIDATION_RUN_ID"] = runId
			env["NVDA_PIPER_VALIDATION_TOKEN"] = token
			env["NVDA_PIPER_VALIDATION_PORT_FILE"] = str(portFile)
			env["NVDA_PIPER_VALIDATION_CONFIG_MARKER"] = str(configPath / ".phase2l-harness-owned.json")
			process = subprocess.Popen([str(PORTABLE_ROOT / "nvda.exe"), "--config-path", str(configPath), "--log-file", str(logPath), "--log-level", "20"], env=env, cwd=str(PORTABLE_ROOT), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
			metadata = RunMetadata(mode, packageInfo["sha256"], configPath.name, metadata.startedNs, process.pid)
			deadline = time.monotonic() + 30
			while not portFile.exists() and process.poll() is None and time.monotonic() < deadline:
				time.sleep(0.1)
			if not portFile.exists():
				errors.append("adapter did not become ready")
			for scenario in ("startup", "character", "editBox", "navigation", "document", "cancellation", "switching"):
				scenarios[scenario] = {"status": "blocked", "reason": "no approved disposable NVDA test plugin is installed"}
				errors.append(f"{scenario}: objective input automation unavailable")
			if process.poll() is None:
				process.terminate()
				try:
					process.wait(timeout=15)
				except subprocess.TimeoutExpired:
					process.kill()
					process.wait(timeout=5)
			metadata = RunMetadata(mode, packageInfo["sha256"], configPath.name, metadata.startedNs, metadata.pid, "blocked")
			removeAdapter(configPath)
		if not args.approve_launch:
			removeAdapter(configPath)
		writeReport(args.results / f"{mode}.json", metadata, scenarios=scenarios, errors=errors)
	return 3 if any("blocked" in str(item) for item in modes) or errors else 0


if __name__ == "__main__":
	try:
		raise SystemExit(main())
	except HarnessError as error:
		print(f"validation refused: {error}")
		raise SystemExit(2)
