"""Bounded Phase 2G protocol values and strict JSON serialization."""

from dataclasses import dataclass, field
from enum import Enum
import json
import math
from typing import TypeAlias

from .jobs import (
	BreakItem,
	CharacterModeItem,
	IndexItem,
	LanguageChangeItem,
	PhonemeItem,
	ProsodyCommandType,
	ProsodyItem,
	SpeechJob,
	TextItem,
)


PROTOCOL_VERSION = 1
MAX_IDENTIFIER = (1 << 63) - 1
MAX_FRAME_BYTES = 65_536
MAX_NESTING_DEPTH = 8
MAX_JOB_ITEMS = 64
MAX_TEXT_CODEPOINTS_PER_ITEM = 4_096
MAX_TOTAL_TEXT_CODEPOINTS = 16_384
MAX_IPA_CODEPOINTS = 1_024
MAX_FALLBACK_CODEPOINTS = 4_096
MAX_LANGUAGE_CODEPOINTS = 64
MAX_VOICE_ID_CODEPOINTS = 128
MAX_CAPABILITY_FIELDS = 10
MAX_ERROR_MESSAGE_CODEPOINTS = 160
MAX_TRACKED_REQUESTS = 2_048
MAX_TRACKED_GENERATIONS = 64
MAX_TRACKED_JOBS = 256
MAX_TRACKED_RESULTS = 512
MAX_CANCELLED_GENERATIONS = 32


class MessageType(Enum):
	HELLO_REQUEST = "helloRequest"
	HELLO_RESPONSE = "helloResponse"
	SUBMIT_JOB_REQUEST = "submitJobRequest"
	JOB_ACCEPTED_RESPONSE = "jobAcceptedResponse"
	CANCEL_GENERATION_REQUEST = "cancelGenerationRequest"
	CANCEL_GENERATION_RESPONSE = "cancelGenerationResponse"
	FAKE_RESULT_REQUEST = "fakeResultRequest"
	FAKE_RESULT_RESPONSE = "fakeResultResponse"
	SHUTDOWN_REQUEST = "shutdownRequest"
	SHUTDOWN_RESPONSE = "shutdownResponse"
	ERROR_RESPONSE = "errorResponse"


class ErrorCode(Enum):
	MALFORMED_FRAME = "malformedFrame"
	OVERSIZED_FRAME = "oversizedFrame"
	INVALID_ENCODING = "invalidEncoding"
	INVALID_JSON = "invalidJson"
	DUPLICATE_JSON_KEY = "duplicateJsonKey"
	UNKNOWN_MESSAGE_TYPE = "unknownMessageType"
	UNSUPPORTED_PROTOCOL_VERSION = "unsupportedProtocolVersion"
	MISSING_FIELD = "missingField"
	UNKNOWN_FIELD = "unknownField"
	INVALID_FIELD_TYPE = "invalidFieldType"
	INVALID_FIELD_VALUE = "invalidFieldValue"
	WRONG_SESSION = "wrongSession"
	HANDSHAKE_REQUIRED = "handshakeRequired"
	DUPLICATE_HANDSHAKE = "duplicateHandshake"
	INVALID_SEQUENCE = "invalidSequence"
	DUPLICATE_REQUEST = "duplicateRequest"
	DUPLICATE_JOB = "duplicateJob"
	GENERATION_STALE = "generationStale"
	GENERATION_CANCELLED = "generationCancelled"
	GENERATION_UNKNOWN = "generationUnknown"
	GENERATION_OUT_OF_ORDER = "generationOutOfOrder"
	TRACKING_LIMIT_EXCEEDED = "trackingLimitExceeded"
	WORKER_SHUT_DOWN = "workerShutDown"
	UNSUPPORTED_JOB_ITEM = "unsupportedJobItem"
	JOB_SIZE_LIMIT_EXCEEDED = "jobSizeLimitExceeded"
	INTERNAL_FAKE_WORKER_ERROR = "internalFakeWorkerError"


