"""Focused tests for the bounded Phase 2J controller."""

from dataclasses import FrozenInstanceError
import os
from pathlib import Path
import threading
import time
import unittest

from addon.synthDrivers._nvdaPiperDriver.backgroundController import (
	BackgroundController,
	BackgroundRequest,
	ControllerState,
	SynthesisSegment,
)
from addon.synthDrivers._nvdaPiperDriver.runtimeBridge import PcmResult, RuntimeBridgeCancelled, RuntimeBridgeError
from addon.synthDrivers._nvdaPiperDriver.runtimeBridge import PersistentRuntimeBridge


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "addon" / "synthDrivers" / "_nvdaPiperDriver" / "runtimeWorker.py"


class FakeBridge:
	def __init__(self) -> None:
		self.token = 0
		self.started = threading.Event()
		self.release = threading.Event()
		self.interruptCalls = 0
		self.texts: list[str] = []
		self.failNext = False

	@property
	def cancellationToken(self) -> int:
		return self.token

	def interrupt(self) -> None:
		self.token += 1
		self.interruptCalls += 1
		self.release.set()

	def forceStop(self) -> None:
		self.interrupt()

	def stop(self) -> None:
		self.interrupt()

	def synthesize(self, text, generationId, jobId, *, cancellationToken, **kwargs):
		self.texts.append(text)
		if self.failNext:
			self.failNext = False
			raise RuntimeBridgeError("workerCrash", "fixture failure")
		self.started.set()
		self.release.wait(2)
		if cancellationToken != self.token:
			raise RuntimeBridgeCancelled()
		return PcmResult(generationId, jobId, 16_000, 1, 2, b"\x01\x00")


