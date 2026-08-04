from __future__ import annotations

import unittest

from experiments.piperRuntime.wasapiLoopbackCapture import (
	ACTIVATION_ENV,
	_firstNonSilent,
	_tone,
	enabled,
	_firstMarkerFrame,
	_resampleMono16ToStereo48,
)


class WasapiLoopbackCaptureTests(unittest.TestCase):
	def test_capture_requires_explicit_activation(self) -> None:
		self.assertFalse(enabled({}))
		self.assertTrue(enabled({ACTIVATION_ENV: "1"}))

	def test_marker_is_deterministic_and_has_immediate_energy(self) -> None:
		self.assertEqual(_tone(), _tone())
		self.assertEqual(_firstNonSilent(_tone()), 0)

	def test_silence_has_no_detected_onset(self) -> None:
		self.assertIsNone(_firstNonSilent(b"\0\0" * 480))

	def test_marker_requires_sustained_energy_above_baseline(self) -> None:
		self.assertIsNotNone(_firstMarkerFrame(_tone(), b"\0\0" * 480))

	def test_fixed_format_conversion_is_aligned(self) -> None:
		converted = _resampleMono16ToStereo48(b"\0\0" * 16, 16_000)
		self.assertEqual(len(converted) % 4, 0)
		self.assertGreater(len(converted), 0)


if __name__ == "__main__":
	unittest.main()