@dataclass(frozen=True, slots=True)
class ProtocolError:
	code: ErrorCode
	message: str = field(repr=False)


class ProtocolException(Exception):
	"""Raised for frame, JSON, or schema failures before worker state handling."""

	def __init__(self, error: ProtocolError) -> None:
		self.error = error
		super().__init__(f"{error.code.value}: {error.message}")


@dataclass(frozen=True, slots=True)
class Envelope:
	protocolVersion: int
	messageType: MessageType
	sessionId: int
	sequenceNumber: int
	requestId: int


@dataclass(frozen=True, slots=True)
class Capabilities:
	protocolVersion: int = PROTOCOL_VERSION
	workerIdentity: str = "NVDA Piper Driver Phase 2G fake worker"
	acceptsSpeechJobs: bool = True
	synthesis: bool = False
	audio: bool = False
	cancellation: bool = True
	pause: bool = False
	models: bool = False
	streaming: bool = False
	notifications: bool = False


@dataclass(frozen=True, slots=True)
class HelloRequest:
	envelope: Envelope


@dataclass(frozen=True, slots=True)
class HelloResponse:
	envelope: Envelope
	capabilities: Capabilities


@dataclass(frozen=True, slots=True)
class SubmitJobRequest:
	envelope: Envelope
	generationId: int
	jobId: int
	job: SpeechJob = field(repr=False)


@dataclass(frozen=True, slots=True)
class JobAcceptedResponse:
	envelope: Envelope
	generationId: int
	jobId: int


@dataclass(frozen=True, slots=True)
class CancelGenerationRequest:
	envelope: Envelope
	generationId: int


@dataclass(frozen=True, slots=True)
class CancelGenerationResponse:
	envelope: Envelope
	generationId: int
	changedState: bool


class FakeResultStatus(Enum):
	ACCEPTED_CURRENT = "acceptedCurrent"
	STALE_GENERATION = "staleGeneration"
	CANCELLED_GENERATION = "cancelledGeneration"
	UNKNOWN_JOB = "unknownJob"
	DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class FakeResultRequest:
	envelope: Envelope
	generationId: int
	jobId: int
	resultId: int


@dataclass(frozen=True, slots=True)
class FakeResultResponse:
	envelope: Envelope
	generationId: int
	jobId: int
	resultId: int
	status: FakeResultStatus


@dataclass(frozen=True, slots=True)
class ShutdownRequest:
	envelope: Envelope


@dataclass(frozen=True, slots=True)
class ShutdownResponse:
	envelope: Envelope


@dataclass(frozen=True, slots=True)
class ErrorResponse:
	envelope: Envelope
	error: ProtocolError


ProtocolMessage: TypeAlias = (
	HelloRequest
	| HelloResponse
	| SubmitJobRequest
	| JobAcceptedResponse
	| CancelGenerationRequest
	| CancelGenerationResponse
	| FakeResultRequest
	| FakeResultResponse
	| ShutdownRequest
	| ShutdownResponse
	| ErrorResponse
)


def _error(code: ErrorCode, message: str) -> ProtocolException:
	if len(message) > MAX_ERROR_MESSAGE_CODEPOINTS:
		message = "Protocol validation failed"
	return ProtocolException(ProtocolError(code, message))


def _requireExactFields(value: object, expected: set[str], context: str) -> dict[str, object]:
	if type(value) is not dict:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, f"{context} must be an object")
	missing = expected - value.keys()
	if missing:
		raise _error(ErrorCode.MISSING_FIELD, f"{context} is missing a required field")
	if value.keys() - expected:
		raise _error(ErrorCode.UNKNOWN_FIELD, f"{context} contains an unknown field")
	return value


def _requireInteger(value: object, fieldName: str, *, positive: bool = True) -> int:
	if type(value) is not int:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, f"{fieldName} must be an integer")
	minimum = 1 if positive else 0
	if not minimum <= value <= MAX_IDENTIFIER:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, f"{fieldName} is outside the allowed range")
	return value


