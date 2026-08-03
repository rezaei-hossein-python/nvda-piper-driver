import unittest

from experiments.piperRuntime.audioDiagnostic import runMode


class Player:
	def __init__(self):
		self.feeds = []
		self.stops = 0

	def feed(self, pcm):
		self.feeds.append(pcm)

	def stop(self):
		self.stops += 1


class AudioDiagnosticTests(unittest.TestCase):
	def test_direct_mode_preserves_event_count(self):
		player = Player()
		events = runMode(b"\x00\x01", player, mode="direct", count=3)
		self.assertEqual(3, len(events))
		self.assertEqual(3, len(player.feeds))
		self.assertEqual(0, player.stops)

	def test_stop_mode_records_stop_and_feed(self):
		player = Player()
		events = runMode(b"\x00\x01", player, mode="stop", count=2)
		self.assertEqual(2, len(events))
		self.assertEqual(2, player.stops)
		self.assertTrue(all(event.stopNs is not None for event in events))

	def test_bounds_and_invalid_mode(self):
		with self.assertRaises(ValueError):
			runMode(b"\x00", Player(), mode="direct", count=101)
		with self.assertRaises(ValueError):
			runMode(b"\x00", Player(), mode="unknown")


if __name__ == "__main__":
	unittest.main()
