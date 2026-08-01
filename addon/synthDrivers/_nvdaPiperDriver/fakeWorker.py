"""Deterministic synchronous Phase 2F fake-worker state machine."""

from .protocol import (
	Capabilities,
	Envelope,
	ErrorCode,
	ErrorResponse,
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
		self._acceptedJobIds: set[int] = set()
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

	def _stateRejection(self, request):
		envelope = request.envelope
		if self._isShutDown:
			return self._errorResponse(envelope, ErrorCode.WORKER_SHUT_DOWN, "fake worker is shut down")
		if type(request) not in (HelloRequest, SubmitJobRequest, ShutdownRequest):
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
		if type(request) is SubmitJobRequest and request.jobId in self._acceptedJobIds:
			return self._errorResponse(envelope, ErrorCode.DUPLICATE_JOB, "job ID was already accepted")
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
		elif type(request) is ShutdownRequest:
			response = ShutdownResponse(self._responseEnvelope(envelope, MessageType.SHUTDOWN_RESPONSE))
		else:
			raise RuntimeError("validated request type was not handled")

		self._acceptedRequestIds.add(envelope.requestId)
		self._nextSequenceNumber += 1
		if type(request) is HelloRequest:
			self._sessionId = envelope.sessionId
		elif type(request) is SubmitJobRequest:
			self._acceptedJobIds.add(request.jobId)
		else:
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
