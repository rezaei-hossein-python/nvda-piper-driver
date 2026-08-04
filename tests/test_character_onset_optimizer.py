from __future__ import annotations

import unittest

from experiments.piperRuntime.characterOnsetOptimizer import (
	ACTIVATION_ENV,
	analyze,
	cacheIdentity,
	enabled,
	optimize,
)


def _signal(prefix: int = 200, body: int = 500) -> bytes:
	return b"\0\0" * prefix + b"\x00\x10" * body


class CharacterOnsetOptimizerTests(unittest.TestCase):
	def test_activation_is_opt_in(self) -> None:
		self.assertFalse(enabled({}))
		self.assertTrue(enabled({ACTIVATION_ENV: "1"}))

	def test_analysis_detects_sustained_energy(self) -> None:
		result = analyze(_signal(), 16_000)
		self.assertGreater(result.leadingFrames, 0)
		self.assertFalse(result.clipping)

	def test_current_policy_is_byte_identical(self) -> None:
		pcm = _signal()
		result = optimize(pcm, 16_000, policy="current")
		self.assertEqual(result.pcm, pcm)
		self.assertTrue(result.fallback)

	def test_adaptive_policy_reduces_onset_without_empty_output(self) -> None:
		pcm = _signal()
		result = optimize(pcm, 16_000, policy="adaptive")
		self.assertFalse(result.fallback)
		self.assertLess(result.outputFrames, result.originalFrames)
		self.assertGreater(result.outputFrames, 0)
		self.assertEqual(len(result.pcm) % 2, 0)

	def test_all_policies_are_deterministic_and_isolated(self) -> None:
		pcm = _signal()
		for policy in ("preserve40ms", "preserve25ms", "preserve15ms", "adaptive"):
			self.assertEqual(optimize(pcm, 16_000, policy=policy).pcm, optimize(pcm, 16_000, policy=policy).pcm)
		self.assertNotEqual(cacheIdentity("voice", "adaptive"), cacheIdentity("voice", "current"))

	def test_invalid_policy_rejected(self) -> None:
		with self.assertRaises(ValueError):
			optimize(_signal(), 16_000, policy="unknown")


if __name__ == "__main__":
	unittest.main()
