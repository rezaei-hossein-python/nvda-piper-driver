from __future__ import annotations

import unittest

from experiments.piperRuntime.cacheHitOnsetDiagnostic import (
	ACTIVATION_ENV,
	RecordingPlayer,
	diagnosticEnabled,
	makeImpulse,
	runTrials,
	summarize,
	validatePcm,
)


class CacheHitOnsetDiagnosticTests(unittest.TestCase):
	def test_activation_is_explicit(self) -> None:
		self.assertFalse(diagnosticEnabled({}))
		self.assertTrue(diagnosticEnabled({ACTIVATION_ENV: "1"}))
		self.assertFalse(diagnosticEnabled({ACTIVATION_ENV: "true"}))

	def test_deterministic_signal_and_validation(self) -> None:
		first, second = makeImpulse(), makeImpulse()
		self.assertEqual(first.pcm, second.pcm)
		self.assertGreater(first.frames, 0)
		validatePcm(first.pcm, sampleRate=first.sampleRate)
		with self.assertRaises(ValueError):
			validatePcm(b"", sampleRate=first.sampleRate)

	def test_stop_and_direct_paths_have_distinct_events(self) -> None:
		signal = makeImpulse()
		player = RecordingPlayer()
		direct = runTrials(signal, player, path="direct", count=10)
		self.assertEqual([event.eventId for event in direct], list(range(1, 11)))
		self.assertTrue(all(event.terminalState == "fed" for event in direct))
		stopped = runTrials(signal, player, path="stop", count=4)
		self.assertEqual(player.stopCount, 4)
		self.assertTrue(all(event.stopEntryNs is not None for event in stopped))

	def test_capture_is_explicitly_unknown_and_content_free_summary(self) -> None:
		signal = makeImpulse()
		events = runTrials(signal, RecordingPlayer(), path="direct", count=3)
		payload = summarize(events)
		self.assertEqual(payload["failures"], 0)
		self.assertEqual(payload["firstCapturedSampleMs"], "unknown")
		self.assertNotIn("speech", str(payload).lower())
		self.assertNotIn("character", str(payload).lower())

	def test_arbitrary_fixture_path_is_not_part_of_api(self) -> None:
		with self.assertRaises(ValueError):
			runTrials(makeImpulse(), RecordingPlayer(), path="arbitrary", count=1)


if __name__ == "__main__":
	unittest.main()
