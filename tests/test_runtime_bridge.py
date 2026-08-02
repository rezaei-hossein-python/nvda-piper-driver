"""Pure tests for the bounded one-shot process boundary used by Phase 2J."""

import ast
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import Mock, patch

from addon.synthDrivers._nvdaPiperDriver.runtimeBridge import (
	MAX_PCM_BYTES,
	OneShotRuntimeBridge,
	PersistentRuntimeBridge,
	RuntimeBridgeCancelled,
	RuntimeBridgeError,
	readModelLanguage,
	validateRuntimePaths,
)


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "addon" / "synthDrivers" / "_nvdaPiperDriver" / "runtimeBridge.py"
WORKER_PATH = ROOT / "addon" / "synthDrivers" / "_nvdaPiperDriver" / "runtimeWorker.py"


class RuntimeBridgeTests(unittest.TestCase):
	@staticmethod
	def _responsePayload() -> bytes:
		header = json.dumps(
			{"channels": 1, "generationId": 7, "jobId": 9, "sampleRate": 16000, "sampleWidth": 2},
			separators=(",", ":"),
			sort_keys=True,
		).encode()
		return struct.pack("<I", len(header)) + header + b"\x01\x00"

	def test_explicit_paths_are_required(self) -> None:
		paths = (ROOT / "python.exe", ROOT / "voice.onnx", ROOT / "voice.onnx.json")
		with patch.object(Path, "is_file", return_value=True):
			self.assertEqual(paths, validateRuntimePaths(*(str(path) for path in paths)))
			for index in range(3):
				bad = list(str(path) for path in paths)
				bad[index] += ".missing"
				with self.assertRaises(RuntimeBridgeError):
					validateRuntimePaths(*bad)

	def test_response_is_correlated_and_format_checked(self) -> None:
		payload = self._responsePayload()
		result = OneShotRuntimeBridge._decodeResponse(payload, 7, 9)
		self.assertEqual((7, 9, 16000, 1, 2, b"\x01\x00"), (result.generationId, result.jobId, result.sampleRate, result.channels, result.sampleWidth, result.pcm))
		with self.assertRaisesRegex(RuntimeBridgeError, "stale PCM"):
			OneShotRuntimeBridge._decodeResponse(payload, 8, 9)

	def test_language_is_model_metadata_not_a_control_branch(self) -> None:
		with patch.object(Path, "stat", return_value=type("Stat", (), {"st_size": 100})()), patch.object(
			Path, "read_bytes", return_value='{"language":{"code":"arbitrary_LOCALE"}}'.encode("utf-8"),
		):
			self.assertEqual("arbitrary_LOCALE", readModelLanguage(ROOT / "voice.onnx.json"))

	def test_response_bounds_and_malformed_data(self) -> None:
		for payload in (b"", struct.pack("<I", 0), struct.pack("<I", 2) + b"{}" + b"x" * (MAX_PCM_BYTES + 1)):
			with self.subTest(size=len(payload)), self.assertRaises(RuntimeBridgeError):
				OneShotRuntimeBridge._decodeResponse(payload, 1, 1)

	def test_subprocess_arguments_exit_status_and_private_stderr(self) -> None:
		with patch.object(Path, "is_file", return_value=True):
			bridge = OneShotRuntimeBridge("runtime.exe", "voice.onnx", "voice.onnx.json", "runtimeWorker.py")
		process = Mock()
		process.poll.return_value = None
		process.returncode = 0
		process.communicate.return_value = (self._responsePayload(), b"")
		with patch("addon.synthDrivers._nvdaPiperDriver.runtimeBridge.subprocess.Popen", return_value=process) as popen:
			bridge.synthesize("private fixture", 7, 9)
		command = popen.call_args.args[0]
		self.assertIs(type(command), list)
		self.assertEqual(
			[
				str((ROOT / "runtime.exe").resolve()),
				"-I",
				str((ROOT / "runtimeWorker.py").resolve()),
				"--model",
				str((ROOT / "voice.onnx").resolve()),
				"--config",
				str((ROOT / "voice.onnx.json").resolve()),
			],
			command,
		)
		self.assertIs(popen.call_args.kwargs["shell"], False)
		process.returncode = 3
		process.communicate.return_value = (b"", b"private fixture and local path")
		with patch("addon.synthDrivers._nvdaPiperDriver.runtimeBridge.subprocess.Popen", return_value=process):
			with self.assertRaises(RuntimeBridgeError) as caught:
				bridge.synthesize("private fixture", 7, 9)
		self.assertNotIn("private fixture", str(caught.exception))
		self.assertNotIn("local path", str(caught.exception))

	def test_interrupt_is_nonblocking_and_invalidates_racing_work(self) -> None:
		with patch.object(Path, "is_file", return_value=True):
			bridge = OneShotRuntimeBridge("runtime.exe", "voice.onnx", "voice.onnx.json", "runtimeWorker.py")
		token = bridge.cancellationToken
		bridge.interrupt()
		with self.assertRaises(RuntimeBridgeCancelled):
			bridge.synthesize("private fixture", 1, 1, cancellationToken=token)

	def test_persistent_interrupt_does_not_consume_restart_budget(self) -> None:
		bridge = PersistentRuntimeBridge.__new__(PersistentRuntimeBridge)
		bridge._processLock = __import__("threading").Lock()
		bridge._cancellationToken = 0
		bridge._restartCount = 2
		process = Mock()
		process.poll.return_value = None
		bridge._process = process
		bridge.interrupt()
		self.assertEqual(0, bridge._restartCount)
		process.terminate.assert_called_once_with()

	def test_worker_has_no_network_or_language_specific_logic(self) -> None:
		for path in (BRIDGE_PATH, WORKER_PATH):
			tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
			imports = {
				node.module.split(".")[0]
				for node in ast.walk(tree)
				if isinstance(node, ast.ImportFrom) and node.module
			}
			imports.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
			self.assertTrue(imports.isdisjoint({"http", "requests", "socket", "urllib"}))
			text = path.read_text(encoding="utf-8").casefold()
			for forbidden in ("persian", "farsi", "arabic", "locale allowlist", "script detection"):
				self.assertNotIn(forbidden, text)

	def test_retained_local_runtime_produces_pcm_and_exits(self) -> None:
		runtime = os.environ.get("NVDA_PIPER_RUNTIME_PYTHON")
		model = os.environ.get("NVDA_PIPER_MODEL_PATH")
		config = os.environ.get("NVDA_PIPER_CONFIG_PATH")
		if not all((runtime, model, config)):
			self.skipTest("Set explicit Phase 2J runtime/model/config paths for child integration")
		bridge = OneShotRuntimeBridge(runtime, model, config, str(WORKER_PATH))  # type: ignore[arg-type]
		result = bridge.synthesize("Bounded child integration fixture.", 1, 1)
		self.assertEqual((1, 1, 1, 2), (result.generationId, result.jobId, result.channels, result.sampleWidth))
		self.assertGreater(result.sampleRate, 0)
		self.assertGreater(len(result.pcm), 0)
		self.assertIsNone(bridge.processId)
		self.assertNotIn("text", bridge.__dict__)


if __name__ == "__main__":
	unittest.main()
