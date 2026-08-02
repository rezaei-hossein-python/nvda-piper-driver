# NVDA Piper Driver
# Copyright (C) 2026 Hosein Rezaei
# This file is covered by the GNU General Public License v2 or later.
# See LICENSE for details.

from collections import OrderedDict
from enum import Enum
import os
from pathlib import Path

import config
import nvwave
import synthDriverHandler

from synthDrivers._nvdaPiperDriver.conversion import SpeechJobConverter
from synthDrivers._nvdaPiperDriver.jobs import LanguageChangeItem, PhonemeItem, SpeechJob, TextItem
from synthDrivers._nvdaPiperDriver.runtimeBridge import OneShotRuntimeBridge, readModelLanguage, validateRuntimePaths


_TEST_ONLY_MARKER_ENV = "NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME"
_TEST_ONLY_MARKER_VALUE = "phase-2c-explicit-local-mock-runtime-6f4d1c8a"
_RUNTIME_PATH_ENV = "NVDA_PIPER_RUNTIME_PYTHON"
_MODEL_PATH_ENV = "NVDA_PIPER_MODEL_PATH"
_CONFIG_PATH_ENV = "NVDA_PIPER_CONFIG_PATH"
_MOCK_VOICE_ID = "configuredModel"
_DEFAULT_RATE = 50


class _MockLifecycleState(Enum):
	INITIALIZING = "initializing"
	READY = "ready"
	TERMINATED = "terminated"


def _isMockRuntimeAvailable() -> bool:
	"""Return whether the exact, process-local Phase 2C test marker is enabled."""
	if os.environ.get(_TEST_ONLY_MARKER_ENV) != _TEST_ONLY_MARKER_VALUE:
		return False
	try:
		_, _, configPath = validateRuntimePaths(
			os.environ.get(_RUNTIME_PATH_ENV),
			os.environ.get(_MODEL_PATH_ENV),
			os.environ.get(_CONFIG_PATH_ENV),
		)
		readModelLanguage(configPath)
	except Exception:
		return False
	return True


class SynthDriver(synthDriverHandler.SynthDriver):
	"""Development-only Phase 2I one-utterance Piper driver."""

	name = "nvdaPiperDriver"
	description = "NVDA Piper Driver"
	supportedSettings = (
		synthDriverHandler.SynthDriver.VoiceSetting(),
		synthDriverHandler.SynthDriver.RateSetting(),
	)
	supportedNotifications = {synthDriverHandler.synthDoneSpeaking}

	@classmethod
	def check(cls) -> bool:
		"""Expose the driver only under the exact development-test condition."""
		return _isMockRuntimeAvailable()

	def __init__(self) -> None:
		if not _isMockRuntimeAvailable():
			raise RuntimeError("The NVDA Piper Driver test availability marker is not enabled")
		self._state = _MockLifecycleState.INITIALIZING
		self._voice = _MOCK_VOICE_ID
		self._language = readModelLanguage(os.environ[_CONFIG_PATH_ENV])
		self._rate = _DEFAULT_RATE
		self._jobConverter = SpeechJobConverter()
		workerPath = Path(__file__).with_name("_nvdaPiperDriver") / "runtimeWorker.py"
		self._runtimeBridge = OneShotRuntimeBridge(
			os.environ[_RUNTIME_PATH_ENV],
			os.environ[_MODEL_PATH_ENV],
			os.environ[_CONFIG_PATH_ENV],
			str(workerPath),
		)
		self._player: nvwave.WavePlayer | None = None
		self._activeGeneration: int | None = None
		super().__init__()
		self._state = _MockLifecycleState.READY

	def _requireReady(self) -> None:
		if self._state is _MockLifecycleState.TERMINATED:
			raise RuntimeError("NVDA Piper Driver is terminated")
		if self._state is not _MockLifecycleState.READY:
			raise RuntimeError("NVDA Piper Driver is not ready")

	def _getAvailableVoices(self) -> OrderedDict[str, synthDriverHandler.VoiceInfo]:
		return OrderedDict(
			((_MOCK_VOICE_ID, synthDriverHandler.VoiceInfo(_MOCK_VOICE_ID, "Configured Piper model", self._language)),),
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

	def _createSpeechJob(self, speechSequence: list[object]) -> SpeechJob:
		"""Convert one sequence without retaining it or submitting it for execution."""
		self._requireReady()
		voiceId = self.voice
		if voiceId not in self.availableVoices:
			raise LookupError("active voice ID is invalid")
		return self._jobConverter.convert(speechSequence, voiceId=voiceId, rate=self.rate)

	@staticmethod
	def _extractText(job: SpeechJob) -> str:
		"""Accept only the narrow Phase 2I job subset without retaining content."""
		parts: list[str] = []
		for item in job.items:
			if type(item) is TextItem:
				parts.append(item.text)
			elif type(item) is LanguageChangeItem:
				# Language metadata is already model-driven; Phase 2I does not switch models mid-job.
				continue
			elif type(item) is PhonemeItem and item.fallbackText is not None:
				parts.append(item.fallbackText)
			else:
				raise RuntimeError("Phase 2I speech item is unsupported")
		return "".join(parts)

	def terminate(self) -> None:
		"""Stop audio and the child before NVDA unregisters this driver."""
		if self._state is _MockLifecycleState.TERMINATED:
			return
		try:
			self.cancel()
			if self._player is not None:
				self._player.close()
				self._player = None
			super().terminate()
		finally:
			self._state = _MockLifecycleState.TERMINATED

	def speak(self, speechSequence) -> None:
		"""Synchronously synthesize and play one bounded development utterance."""
		self._requireReady()
		job = self._createSpeechJob(speechSequence)
		text = self._extractText(job)
		if not text:
			synthDriverHandler.synthDoneSpeaking.notify(synth=self)
			return
		if self._player is not None:
			self._player.stop()
		self._activeGeneration = job.generationId
		result = self._runtimeBridge.synthesize(text, job.generationId, job.jobId)
		if self._activeGeneration != result.generationId or self._state is not _MockLifecycleState.READY:
			return
		if self._player is None or self._player.samplesPerSec != result.sampleRate:
			if self._player is not None:
				self._player.close()
			self._player = nvwave.WavePlayer(
				channels=result.channels,
				samplesPerSec=result.sampleRate,
				bitsPerSample=result.sampleWidth * 8,
				outputDevice=config.conf["audio"]["outputDevice"],
			)
		self._player.feed(result.pcm)
		self._player.idle()
		if self._activeGeneration == result.generationId and self._state is _MockLifecycleState.READY:
			synthDriverHandler.synthDoneSpeaking.notify(synth=self)

	def cancel(self) -> None:
		"""Perform safe teardown only; active inference cancellation is not claimed."""
		if self._state is _MockLifecycleState.TERMINATED:
			return
		self._activeGeneration = None
		if self._player is not None:
			self._player.stop()
		self._runtimeBridge.stop()