def _requireSignedInteger(value: object, fieldName: str) -> int:
	if type(value) is not int:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, f"{fieldName} must be an integer")
	if not -MAX_IDENTIFIER <= value <= MAX_IDENTIFIER:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, f"{fieldName} is outside the allowed range")
	return value


def _requireBoolean(value: object, fieldName: str) -> bool:
	if type(value) is not bool:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, f"{fieldName} must be Boolean")
	return value


def _requireString(value: object, fieldName: str, maximum: int, *, allowNone: bool = False) -> str | None:
	if allowNone and value is None:
		return None
	if type(value) is not str:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, f"{fieldName} must be a string")
	if len(value) > maximum:
		raise _error(ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, f"{fieldName} exceeds its size limit")
	return value


def _validateEnvelope(envelope: Envelope, expectedType: MessageType | None = None) -> None:
	if type(envelope) is not Envelope:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "envelope has an invalid type")
	if type(envelope.protocolVersion) is not int:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "protocolVersion must be an integer")
	if envelope.protocolVersion != PROTOCOL_VERSION:
		raise _error(ErrorCode.UNSUPPORTED_PROTOCOL_VERSION, "protocol version is unsupported")
	if type(envelope.messageType) is not MessageType:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "messageType has an invalid type")
	if expectedType is not None and envelope.messageType is not expectedType:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "messageType does not match the message schema")
	_requireInteger(envelope.sessionId, "sessionId")
	_requireInteger(envelope.sequenceNumber, "sequenceNumber")
	_requireInteger(envelope.requestId, "requestId")


def _itemToWire(item: object) -> dict[str, object]:
	itemType = type(item)
	if itemType is TextItem:
		_requireString(item.text, "text", MAX_TEXT_CODEPOINTS_PER_ITEM)
		return {"type": "text", "text": item.text}
	if itemType is IndexItem:
		return {"type": "index", "index": _requireSignedInteger(item.index, "index")}
	if itemType is CharacterModeItem:
		return {"type": "characterMode", "state": _requireBoolean(item.state, "state")}
	if itemType is LanguageChangeItem:
		return {"type": "language", "language": _requireString(item.language, "language", MAX_LANGUAGE_CODEPOINTS, allowNone=True)}
	if itemType is BreakItem:
		return {"type": "break", "durationMs": _requireInteger(item.durationMs, "durationMs", positive=False)}
	if itemType is ProsodyItem:
		if type(item.commandType) is not ProsodyCommandType:
			raise _error(ErrorCode.UNSUPPORTED_JOB_ITEM, "prosody command type is unsupported")
		if type(item.offset) is not int:
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "prosody offset must be an integer")
		if not -MAX_IDENTIFIER <= item.offset <= MAX_IDENTIFIER:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody offset is outside the allowed range")
		if type(item.multiplier) not in (int, float):
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "prosody multiplier has an invalid type")
		if not math.isfinite(item.multiplier):
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody multiplier is invalid")
		if item.offset != 0 and item.multiplier != 1:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody values conflict")
		if type(item.isDefault) is not bool or item.isDefault is not (item.offset == 0 and item.multiplier == 1):
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody default state is invalid")
		return {
			"type": item.commandType.value,
			"offset": item.offset,
			"multiplier": item.multiplier,
			"isDefault": item.isDefault,
		}
	if itemType is PhonemeItem:
		return {
			"type": "phoneme",
			"ipa": _requireString(item.ipa, "ipa", MAX_IPA_CODEPOINTS),
			"fallbackText": _requireString(item.fallbackText, "fallbackText", MAX_FALLBACK_CODEPOINTS, allowNone=True),
		}
	raise _error(ErrorCode.UNSUPPORTED_JOB_ITEM, "job item type is unsupported")


