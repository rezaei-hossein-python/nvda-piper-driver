"""Bounded background ownership for the development Piper runtime bridge."""

from __future__ import annotations

from collections.abc import Callable
from collections import deque
from dataclasses import dataclass, field, replace
from enum import Enum
import threading
from typing import Final

from .runtimeBridge import PcmResult, RuntimeBridgeCancelled, RuntimeBridgeError
from .latencyMetrics import LatencyTrace


CONTROLLER_JOIN_TIMEOUT_SECONDS: Final = 3
CONTROLLER_FORCED_JOIN_TIMEOUT_SECONDS: Final = 2
SHORT_REQUEST_CODE_POINTS: Final = 64
CHARACTER_QUEUE_LIMIT: Final = 8


class ControllerState(Enum):
	STARTING = "starting"
	READY = "ready"
	ACTIVE = "active"
	FAILED = "failed"
	STOPPING = "stopping"
	STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class SynthesisSegment:
	text: str = field(repr=False)
	characterMode: bool = False
	indexesAfter: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class BackgroundRequest:
	generationId: int
	jobId: int
	segments: tuple[SynthesisSegment, ...]
	trace: LatencyTrace | None = field(default=None, repr=False, compare=False)
	category: str = "ordered"

	@property
	def text(self) -> str:
		return "".join(segment.text for segment in self.segments)


