# NVDA Piper Driver
# Copyright (C) 2026 Hosein Rezaei
# This file is covered by the GNU General Public License v2 or later.
# See LICENSE for details.

import os

import synthDriverHandler


_TEST_ONLY_MARKER_ENV = "NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME"
_TEST_ONLY_MARKER_VALUE = "phase-2c-explicit-local-mock-runtime-6f4d1c8a"


def _isMockRuntimeAvailable() -> bool:
	"""Return whether the exact, process-local Phase 2C test marker is enabled."""
	return os.environ.get(_TEST_ONLY_MARKER_ENV) == _TEST_ONLY_MARKER_VALUE


class SynthDriver(synthDriverHandler.SynthDriver):
	"""Test-only Phase 2C synthesizer integration fixture."""

	name = "nvdaPiperDriver"
	description = "NVDA Piper Driver"

	@classmethod
	def check(cls) -> bool:
		"""Expose the driver only under the exact Phase 2C test condition."""
		return _isMockRuntimeAvailable()

	def __init__(self) -> None:
		if not _isMockRuntimeAvailable():
			raise RuntimeError("The NVDA Piper Driver test availability marker is not enabled")
		super().__init__()
		self._isTerminated = False

	def terminate(self) -> None:
		"""Run NVDA's base cleanup at most once; this fixture owns no runtime resources."""
		if self._isTerminated:
			return
		self._isTerminated = True
		super().terminate()

	def speak(self, speechSequence) -> None:
		"""Reject an unexpected call because this test fixture cannot synthesize."""
		raise RuntimeError("The test-only NVDA Piper Driver cannot speak")