def _jobToWire(job: SpeechJob) -> dict[str, object]:
	if type(job) is not SpeechJob:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "job has an invalid type")
	_requireInteger(job.jobId, "job.jobId")
	_requireInteger(job.generationId, "job.generationId")
	_requireInteger(job.requestNumber, "job.requestNumber")
	_requireString(job.voiceId, "job.voiceId", MAX_VOICE_ID_CODEPOINTS)
	if not job.voiceId:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "job.voiceId must not be empty")
	if type(job.rate) is not int:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "job.rate must be an integer")
	if not 0 <= job.rate <= 100:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "job.rate is outside the allowed range")
	if type(job.items) is not tuple:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "job.items must be a tuple")
	if len(job.items) > MAX_JOB_ITEMS:
		raise _error(ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, "job item count exceeds its limit")
	items = [_itemToWire(item) for item in job.items]
	totalText = sum(
		len(item.text) if type(item) is TextItem else len(item.fallbackText or "") if type(item) is PhonemeItem else 0
		for item in job.items
	)
	if totalText > MAX_TOTAL_TEXT_CODEPOINTS:
		raise _error(ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, "job text exceeds its total size limit")
	return {
		"jobId": job.jobId,
		"generationId": job.generationId,
		"requestNumber": job.requestNumber,
		"items": items,
		"voiceId": job.voiceId,
		"rate": job.rate,
	}


def _wireToItem(value: object):
	if type(value) is not dict:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "job item must be an object")
	itemType = value.get("type")
	if type(itemType) is not str:
		raise _error(ErrorCode.MISSING_FIELD if "type" not in value else ErrorCode.INVALID_FIELD_TYPE, "job item type is invalid")
	if itemType == "text":
		fields = _requireExactFields(value, {"type", "text"}, "text item")
		return TextItem(_requireString(fields["text"], "text", MAX_TEXT_CODEPOINTS_PER_ITEM))
	if itemType == "index":
		fields = _requireExactFields(value, {"type", "index"}, "index item")
		return IndexItem(_requireSignedInteger(fields["index"], "index"))
	if itemType == "characterMode":
		fields = _requireExactFields(value, {"type", "state"}, "character-mode item")
		return CharacterModeItem(_requireBoolean(fields["state"], "state"))
	if itemType == "language":
		fields = _requireExactFields(value, {"type", "language"}, "language item")
		return LanguageChangeItem(_requireString(fields["language"], "language", MAX_LANGUAGE_CODEPOINTS, allowNone=True))
	if itemType == "break":
		fields = _requireExactFields(value, {"type", "durationMs"}, "break item")
		return BreakItem(_requireInteger(fields["durationMs"], "durationMs", positive=False))
	if itemType in {"rate", "pitch", "volume"}:
		fields = _requireExactFields(value, {"type", "offset", "multiplier", "isDefault"}, "prosody item")
		offset = fields["offset"]
		multiplier = fields["multiplier"]
		isDefault = fields["isDefault"]
		if type(offset) is not int or not -MAX_IDENTIFIER <= offset <= MAX_IDENTIFIER:
			raise _error(ErrorCode.INVALID_FIELD_TYPE if type(offset) is not int else ErrorCode.INVALID_FIELD_VALUE, "prosody offset is invalid")
		if type(multiplier) not in (int, float):
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "prosody multiplier has an invalid type")
		if not math.isfinite(multiplier):
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody multiplier is invalid")
		_requireBoolean(isDefault, "isDefault")
		if offset != 0 and multiplier != 1:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody values conflict")
		if isDefault is not (offset == 0 and multiplier == 1):
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "prosody default state is invalid")
		commandType = ProsodyCommandType(itemType)
		return ProsodyItem(commandType, offset, multiplier, isDefault)
	if itemType == "phoneme":
		fields = _requireExactFields(value, {"type", "ipa", "fallbackText"}, "phoneme item")
		return PhonemeItem(
			_requireString(fields["ipa"], "ipa", MAX_IPA_CODEPOINTS),
			_requireString(fields["fallbackText"], "fallbackText", MAX_FALLBACK_CODEPOINTS, allowNone=True),
		)
	raise _error(ErrorCode.UNSUPPORTED_JOB_ITEM, "job item type is unsupported")


