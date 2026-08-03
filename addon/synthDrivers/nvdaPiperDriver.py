# NVDA Piper Driver
# Copyright (C) 2026 Hosein Rezaei
# This file is covered by the GNU General Public License v2 or later.
# See LICENSE for details.

from collections import OrderedDict
from enum import Enum
import os
from pathlib import Path
import threading
import time

import config
from logHandler import log
import nvwave
import queueHandler
import synthDriverHandler

try:
	from speech.commands import CharacterModeCommand, IndexCommand
except ImportError:  # pragma: no cover - isolated source tests provide no NVDA speech package.
	CharacterModeCommand = None
	IndexCommand = None

from synthDrivers._nvdaPiperDriver.backgroundController import BackgroundController, BackgroundRequest, SynthesisSegment
from synthDrivers._nvdaPiperDriver.conversion import SpeechJobConverter
try:
	from synthDrivers._nvdaPiperDriver.conversion import UnsupportedSpeechItemError
except ImportError:  # pragma: no cover - isolated source tests provide a narrow converter stub.
	class UnsupportedSpeechItemError(Exception):
		pass
from synthDrivers._nvdaPiperDriver.jobs import (
	BreakItem,
	CharacterModeItem,
	IndexItem,
	LanguageChangeItem,
	ProsodyItem,
	SpeechJob,
	TextItem,
)
from synthDrivers._nvdaPiperDriver.runtimeBridge import PersistentRuntimeBridge, readModelLanguage, validateRuntimePaths
from synthDrivers._nvdaPiperDriver.latencyMetrics import LatencyRecorder, LatencyTrace

_TEST_ONLY_MARKER_ENV = "NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME"
_TEST_ONLY_MARKER_VALUE = "phase-2c-explicit-local-mock-runtime-6f4d1c8a"
_RUNTIME_PATH_ENV = "NVDA_PIPER_RUNTIME_PYTHON"
_MODEL_PATH_ENV = "NVDA_PIPER_MODEL_PATH"
_CONFIG_PATH_ENV = "NVDA_PIPER_CONFIG_PATH"
_LATENCY_TRACE_ENV = "NVDA_PIPER_LATENCY_TRACE"
_MOCK_VOICE_ID = "configuredModel"
_DEFAULT_RATE = 50