class ControllerTests(unittest.TestCase):
	def _controller(self, bridge=None):
		bridge = bridge or FakeBridge()
		played = []
		dispatched = []
		completed = []
		indexes = []
		errors = []
		controller = BackgroundController(
			bridge,
			lambda result: played.append(result.generationId) is None or True,
			dispatched.append,
			lambda: completed.append(True),
			indexes.append,
			errors.append,
		)
		return controller, bridge, played, dispatched, completed, indexes, errors

	def test_values_are_immutable_and_thread_starts_once(self) -> None:
		request = BackgroundRequest(1, 1, (SynthesisSegment("private"),))
		with self.assertRaises(FrozenInstanceError):
			request.jobId = 2  # type: ignore[misc]
		controller, bridge, _, _, _, _, _ = self._controller()
		self.assertTrue(controller.threadAlive)
		self.assertIn(controller.state, {ControllerState.STARTING, ControllerState.READY})
		self.assertTrue(controller.shutdown())
		self.assertTrue(controller.shutdown())
		self.assertFalse(controller.threadAlive)

	def test_submit_is_prompt_and_replacement_is_bounded(self) -> None:
		controller, bridge, played, dispatched, completed, _, _ = self._controller()
		start = time.perf_counter()
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("first private fixture " * 5),)))
		self.assertLess(time.perf_counter() - start, 0.1)
		self.assertTrue(bridge.started.wait(1))
		controller.submit(BackgroundRequest(2, 2, (SynthesisSegment("newest private fixture " * 5),)))
		controller.submit(BackgroundRequest(3, 3, (SynthesisSegment("final private fixture " * 5),)))
		self.assertLessEqual(controller.pendingCount, 1)
		bridge.release.set()
		for _ in range(100):
			if played == [3]:
				break
			time.sleep(0.01)
		for callback in list(dispatched):
			callback()
		self.assertEqual([3], played)
		self.assertEqual([True], completed)
		self.assertNotIn(1, played)
		self.assertGreaterEqual(bridge.interruptCalls, 1)
		self.assertTrue(controller.shutdown())
		self.assertNotIn("text", controller.__dict__)

	def test_short_navigation_replacement_keeps_warm_worker(self) -> None:
		controller, bridge, played, dispatched, completed, _, _ = self._controller()
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("first"),)))
		self.assertTrue(bridge.started.wait(1))
		controller.submit(BackgroundRequest(2, 2, (SynthesisSegment("second"),)))
		self.assertEqual(0, bridge.interruptCalls)
		bridge.release.set()
		for _ in range(100):
			for callback in list(dispatched):
				callback()
			if played == [2]:
				break
			time.sleep(0.01)
		self.assertEqual([2], played)
		self.assertTrue(controller.shutdown())

	def test_cancel_rejects_audio_and_completion(self) -> None:
		controller, bridge, played, dispatched, completed, _, _ = self._controller()
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("private fixture"),)))
		self.assertTrue(bridge.started.wait(1))
		start = time.perf_counter()
		controller.cancel()
		self.assertLess(time.perf_counter() - start, 0.1)
		bridge.release.set()
		time.sleep(0.05)
		for callback in dispatched:
			callback()
		self.assertEqual([], played)
		self.assertEqual([], completed)
		self.assertEqual(0, controller.pendingCount)
		self.assertTrue(controller.shutdown())

	def test_completion_is_rechecked_on_main_thread_dispatch(self) -> None:
		controller, bridge, played, dispatched, completed, _, _ = self._controller()
		bridge.release.set()
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("private fixture"),)))
		for _ in range(100):
			if dispatched:
				break
			time.sleep(0.01)
		controller.cancel()
		for callback in dispatched:
			callback()
		self.assertEqual([1], played)
		self.assertEqual([], completed)
		self.assertTrue(controller.shutdown())

	def test_worker_error_returns_controller_to_ready_for_later_request(self) -> None:
		controller, bridge, played, dispatched, completed, _, errors = self._controller()
		bridge.failNext = True
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("fails"),)))
		for _ in range(100):
			for callback in list(dispatched):
				callback()
			if errors:
				break
			time.sleep(0.01)
		self.assertEqual(["workerCrash"], errors)
		self.assertEqual(ControllerState.READY, controller.state)
		bridge.release.set()
		controller.submit(BackgroundRequest(2, 2, (SynthesisSegment("recovers"),)))
		for _ in range(100):
			for callback in list(dispatched):
				callback()
			if completed:
				break
			time.sleep(0.01)
		self.assertEqual([2], played)
		self.assertEqual(ControllerState.READY, controller.state)
		self.assertTrue(controller.shutdown())

	def test_retained_runtime_loads_and_synthesizes_in_background(self) -> None:
		runtime = os.environ.get("NVDA_PIPER_RUNTIME_PYTHON")
		model = os.environ.get("NVDA_PIPER_MODEL_PATH")
		config = os.environ.get("NVDA_PIPER_CONFIG_PATH")
		if not all((runtime, model, config)):
			self.skipTest("Set explicit Phase 2J runtime/model/config paths for background integration")
		bridge = PersistentRuntimeBridge(runtime, model, config, str(WORKER_PATH))  # type: ignore[arg-type]
		played = []
		completed = threading.Event()
		controller = BackgroundController(
			bridge,
			lambda result: played.append((result.sampleRate, len(result.pcm))) is None or True,
			lambda callback: callback(),
			completed.set,
			lambda index: None,
			lambda code: self.fail(code),
		)
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("Background integration fixture."),)))
		self.assertTrue(completed.wait(30))
		self.assertEqual(1, len(played))
		self.assertGreater(played[0][0], 0)
		self.assertGreater(played[0][1], 0)
		self.assertTrue(controller.shutdown())
		self.assertIsNone(bridge.processId)

	def test_retained_runtime_reuses_worker_and_dispatches_ordered_indexes(self) -> None:
		runtime = os.environ.get("NVDA_PIPER_RUNTIME_PYTHON")
		model = os.environ.get("NVDA_PIPER_MODEL_PATH")
		config = os.environ.get("NVDA_PIPER_CONFIG_PATH")
		if not all((runtime, model, config)):
			self.skipTest("Set explicit Phase 2J runtime/model/config paths for background integration")
		bridge = PersistentRuntimeBridge(runtime, model, config, str(WORKER_PATH))  # type: ignore[arg-type]
		played: list[int] = []
		indexes: list[int] = []
		completed: list[int] = []
		controller = BackgroundController(
			bridge,
			lambda result: played.append(result.jobId) is None or True,
			lambda callback: callback(),
			lambda: completed.append(1),
			indexes.append,
			lambda code: self.fail(code),
		)
		controller.submit(BackgroundRequest(1, 1, (SynthesisSegment("one", indexesAfter=(11,)),)))
		for _ in range(300):
			if completed:
				break
			time.sleep(0.01)
		self.assertEqual([11], indexes)
		controller.submit(BackgroundRequest(2, 2, (SynthesisSegment("two", characterMode=True, indexesAfter=(22,)),)))
		for _ in range(300):
			if len(completed) == 2:
				break
			time.sleep(0.01)
		self.assertEqual([1, 2], played)
		self.assertEqual([11, 22], indexes)
		self.assertEqual(2, len(completed))
		self.assertTrue(controller.shutdown())
		self.assertIsNone(bridge.processId)


if __name__ == "__main__":
	unittest.main()