def _wireToJob(value: object) -> SpeechJob:
	fields = _requireExactFields(value, {"jobId", "generationId", "requestNumber", "items", "voiceId", "rate"}, "job")
	if type(fields["items"]) is not list:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "job.items must be an array")
	if len(fields["items"]) > MAX_JOB_ITEMS:
		raise _error(ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, "job item count exceeds its limit")
	items = tuple(_wireToItem(item) for item in fields["items"])
	job = SpeechJob(
		jobId=_requireInteger(fields["jobId"], "job.jobId"),
		generationId=_requireInteger(fields["generationId"], "job.generationId"),
		requestNumber=_requireInteger(fields["requestNumber"], "job.requestNumber"),
		items=items,
		voiceId=_requireString(fields["voiceId"], "job.voiceId", MAX_VOICE_ID_CODEPOINTS),
		rate=_requireInteger(fields["rate"], "job.rate", positive=False),
	)
	return _wireValidatedJob(job)


def _wireValidatedJob(job: SpeechJob) -> SpeechJob:
	_jobToWire(job)
	return job


def _capabilitiesToWire(capabilities: Capabilities) -> dict[str, object]:
	if type(capabilities) is not Capabilities:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "capabilities have an invalid type")
	result = {
		"protocolVersion": capabilities.protocolVersion,
		"workerIdentity": capabilities.workerIdentity,
		"acceptsSpeechJobs": capabilities.acceptsSpeechJobs,
		"synthesis": capabilities.synthesis,
		"audio": capabilities.audio,
		"cancellation": capabilities.cancellation,
		"pause": capabilities.pause,
		"models": capabilities.models,
		"streaming": capabilities.streaming,
		"notifications": capabilities.notifications,
	}
	if len(result) > MAX_CAPABILITY_FIELDS:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "capability count exceeds its limit")
	if capabilities != Capabilities():
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "capabilities differ from the Phase 2G set")
	if capabilities.protocolVersion != PROTOCOL_VERSION:
		raise _error(ErrorCode.UNSUPPORTED_PROTOCOL_VERSION, "capability protocol version is unsupported")
	if capabilities.workerIdentity != "NVDA Piper Driver Phase 2G fake worker":
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "worker identity is invalid")
	for key in result.keys() - {"protocolVersion", "workerIdentity"}:
		_requireBoolean(result[key], key)
	return result


def _wireToCapabilities(value: object) -> Capabilities:
	expected = {"protocolVersion", "workerIdentity", "acceptsSpeechJobs", "synthesis", "audio", "cancellation", "pause", "models", "streaming", "notifications"}
	fields = _requireExactFields(value, expected, "capabilities")
	capabilities = Capabilities(
		protocolVersion=_requireInteger(fields["protocolVersion"], "capabilities.protocolVersion"),
		workerIdentity=_requireString(fields["workerIdentity"], "capabilities.workerIdentity", MAX_ERROR_MESSAGE_CODEPOINTS),
		acceptsSpeechJobs=_requireBoolean(fields["acceptsSpeechJobs"], "acceptsSpeechJobs"),
		synthesis=_requireBoolean(fields["synthesis"], "synthesis"),
		audio=_requireBoolean(fields["audio"], "audio"),
		cancellation=_requireBoolean(fields["cancellation"], "cancellation"),
		pause=_requireBoolean(fields["pause"], "pause"),
		models=_requireBoolean(fields["models"], "models"),
		streaming=_requireBoolean(fields["streaming"], "streaming"),
		notifications=_requireBoolean(fields["notifications"], "notifications"),
	)
	_capabilitiesToWire(capabilities)
	return capabilities


