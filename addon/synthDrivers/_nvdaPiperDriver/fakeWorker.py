"""Deterministic synchronous Phase 2G fake-worker state machine."""

from .protocol import (
	MAX_CANCELLED_GENERATIONS,
	MAX_TRACKED_GENERATIONS,
	MAX_TRACKED_JOBS,
	MAX_TRACKED_REQUESTS,
	MAX_TRACKED_RESULTS,
	Capabilities,
	CancelGenerationRequest,
	CancelGenerationResponse,
	Envelope,
	ErrorCode,
	ErrorResponse,
	FakeResultRequest,
	FakeResultResponse,
	FakeResultStatus,
	HelloRequest,
	HelloResponse,
	JobAcceptedResponse,
	MessageType,
	PROTOCOL_VERSION,
	ProtocolError,
	ShutdownRequest,
	ShutdownResponse,
	SubmitJobRequest,
	decodeMessage,
	encodeMessage,
)


class FakeWorker:
	"""Validate encoded requests in-process without transport or synthesis."""

	def __init__(self) -> None:
		self._sessionId: int | None = None
		self._nextSequenceNumber = 1
		self._acceptedRequestIds: set[int] = set()
		self._activeGenerationId: int | None = None
		self._trackedGenerations: set[int] = set()
		self._acceptedJobs: dict[int, int] = {}
		self._acceptedResults: set[tuple[int, int]] = set()
		self._cancelledGenerations: set[int] = set()
		self._isShutDown = False
		self.capabilities = Capabilities()

	def _responseEnvelope(self, requestEnvelope: Envelope, messageType: MessageType) -> Envelope:
		return Envelope(
			protocolVersion=PROTOCOL_VERSION,
			messageType=messageType,
			sessionId=requestEnvelope.sessionId,
			sequenceNumber=requestEnvelope.sequenceNumber,
			requestId=requestEnvelope.requestId,
		)

	def _errorResponse(self, requestEnvelope: Envelope, code: ErrorCode, message: str) -> ErrorResponse:
		return ErrorResponse(
			self._responseEnvelope(requestEnvelope, MessageType.ERROR_RESPONSE),
			ProtocolError(code, message),
		)

	def _jobRejection(self, request: SubmitJobRequest) -> ErrorResponse | None:
		envelope = request.envelope
		generationId = request.generationId
		if self._activeGenerationId is None:
			if generationId != 1:
				return self._errorResponse(envelope, ErrorCode.GENERATION_OUT_OF_ORDER, "first generation must be one")
			isNewGeneration = True
		elif generationId < self._activeGenerationId:
			code = ErrorCode.GENERATION_CANCELLED if generationId in self._cancelledGenerations else ErrorCode.GENERATION_STALE
			return self._errorResponse(envelope, code, "job generation is no longer current")
		elif generationId == self._activeGenerationId:
			if generationId in self._cancelledGenerations:
				return self._errorResponse(envelope, ErrorCode.GENERATION_CANCELLED, "job generation is cancelled")
			isNewGeneration = False
		else:
			if generationId != self._activeGenerationId + 1:
				return self._errorResponse(envelope, ErrorCode.GENERATION_OUT_OF_ORDER, "job generation is not the next generation")
			isNewGeneration = True
		if request.jobId in self._acceptedJobs:
			return self._errorResponse(envelope, ErrorCode.DUPLICATE_JOB, "job ID was already accepted")
		if len(self._acceptedJobs) >= MAX_TRACKED_JOBS:
			return self._errorResponse(envelope, ErrorCode.TRACKING_LIMIT_EXCEEDED, "job tracking limit was reached")
		if isNewGeneration and len(self._trackedGenerations) >= MAX_TRACKED_GENERATIONS:
			return self._errorResponse(envelope, ErrorCode.TRACKING_LIMIT_EXCEEDED, "generation tracking limit was reached")
		return None

	def _cancelRejection(self, request: CancelGenerationRequest) -> ErrorResponse | None:
		if self._activeGenerationId is None or request.generationId > self._activeGenerationId:
			return self._errorResponse(request.envelope, ErrorCode.GENERATION_UNKNOWN, "generation is not known")
		if (
			request.generationId == self._activeGenerationId
			and request.generationId not in self._cancelledGenerations
			and len(self._cancelledGenerations) >= MAX_CANCELLED_GENERATIONS
		):
			return self._errorResponse(request.envelope, ErrorCode.TRACKING_LIMIT_EXCEEDED, "cancelled-generation tracking limit was reached")
		return None

	def _fakeResultStatus(self, request: FakeResultRequest) -> FakeResultStatus:
		jobGeneration = self._acceptedJobs.get(request.jobId)
		if jobGeneration is None or jobGeneration != request.generationId:
			return FakeResultStatus.UNKNOWN_JOB
		if request.generationId in self._cancelledGenerations:
			return FakeResultStatus.CANCELLED_GENERATION
		if request.generationId != self._activeGenerationId:
			return FakeResultStatus.STALE_GENERATION
		if (request.jobId, request.resultId) in self._acceptedResults:
			return FakeResultStatus.DUPLICATE
		return FakeResultStatus.ACCEPTED_CURRENT

	def _stateRejection(self, request):
		envelope = request.envelope
		if self._isShutDown:
			return self._errorResponse(envelope, ErrorCode.WORKER_SHUT_DOWN, "fake worker is shut down")
		if type(request) not in (HelloRequest, SubmitJobRequest, CancelGenerationRequest, FakeResultRequest, ShutdownRequest):
			return self._errorResponse(envelope, ErrorCode.UNKNOWN_MESSAGE_TYPE, "message is not a worker request")
		if self._sessionId is None:
			if type(request) is not HelloRequest:
				return self._errorResponse(envelope, ErrorCode.HANDSHAKE_REQUIRED, "hello handshake is required")
		else:
			if type(request) is HelloRequest:
				return self._errorResponse(envelope, ErrorCode.DUPLICATE_HANDSHAKE, "hello handshake is already complete")
			if envelope.sessionId != self._sessionId:
				return self._errorResponse(envelope, ErrorCode.WRONG_SESSION, "request session does not match")
		if envelope.requestId in self._acceptedRequestIds:
			return self._errorResponse(envelope, ErrorCode.DUPLICATE_REQUEST, "request ID was already accepted")
		if envelope.sequenceNumber != self._nextSequenceNumber:
			return self._errorResponse(envelope, ErrorCode.INVALID_SEQUENCE, "request sequence is not the next expected value")
		# Keep one final request slot available for deterministic shutdown.
		if type(request) is not ShutdownRequest and len(self._acceptedRequestIds) >= MAX_TRACKED_REQUESTS - 1:
			return self._errorResponse(envelope, ErrorCode.TRACKING_LIMIT_EXCEEDED, "request tracking limit was reached")
		if type(request) is SubmitJobRequest:
			return self._jobRejection(request)
		if type(request) is CancelGenerationRequest:
			return self._cancelRejection(request)
		if type(request) is FakeResultRequest:
			status = self._fakeResultStatus(request)
			if status is FakeResultStatus.ACCEPTED_CURRENT and len(self._acceptedResults) >= MAX_TRACKED_RESULTS:
				return self._errorResponse(envelope, ErrorCode.TRACKING_LIMIT_EXCEEDED, "fake-result tracking limit was reached")
		return None

	def _accept(self, request):
		envelope = request.envelope
		if type(request) is HelloRequest:
			response = HelloResponse(
				self._responseEnvelope(envelope, MessageType.HELLO_RESPONSE),
				self.capabilities,
			)
		elif type(request) is SubmitJobRequest:
			response = JobAcceptedResponse(
				self._responseEnvelope(envelope, MessageType.JOB_ACCEPTED_RESPONSE),
				request.generationId,
				request.jobId,
			)
		elif type(request) is CancelGenerationRequest:
			changedState = (
				request.generationId == self._activeGenerationId
				and request.generationId not in self._cancelledGenerations
			)
			response = CancelGenerationResponse(
				self._responseEnvelope(envelope, MessageType.CANCEL_GENERATION_RESPONSE),
				request.generationId,
				changedState,
			)
		elif type(request) is FakeResultRequest:
			status = self._fakeResultStatus(request)
			response = FakeResultResponse(
				self._responseEnvelope(envelope, MessageType.FAKE_RESULT_RESPONSE),
				request.generationId,
				request.jobId,
				request.resultId,
				status,
			)
		elif type(request) is ShutdownRequest:
			response = ShutdownResponse(self._responseEnvelope(envelope, MessageType.SHUTDOWN_RESPONSE))
		else:
			raise RuntimeError("validated request type was not handled")

		self._acceptedRequestIds.add(envelope.requestId)
		self._nextSequenceNumber += 1
		if type(request) is HelloRequest:
			self._sessionId = envelope.sessionId
		elif type(request) is SubmitJobRequest:
			self._trackedGenerations.add(request.generationId)
			self._activeGenerationId = request.generationId
			self._acceptedJobs[request.jobId] = request.generationId
		elif type(request) is CancelGenerationRequest:
			if response.changedState:
				self._cancelledGenerations.add(request.generationId)
		elif type(request) is FakeResultRequest:
			if response.status is FakeResultStatus.ACCEPTED_CURRENT:
				self._acceptedResults.add((request.jobId, request.resultId))
		elif type(request) is ShutdownRequest:
			self._isShutDown = True
		return response

	def handleFrame(self, frame: bytes) -> bytes:
		"""Decode one complete request frame and return one complete response frame."""
		request = decodeMessage(frame)
		rejection = self._stateRejection(request)
		if rejection is not None:
			return encodeMessage(rejection)
		try:
			response = self._accept(request)
		except Exception:
			response = self._errorResponse(
				request.envelope,
				ErrorCode.INTERNAL_FAKE_WORKER_ERROR,
				"fake worker could not handle the request",
			)
		return encodeMessage(response)
