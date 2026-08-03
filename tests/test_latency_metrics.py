"""Content-free latency trace tests."""

import unittest

from addon.synthDrivers._nvdaPiperDriver.latencyMetrics import LatencyRecorder, LatencyTrace


class LatencyMetricsTests(unittest.TestCase):
	def test_trace_is_monotonic_and_content_free(self) -> None:
		trace = LatencyTrace(7, 11)
		trace.mark("speakEntry", 100)
		trace.mark("firstPcmReceived", 200)
		trace.mark("firstWavePlayerFeed", 300)
		recorder = LatencyRecorder()
		recorder.record(trace)
		record = recorder.snapshot()[0]
		self.assertEqual({"requestId", "generationId", "timestamps"}, set(record))
		self.assertEqual({"speakEntry", "firstPcmReceived", "firstWavePlayerFeed"}, set(record["timestamps"]))
		self.assertNotIn("text", repr(record).lower())

	def test_trace_rejects_backwards_timestamp(self) -> None:
		trace = LatencyTrace(1, 1)
		trace.mark("event", 20)
		with self.assertRaises(ValueError):
			trace.mark("event", 19)

	def test_recorder_is_bounded(self) -> None:
		recorder = LatencyRecorder()
		for index in range(200):
			recorder.record(LatencyTrace(index, index))
		self.assertEqual(128, len(recorder.snapshot()))


if __name__ == "__main__":
	unittest.main()