def _messageToWire(message: ProtocolMessage) -> dict[str, object]:
	messageType = type(message)
	expectedTypes = {
		HelloRequest: MessageType.HELLO_REQUEST,
		HelloResponse: MessageType.HELLO_RESPONSE,
		SubmitJobRequest: MessageType.SUBMIT_JOB_REQUEST,
		JobAcceptedResponse: MessageType.JOB_ACCEPTED_RESPONSE,
		CancelGenerationRequest: MessageType.CANCEL_GENERATION_REQUEST,
		CancelGenerationResponse: MessageType.CANCEL_GENERATION_RESPONSE,
		FakeResultRequest: MessageType.FAKE_RESULT_REQUEST,
		FakeResultResponse: MessageType.FAKE_RESULT_RESPONSE,
		ShutdownRequest: MessageType.SHUTDOWN_REQUEST,
		ShutdownResponse: MessageType.SHUTDOWN_RESPONSE,
		ErrorResponse: MessageType.ERROR_RESPONSE,
	}
	if messageType not in expectedTypes:
		raise _error(ErrorCode.UNKNOWN_MESSAGE_TYPE, "message object type is unsupported")
	_validateEnvelope(message.envelope, expectedTypes[messageType])
	payload: dict[str, object]
	if messageType in (HelloRequest, ShutdownRequest, ShutdownResponse):
		payload = {}
	elif messageType is HelloResponse:
		payload = {"capabilities": _capabilitiesToWire(message.capabilities)}
	elif messageType is SubmitJobRequest:
		generationId = _requireInteger(message.generationId, "generationId")
		jobId = _requireInteger(message.jobId, "jobId")
		jobWire = _jobToWire(message.job)
		if generationId != message.job.generationId or jobId != message.job.jobId:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "job envelope identifiers do not match")
		payload = {"generationId": generationId, "jobId": jobId, "job": jobWire}
	elif messageType is JobAcceptedResponse:
		payload = {
			"generationId": _requireInteger(message.generationId, "generationId"),
			"jobId": _requireInteger(message.jobId, "jobId"),
		}
	elif messageType is CancelGenerationRequest:
		payload = {"generationId": _requireInteger(message.generationId, "generationId")}
	elif messageType is CancelGenerationResponse:
		payload = {
			"generationId": _requireInteger(message.generationId, "generationId"),
			"changedState": _requireBoolean(message.changedState, "changedState"),
		}
	elif messageType is FakeResultRequest:
		payload = {
			"generationId": _requireInteger(message.generationId, "generationId"),
			"jobId": _requireInteger(message.jobId, "jobId"),
			"resultId": _requireInteger(message.resultId, "resultId"),
		}
	elif messageType is FakeResultResponse:
		if type(message.status) is not FakeResultStatus:
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "fake result status has an invalid type")
		payload = {
			"generationId": _requireInteger(message.generationId, "generationId"),
			"jobId": _requireInteger(message.jobId, "jobId"),
			"resultId": _requireInteger(message.resultId, "resultId"),
			"status": message.status.value,
		}
	elif messageType is ErrorResponse:
		if type(message.error) is not ProtocolError or type(message.error.code) is not ErrorCode:
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "error response is invalid")
		if type(message.error.message) is not str or len(message.error.message) > MAX_ERROR_MESSAGE_CODEPOINTS:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "error message is invalid")
		payload = {"error": {"code": message.error.code.value, "message": message.error.message}}
	return {
		"protocolVersion": message.envelope.protocolVersion,
		"messageType": message.envelope.messageType.value,
		"sessionId": message.envelope.sessionId,
		"sequenceNumber": message.envelope.sequenceNumber,
		"requestId": message.envelope.requestId,
		"payload": payload,
	}


def encodeMessage(message: ProtocolMessage) -> bytes:
	try:
		text = json.dumps(
			_messageToWire(message),
			ensure_ascii=False,
			allow_nan=False,
			separators=(",", ":"),
			sort_keys=True,
		)
	except (TypeError, ValueError) as error:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "message contains a non-JSON value") from error
	frame = text.encode("utf-8")
	if len(frame) > MAX_FRAME_BYTES:
		raise _error(ErrorCode.OVERSIZED_FRAME, "encoded frame exceeds its size limit")
	return frame


def _rejectConstant(_value: str):
	raise _error(ErrorCode.INVALID_JSON, "non-finite JSON number is forbidden")


