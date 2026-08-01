# NVDA Piper Driver
# Copyright (C) 2026 Hosein Rezaei
# This file is covered by the GNU General Public License v2 or later.
# See LICENSE for details.

from collections import OrderedDict
from enum import Enum
import os

import synthDriverHandler


_TEST_ONLY_MARKER_ENV = "NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME"
_TEST_ONLY_MARKER_VALUE = "phase-2c-explicit-local-mock-runtime-6f4d1c8a"
_MOCK_VOICE_ID = "mockVoice"
_DEFAULT_RATE = 50


class _MockLifecycleState(Enum):
	INITIALIZING = "initializing"
	READY = "ready"
	TERMINATED = "terminated"


def _isMockRuntimeAvailable() -> bool:
	"""Return whether the exact, process-local Phase 2C test marker is enabled."""
	return os.environ.get(_TEST_ONLY_MARKER_ENV) == _TEST_ONLY_MARKER_VALUE


class SynthDriver(synthDriverHandler.SynthDriver):
	"""Test-only Phase 2D lifecycle and settings integration fixture."""

	name = "nvdaPiperDriver"
	description = "NVDA Piper Driver"
	supportedSettings = (
		synthDriverHandler.SynthDriver.VoiceSetting(),
		synthDriverHandler.SynthDriver.RateSetting(),
	)

	@classmethod
	def check(cls) -> bool:
		"""Expose the driver only under the exact development-test condition."""
		return _isMockRuntimeAvailable()

	def __init__(self) -> None:
		if not _isMockRuntimeAvailable():
			raise RuntimeError("The NVDA Piper Driver test availability marker is not enabled")
		self._state = _MockLifecycleState.INITIALIZING
		self._voice = _MOCK_VOICE_ID
		self._rate = _DEFAULT_RATE
		super().__init__()
		self._state = _MockLifecycleState.READY

	def _requireReady(self) -> None:
		if self._state is _MockLifecycleState.TERMINATED:
			raise RuntimeError("NVDA Piper Driver is terminated")
		if self._state is not _MockLifecycleState.READY:
			raise RuntimeError("NVDA Piper Driver is not ready")

	def _getAvailableVoices(self) -> OrderedDict[str, synthDriverHandler.VoiceInfo]:
		return OrderedDict(
			((_MOCK_VOICE_ID, synthDriverHandler.VoiceInfo(_MOCK_VOICE_ID, "Mock Voice — No Speech", None)),),
		)

	def _get_voice(self) -> str:
		self._requireReady()
		return self._voice

	def _set_voice(self, value: str) -> None:
		self._requireReady()
		if value != _MOCK_VOICE_ID:
			raise LookupError(value)
		self._voice = value

	def _get_rate(self) -> int:
		self._requireReady()
		return self._rate

	def _set_rate(self, value: int) -> None:
		self._requireReady()
		if type(value) is not int:
			raise TypeError("rate must be an integer")
		if not 0 <= value <= 100:
			raise ValueError("rate must be between 0 and 100")
		self._rate = value

	def terminate(self) -> None:
		"""Run NVDA's base cleanup at most once; this fixture owns no runtime resources."""
		if self._state is _MockLifecycleState.TERMINATED:
			return
		try:
			super().terminate()
		finally:
			self._state = _MockLifecycleState.TERMINATED

	def speak(self, speechSequence) -> None:
		"""Reject speech without inspecting its content or changing lifecycle state."""
		if self._state is _MockLifecycleState.TERMINATED:
			raise RuntimeError("NVDA Piper Driver is terminated")
		raise RuntimeError("Phase 2D has no speech implementation")