class _SpeechExtractionError(RuntimeError):
	"""A fixed, content-free rejection at the Phase 2J extraction boundary."""

	def __init__(self, code: str, message: str) -> None:
		self.code = code
		super().__init__(message)


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
	"""Development-only Phase 2J bounded-background Piper driver."""

	name = "nvdaPiperDriver"
	description = "NVDA Piper Driver"
	supportedSettings = (
		synthDriverHandler.SynthDriver.VoiceSetting(),
		synthDriverHandler.SynthDriver.RateSetting(),
	)
	supportedCommands = frozenset({CharacterModeCommand}) if CharacterModeCommand is not None else frozenset()
	supportedNotifications = {synthDriverHandler.synthDoneSpeaking, synthDriverHandler.synthIndexReached}

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
		self._runtimeBridge = PersistentRuntimeBridge(
			os.environ[_RUNTIME_PATH_ENV],
			os.environ[_MODEL_PATH_ENV],
			os.environ[_CONFIG_PATH_ENV],
			str(workerPath),
		)
		self._player: nvwave.WavePlayer | None = None
		self._audioLock = threading.Lock()
		self._speechRejectionReported = False
		self._latencyRecorder = LatencyRecorder()
		super().__init__()
		self._controller = BackgroundController(
			self._runtimeBridge,
			self._playResult,
			lambda callback: queueHandler.queueFunction(queueHandler.eventQueue, callback),
			lambda: synthDriverHandler.synthDoneSpeaking.notify(synth=self),
			lambda index: synthDriverHandler.synthIndexReached.notify(synth=self, index=index),
			self._reportBackgroundError,
		)
		self._state = _MockLifecycleState.READY

	def _reportBackgroundError(self, code: str) -> None:
		log.error("NVDA Piper background runtime failure: %s", code)

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
	def _buildSegments(job: SpeechJob) -> tuple[SynthesisSegment, ...]:
		"""Build immutable audio segments while retaining real index boundaries."""
		segments: list[SynthesisSegment] = []
		parts: list[str] = []
		characterMode = False

		def flush() -> None:
			if parts:
				segments.append(SynthesisSegment("".join(parts), characterMode))
				parts.clear()

		for item in job.items:
			if type(item) is TextItem:
				parts.append(item.text)
			elif type(item) is BreakItem:
				# Piper has no NVDA break primitive. Keep the speech request valid;
				# NVDA still owns utterance and index ordering.
				continue
			elif type(item) is ProsodyItem:
				# The configured Piper model has no per-utterance prosody adapter yet.
				# Do not reject otherwise valid NVDA speech metadata.
				continue
			elif type(item) is CharacterModeItem:
				if item.state is not characterMode:
					flush()
					characterMode = item.state
			elif type(item) is IndexItem:
				flush()
				if segments:
					previous = segments[-1]
					segments[-1] = SynthesisSegment(previous.text, previous.characterMode, previous.indexesAfter + (item.index,))
				else:
					segments.append(SynthesisSegment("", False, (item.index,)))
			elif type(item) is LanguageChangeItem:
				# NVDA metadata is tolerated; this single explicitly selected model
				# does not infer languages or switch voices.
				continue
			else:
				raise _SpeechExtractionError("unsupportedItem", "Phase 2J speech item is unsupported")
		flush()
		if not any(segment.text for segment in segments):
			raise _SpeechExtractionError("emptySpeech", "Phase 2J speech is empty")
		return tuple(segments)

	@classmethod
	def _extractText(cls, job: SpeechJob) -> str:
		"""Compatibility helper returning text without metadata separators."""
		return "".join(segment.text for segment in cls._buildSegments(job))

	def terminate(self) -> None:
		"""Stop audio and the child before NVDA unregisters this driver."""
		if self._state is _MockLifecycleState.TERMINATED:
			return
		try:
			self.cancel()
			if not self._controller.shutdown():
				self._reportBackgroundError("shutdownTimeout")
			with self._audioLock:
				if self._player is not None:
					self._player.close()
					self._player = None
			super().terminate()
		finally:
			self._state = _MockLifecycleState.TERMINATED

	def speak(self, speechSequence) -> None:
		"""Submit one bounded utterance without waiting for runtime or playback."""
		self._requireReady()
		entryNs = time.monotonic_ns()
		try:
			job = self._createSpeechJob(speechSequence)
			segments = self._buildSegments(job)
		except (_SpeechExtractionError, UnsupportedSpeechItemError, TypeError, ValueError) as error:
			# NVDA does not wrap SynthDriver.speak exceptions. Reject locally so
			# an unsupported command cannot leak event arguments through an NVDA
			# traceback or flood the log during consecutive character events.
			if not self._speechRejectionReported:
				log.warning("NVDA Piper speech request rejected: %s", getattr(error, "code", "unsupportedItem"))
				self._speechRejectionReported = True
			self._completeRejectedIndexes(speechSequence)
			return
		self._speechRejectionReported = False
		trace = LatencyTrace(job.jobId, job.generationId)
		trace.mark("speakEntry", entryNs)
		if getattr(self._controller, "active", False):
			with self._audioLock:
				if self._player is not None:
					self._player.stop()
		self._controller.submit(BackgroundRequest(job.generationId, job.jobId, segments, trace))
		trace.mark("speakReturn")

	def _completeRejectedIndexes(self, speechSequence: object) -> None:
		"""Consume real NVDA indexes when a request is rejected before submission."""
		if IndexCommand is None or type(speechSequence) is not list:
			return
		for item in speechSequence:
			if type(item) is IndexCommand:
				synthDriverHandler.synthIndexReached.notify(synth=self, index=item.index)

	def _playResult(self, result) -> bool:
		"""Validate currency while feeding bounded chunks on the controller thread."""
		if not self._controller.isCurrent(result.generationId):
			return False
		with self._audioLock:
			if not self._controller.isCurrent(result.generationId):
				return False
			if self._player is None or self._player.samplesPerSec != result.sampleRate:
				if self._player is not None:
					self._player.close()
				self._player = nvwave.WavePlayer(
					channels=result.channels,
					samplesPerSec=result.sampleRate,
					bitsPerSample=result.sampleWidth * 8,
					outputDevice=config.conf["audio"]["outputDevice"],
				)
			player = self._player
		# Fifty milliseconds of mono 16-bit PCM bounds each blocking feed call.
		chunkBytes = max(2, result.sampleRate // 20 * result.channels * result.sampleWidth)
		for offset in range(0, len(result.pcm), chunkBytes):
			with self._audioLock:
				if not self._controller.isCurrent(result.generationId):
					return False
				if offset == 0:
					# The first feed is the closest available objective proxy for
					# device playback onset in the NVDA audio API.
					trace = getattr(result, "latencyTrace", None)
					if trace is not None:
						trace.mark("firstWavePlayerFeed")
				player.feed(result.pcm[offset : offset + chunkBytes])
		player.idle()
		current = self._controller.isCurrent(result.generationId)
		trace = getattr(result, "latencyTrace", None)
		if trace is not None:
			trace.mark("playbackDrainComplete")
			self._latencyRecorder.record(trace)
			if os.environ.get(_LATENCY_TRACE_ENV) == "1":
				debug = getattr(log, "debug", None)
				if debug is not None:
					debug(
						"NVDA Piper latency request=%d generation=%d timestamps=%s",
						trace.requestId,
						trace.generationId,
						trace.snapshot(),
					)
		return current

	def cancel(self) -> None:
		"""Stop local playback and invalidate active synthesis."""
		if self._state is _MockLifecycleState.TERMINATED:
			return
		self._controller.cancel()
		with self._audioLock:
			if self._player is not None:
				self._player.stop()