def _objectFromPairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
	result: dict[str, object] = {}
	for key, value in pairs:
		if key in result:
			raise _error(ErrorCode.DUPLICATE_JSON_KEY, "JSON object contains a duplicate key")
		result[key] = value
	return result


def _depth(value: object) -> int:
	if type(value) is dict:
		return 1 + max((_depth(child) for child in value.values()), default=0)
	if type(value) is list:
		return 1 + max((_depth(child) for child in value), default=0)
	return 0


def _containsNonFinite(value: object) -> bool:
	if type(value) is float:
		return not math.isfinite(value)
	if type(value) is dict:
		return any(_containsNonFinite(child) for child in value.values())
	if type(value) is list:
		return any(_containsNonFinite(child) for child in value)
	return False


def _decodeEnvelope(root: dict[str, object]) -> tuple[Envelope, dict[str, object]]:
	fields = _requireExactFields(root, {"protocolVersion", "messageType", "sessionId", "sequenceNumber", "requestId", "payload"}, "message")
	protocolVersion = fields["protocolVersion"]
	if type(protocolVersion) is not int:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "protocolVersion must be an integer")
	if protocolVersion != PROTOCOL_VERSION:
		raise _error(ErrorCode.UNSUPPORTED_PROTOCOL_VERSION, "protocol version is unsupported")
	if type(fields["messageType"]) is not str:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "messageType must be a string")
	try:
		messageType = MessageType(fields["messageType"])
	except ValueError:
		raise _error(ErrorCode.UNKNOWN_MESSAGE_TYPE, "message type is unsupported") from None
	envelope = Envelope(
		protocolVersion=protocolVersion,
		messageType=messageType,
		sessionId=_requireInteger(fields["sessionId"], "sessionId"),
		sequenceNumber=_requireInteger(fields["sequenceNumber"], "sequenceNumber"),
		requestId=_requireInteger(fields["requestId"], "requestId"),
	)
	payload = fields["payload"]
	if type(payload) is not dict:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "payload must be an object")
	return envelope, payload