class BackgroundController:
	"""Run at most one request plus one replaceable pending request."""

	def __init__(
		self,
		bridge,
		playResult: Callable[[PcmResult], bool],
		dispatch: Callable[[Callable[[], None]], None],
		onComplete: Callable[[], None],
		onIndex: Callable[[int], None],
		onError: Callable[[str], None],
		cacheGet: Callable[[SynthesisSegment, int], PcmResult | None] | None = None,
		cachePut: Callable[[SynthesisSegment, PcmResult], None] | None = None,
	) -> None:
		self._bridge = bridge
		self._playResult = playResult
		self._dispatch = dispatch
		self._onComplete = onComplete
		self._onIndex = onIndex
		self._onError = onError
		self._cacheGet = cacheGet
		self._cachePut = cachePut
		self._condition = threading.Condition()
		self._pending: BackgroundRequest | None = None
		self._characterPending: deque[BackgroundRequest] = deque()
		self._droppedCharacters = 0
		self._activeGeneration: int | None = None
		self._activeRequestCategory: str | None = None
		self._currentRequestCategory: str | None = None
		self._activeShortRequest = False
		self._currentGeneration: int | None = None
		self._stopping = False
		self._state = ControllerState.STARTING
		self._lastErrorCode: str | None = None
		self._thread = threading.Thread(target=self._run, name="nvdaPiperBackground", daemon=False)
		self._thread.start()

	@property
	def state(self) -> ControllerState:
		with self._condition:
			return self._state

	@property
	def threadAlive(self) -> bool:
		return self._thread.is_alive()

	@property
	def pendingCount(self) -> int:
		with self._condition:
			return int(self._pending is not None) + len(self._characterPending)

	@property
	def droppedCharacters(self) -> int:
		with self._condition:
			return self._droppedCharacters

	@property
	def active(self) -> bool:
		with self._condition:
			return self._activeGeneration is not None

	@property
	def lastErrorCode(self) -> str | None:
		with self._condition:
			return self._lastErrorCode

	def isCurrent(self, generationId: int) -> bool:
		with self._condition:
			if self._stopping:
				return False
			if self._currentGeneration is not None and self._currentRequestCategory == "character" and self._activeRequestCategory == "character" and self._activeGeneration == generationId:
				return True
			return self._currentGeneration == generationId

	def submit(self, request: BackgroundRequest) -> None:
		if type(request) is not BackgroundRequest:
			raise TypeError("request must be an immutable BackgroundRequest")
		with self._condition:
			if self._stopping:
				raise RuntimeError("background controller is stopping")
			isCharacter = request.category == "character"
			interrupt = (
				self._activeGeneration is not None
				and self._activeGeneration != request.generationId
				and not isCharacter
				and (request.category == "navigation" or not self._activeShortRequest)
			)
			self._currentGeneration = request.generationId
			self._currentRequestCategory = request.category
			if request.trace is not None:
				request.trace.mark("controllerSubmit")
			if isCharacter:
				if len(self._characterPending) >= CHARACTER_QUEUE_LIMIT:
					self._droppedCharacters += 1
				else:
					self._characterPending.append(request)
			else:
				self._characterPending.clear()
				self._pending = request
			self._condition.notify()
		if interrupt:
			self._bridge.interrupt()

	def cancel(self) -> None:
		with self._condition:
			self._currentGeneration = None
			self._currentRequestCategory = None
			self._pending = None
			self._characterPending.clear()
			interrupt = self._activeGeneration is not None
			self._condition.notify()
		if interrupt:
			self._bridge.interrupt()

	def shutdown(self) -> bool:
		with self._condition:
			if self._state is ControllerState.STOPPED:
				return True
			self._stopping = True
			self._state = ControllerState.STOPPING
			self._currentGeneration = None
			self._currentRequestCategory = None
			self._pending = None
			self._characterPending.clear()
			self._condition.notify()
		self._bridge.interrupt()
		self._thread.join(CONTROLLER_JOIN_TIMEOUT_SECONDS)
		if self._thread.is_alive():
			self._bridge.forceStop()
			self._thread.join(CONTROLLER_FORCED_JOIN_TIMEOUT_SECONDS)
		self._bridge.stop()
		return not self._thread.is_alive()

	def _isRequestCurrent(self, request: BackgroundRequest) -> bool:
		return self.isCurrent(request.generationId)

	def _deliverCompletion(self, generationId: int) -> None:
		if self.isCurrent(generationId):
			self._onComplete()

	def _deliverIndex(self, generationId: int, index: int) -> None:
		if self.isCurrent(generationId):
			self._onIndex(index)

	def _reportError(self, code: str) -> None:
		with self._condition:
			self._lastErrorCode = code
			self._state = ControllerState.FAILED
		try:
			self._dispatch(lambda: self._onError(code))
		except Exception:
			# Dispatch failure is already represented by FAILED; never let it orphan the thread.
			pass

	def _run(self) -> None:
		with self._condition:
			self._state = ControllerState.READY
		while True:
			with self._condition:
				while self._pending is None and not self._stopping:
					if self._characterPending:
						break
					self._condition.wait()
				if self._stopping:
					break
				request = self._pending
				if request is not None:
					self._pending = None
				elif self._characterPending:
					request = self._characterPending.popleft()
				else:
					continue
				self._activeGeneration = request.generationId
				self._activeRequestCategory = request.category
				self._activeShortRequest = (
					len(request.segments) == 1
					and len(request.segments[0].text) <= SHORT_REQUEST_CODE_POINTS
				)
				self._state = ControllerState.ACTIVE
			try:
				if request.trace is not None:
					request.trace.mark("controllerStart")
				if not self._isRequestCurrent(request):
					continue
				if not request.segments:
					self._dispatch(lambda generationId=request.generationId: self._deliverCompletion(generationId))
					continue
				token = self._bridge.cancellationToken
				for segmentNumber, segment in enumerate(request.segments, 1):
					if not self._isRequestCurrent(request):
						break
					if segment.text:
						result = self._cacheGet(segment, request.generationId) if self._cacheGet is not None else None
						if result is None:
							result = self._bridge.synthesize(
								segment.text,
								request.generationId,
								request.jobId,
								cancellationToken=token,
								characterMode=segment.characterMode,
								indexesAfter=segment.indexesAfter,
								segmentNumber=segmentNumber,
							)
							if self._cachePut is not None and self._isRequestCurrent(request):
								self._cachePut(segment, result)
						if request.trace is not None:
							request.trace.mark("firstPcmReceived")
							result = replace(result, latencyTrace=request.trace)
						if not self._isRequestCurrent(request) or not self._playResult(result):
							break
					for index in segment.indexesAfter:
						self._dispatch(lambda index=index, generationId=request.generationId: self._deliverIndex(generationId, index))
				if self._isRequestCurrent(request):
					self._dispatch(lambda generationId=request.generationId: self._deliverCompletion(generationId))
			except RuntimeBridgeCancelled:
				pass
			except RuntimeBridgeError as error:
				if self._isRequestCurrent(request):
					self._reportError(error.code)
			except Exception:
				if self._isRequestCurrent(request):
					self._reportError("internalControllerError")
			finally:
				request = None
				result = None
				with self._condition:
					self._activeGeneration = None
					self._activeRequestCategory = None
					self._activeShortRequest = False
					if not self._stopping:
						self._state = ControllerState.READY
		with self._condition:
			self._activeGeneration = None
			self._activeRequestCategory = None
			self._activeShortRequest = False
			self._pending = None
			self._characterPending.clear()
			self._state = ControllerState.STOPPED