def _decodeMessage(root: dict[str, object]) -> ProtocolMessage:
	envelope, payload = _decodeEnvelope(root)
	messageType = envelope.messageType
	if messageType is MessageType.HELLO_REQUEST:
		_requireExactFields(payload, set(), "hello payload")
		return HelloRequest(envelope)
	if messageType is MessageType.HELLO_RESPONSE:
		fields = _requireExactFields(payload, {"capabilities"}, "hello response payload")
		return HelloResponse(envelope, _wireToCapabilities(fields["capabilities"]))
	if messageType is MessageType.SUBMIT_JOB_REQUEST:
		fields = _requireExactFields(payload, {"generationId", "jobId", "job"}, "submit payload")
		generationId = _requireInteger(fields["generationId"], "generationId")
		jobId = _requireInteger(fields["jobId"], "jobId")
		job = _wireToJob(fields["job"])
		if generationId != job.generationId or jobId != job.jobId:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "job envelope identifiers do not match")
		return SubmitJobRequest(envelope, generationId, jobId, job)
	if messageType is MessageType.JOB_ACCEPTED_RESPONSE:
		fields = _requireExactFields(payload, {"generationId", "jobId"}, "job response payload")
		return JobAcceptedResponse(
			envelope,
			_requireInteger(fields["generationId"], "generationId"),
			_requireInteger(fields["jobId"], "jobId"),
		)
	if messageType is MessageType.CANCEL_GENERATION_REQUEST:
		fields = _requireExactFields(payload, {"generationId"}, "cancel-generation payload")
		return CancelGenerationRequest(envelope, _requireInteger(fields["generationId"], "generationId"))
	if messageType is MessageType.CANCEL_GENERATION_RESPONSE:
		fields = _requireExactFields(payload, {"generationId", "changedState"}, "cancel-generation response payload")
		return CancelGenerationResponse(
			envelope,
			_requireInteger(fields["generationId"], "generationId"),
			_requireBoolean(fields["changedState"], "changedState"),
		)
	if messageType is MessageType.FAKE_RESULT_REQUEST:
		fields = _requireExactFields(payload, {"generationId", "jobId", "resultId"}, "fake-result payload")
		return FakeResultRequest(
			envelope,
			_requireInteger(fields["generationId"], "generationId"),
			_requireInteger(fields["jobId"], "jobId"),
			_requireInteger(fields["resultId"], "resultId"),
		)
	if messageType is MessageType.FAKE_RESULT_RESPONSE:
		fields = _requireExactFields(payload, {"generationId", "jobId", "resultId", "status"}, "fake-result response payload")
		if type(fields["status"]) is not str:
			raise _error(ErrorCode.INVALID_FIELD_TYPE, "fake result status must be a string")
		try:
			status = FakeResultStatus(fields["status"])
		except ValueError:
			raise _error(ErrorCode.INVALID_FIELD_VALUE, "fake result status is unknown") from None
		return FakeResultResponse(
			envelope,
			_requireInteger(fields["generationId"], "generationId"),
			_requireInteger(fields["jobId"], "jobId"),
			_requireInteger(fields["resultId"], "resultId"),
			status,
		)
	if messageType is MessageType.SHUTDOWN_REQUEST:
		_requireExactFields(payload, set(), "shutdown payload")
		return ShutdownRequest(envelope)
	if messageType is MessageType.SHUTDOWN_RESPONSE:
		_requireExactFields(payload, set(), "shutdown response payload")
		return ShutdownResponse(envelope)
	fields = _requireExactFields(payload, {"error"}, "error response payload")
	errorFields = _requireExactFields(fields["error"], {"code", "message"}, "error")
	if type(errorFields["code"]) is not str:
		raise _error(ErrorCode.INVALID_FIELD_TYPE, "error code must be a string")
	try:
		code = ErrorCode(errorFields["code"])
	except ValueError:
		raise _error(ErrorCode.INVALID_FIELD_VALUE, "error code is unknown") from None
	message = _requireString(errorFields["message"], "error message", MAX_ERROR_MESSAGE_CODEPOINTS)
	return ErrorResponse(envelope, ProtocolError(code, message))


def decodeMessage(frame: bytes) -> ProtocolMessage:
	if type(frame) is not bytes:
		raise _error(ErrorCode.MALFORMED_FRAME, "frame must be bytes")
	if not frame:
		raise _error(ErrorCode.MALFORMED_FRAME, "frame must not be empty")
	if len(frame) > MAX_FRAME_BYTES:
		raise _error(ErrorCode.OVERSIZED_FRAME, "frame exceeds its size limit")
	if frame.startswith(b"\xef\xbb\xbf"):
		raise _error(ErrorCode.INVALID_ENCODING, "UTF-8 BOM is forbidden")
	try:
		text = frame.decode("utf-8", errors="strict")
	except UnicodeDecodeError:
		raise _error(ErrorCode.INVALID_ENCODING, "frame is not valid UTF-8") from None
	try:
		root = json.loads(text, object_pairs_hook=_objectFromPairs, parse_constant=_rejectConstant)
	except ProtocolException:
		raise
	except (json.JSONDecodeError, RecursionError):
		raise _error(ErrorCode.INVALID_JSON, "frame is not one complete JSON document") from None
	try:
		depth = _depth(root)
	except RecursionError:
		raise _error(ErrorCode.MALFORMED_FRAME, "frame nesting exceeds its limit") from None
	if depth > MAX_NESTING_DEPTH:
		raise _error(ErrorCode.MALFORMED_FRAME, "frame nesting exceeds its limit")
	if _containsNonFinite(root):
		raise _error(ErrorCode.INVALID_JSON, "non-finite JSON number is forbidden")
	if type(root) is not dict:
		raise _error(ErrorCode.MALFORMED_FRAME, "top-level JSON value must be an object")
	return _decodeMessage(root)
