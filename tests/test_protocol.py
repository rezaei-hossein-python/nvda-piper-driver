"""Tests for the bounded Phase 2F protocol model and strict JSON codec."""

from dataclasses import fields, FrozenInstanceError
import json
import unittest

from addon.synthDrivers._nvdaPiperDriver.jobs import (
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
from addon.synthDrivers._nvdaPiperDriver import protocol


def envelope(messageType: protocol.MessageType, sequence: int = 1, request: int = 1, session: int = 7):
	return protocol.Envelope(protocol.PROTOCOL_VERSION, messageType, session, sequence, request)


def sampleJob(*items, jobId: int = 1, generationId: int = 2) -> SpeechJob:
	return SpeechJob(jobId, generationId, 3, tuple(items), "mockVoice", 50)


def submitRequest(job: SpeechJob | None = None) -> protocol.SubmitJobRequest:
	job = job or sampleJob(TextItem("text"))
	return protocol.SubmitJobRequest(
		envelope(protocol.MessageType.SUBMIT_JOB_REQUEST),
		job.generationId,
		job.jobId,
		job,
	)


def wireObject(message) -> dict:
	return json.loads(protocol.encodeMessage(message).decode("utf-8"))


def wireBytes(value: object) -> bytes:
	return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


class ProtocolTests(unittest.TestCase):
	def assertProtocolCode(self, code: protocol.ErrorCode, callableObject, *args) -> None:
		with self.assertRaises(protocol.ProtocolException) as error:
			callableObject(*args)
		self.assertIs(code, error.exception.error.code)

	def test_protocol_values_are_immutable(self) -> None:
		values = [
			envelope(protocol.MessageType.HELLO_REQUEST),
			protocol.Capabilities(),
			protocol.ProtocolError(protocol.ErrorCode.INVALID_JSON, "safe"),
			protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST)),
			protocol.HelloResponse(envelope(protocol.MessageType.HELLO_RESPONSE), protocol.Capabilities()),
			submitRequest(),
			protocol.JobAcceptedResponse(envelope(protocol.MessageType.JOB_ACCEPTED_RESPONSE), 2, 1),
			protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST)),
			protocol.ShutdownResponse(envelope(protocol.MessageType.SHUTDOWN_RESPONSE)),
			protocol.ErrorResponse(envelope(protocol.MessageType.ERROR_RESPONSE), protocol.ProtocolError(protocol.ErrorCode.INVALID_SEQUENCE, "safe")),
		]
		for value in values:
			with self.subTest(valueType=type(value)), self.assertRaises(FrozenInstanceError):
				fieldName = fields(value)[0].name
				setattr(value, fieldName, getattr(value, fieldName))

	def test_deterministic_utf8_round_trip_preserves_every_item(self) -> None:
		items = (
			TextItem(" فارسی English e\u0301\n\u200c\u200f "),
			TextItem(""),
			IndexItem(-3),
			CharacterModeItem(True),
			LanguageChangeItem(None),
			LanguageChangeItem("fa_IR"),
			BreakItem(25),
			ProsodyItem(ProsodyCommandType.RATE, 4, 1, False),
			ProsodyItem(ProsodyCommandType.PITCH, 0, 1.5, False),
			ProsodyItem(ProsodyCommandType.VOLUME, 0, 1, True),
			PhonemeItem("tɛst", None),
			PhonemeItem("a", ""),
		)
		request = submitRequest(sampleJob(*items))
		first = protocol.encodeMessage(request)
		second = protocol.encodeMessage(request)
		self.assertEqual(first, second)
		self.assertIn("فارسی".encode("utf-8"), first)
		decoded = protocol.decodeMessage(first)
		self.assertEqual(request, decoded)
		self.assertEqual(items, decoded.job.items)

	def test_all_message_types_round_trip(self) -> None:
		messages = (
			protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST)),
			protocol.HelloResponse(envelope(protocol.MessageType.HELLO_RESPONSE), protocol.Capabilities()),
			submitRequest(),
			protocol.JobAcceptedResponse(envelope(protocol.MessageType.JOB_ACCEPTED_RESPONSE), 2, 1),
			protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST)),
			protocol.ShutdownResponse(envelope(protocol.MessageType.SHUTDOWN_RESPONSE)),
			protocol.ErrorResponse(envelope(protocol.MessageType.ERROR_RESPONSE), protocol.ProtocolError(protocol.ErrorCode.WRONG_SESSION, "safe")),
		)
		for message in messages:
			with self.subTest(messageType=type(message)):
				self.assertEqual(message, protocol.decodeMessage(protocol.encodeMessage(message)))

	def test_capabilities_and_error_messages_are_fixed_and_bounded(self) -> None:
		changed = protocol.HelloResponse(
			envelope(protocol.MessageType.HELLO_RESPONSE),
			protocol.Capabilities(synthesis=True),
		)
		self.assertProtocolCode(protocol.ErrorCode.INVALID_FIELD_VALUE, protocol.encodeMessage, changed)
		longError = protocol.ErrorResponse(
			envelope(protocol.MessageType.ERROR_RESPONSE),
			protocol.ProtocolError(protocol.ErrorCode.INVALID_JSON, "x" * (protocol.MAX_ERROR_MESSAGE_CODEPOINTS + 1)),
		)
		self.assertProtocolCode(protocol.ErrorCode.INVALID_FIELD_VALUE, protocol.encodeMessage, longError)

	def test_frame_and_json_rejections(self) -> None:
		self.assertProtocolCode(protocol.ErrorCode.MALFORMED_FRAME, protocol.decodeMessage, "not bytes")
		self.assertProtocolCode(protocol.ErrorCode.MALFORMED_FRAME, protocol.decodeMessage, b"")
		self.assertProtocolCode(protocol.ErrorCode.OVERSIZED_FRAME, protocol.decodeMessage, b" " * (protocol.MAX_FRAME_BYTES + 1))
		self.assertProtocolCode(protocol.ErrorCode.INVALID_ENCODING, protocol.decodeMessage, b"\xff")
		self.assertProtocolCode(protocol.ErrorCode.INVALID_ENCODING, protocol.decodeMessage, b"\xef\xbb\xbf{}")
		self.assertProtocolCode(protocol.ErrorCode.INVALID_JSON, protocol.decodeMessage, b"{")
		self.assertProtocolCode(protocol.ErrorCode.INVALID_JSON, protocol.decodeMessage, b"{} {}")
		self.assertProtocolCode(protocol.ErrorCode.DUPLICATE_JSON_KEY, protocol.decodeMessage, b'{"protocolVersion":1,"protocolVersion":1}')
		self.assertProtocolCode(protocol.ErrorCode.INVALID_JSON, protocol.decodeMessage, b'{"value":NaN}')
		self.assertProtocolCode(protocol.ErrorCode.INVALID_JSON, protocol.decodeMessage, b'{"value":Infinity}')
		self.assertProtocolCode(protocol.ErrorCode.INVALID_JSON, protocol.decodeMessage, b'{"value":1e999}')

	def test_depth_limit_is_enforced(self) -> None:
		value: object = 0
		for _ in range(protocol.MAX_NESTING_DEPTH + 1):
			value = [value]
		self.assertProtocolCode(protocol.ErrorCode.MALFORMED_FRAME, protocol.decodeMessage, wireBytes(value))

	def test_envelope_schema_rejections(self) -> None:
		base = wireObject(protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST)))
		cases = []
		unknown = dict(base, unexpected=1)
		cases.append((protocol.ErrorCode.UNKNOWN_FIELD, unknown))
		missing = dict(base)
		missing.pop("requestId")
		cases.append((protocol.ErrorCode.MISSING_FIELD, missing))
		unknownType = dict(base, messageType="future")
		cases.append((protocol.ErrorCode.UNKNOWN_MESSAGE_TYPE, unknownType))
		wrongVersion = dict(base, protocolVersion=2)
		cases.append((protocol.ErrorCode.UNSUPPORTED_PROTOCOL_VERSION, wrongVersion))
		for field in ("protocolVersion", "sessionId", "sequenceNumber", "requestId"):
			wrong = dict(base, **{field: True})
			cases.append((protocol.ErrorCode.INVALID_FIELD_TYPE, wrong))
		for field in ("sessionId", "sequenceNumber", "requestId"):
			for value in (0, -1, protocol.MAX_IDENTIFIER + 1):
				wrong = dict(base, **{field: value})
				cases.append((protocol.ErrorCode.INVALID_FIELD_VALUE, wrong))
		for expectedCode, value in cases:
			with self.subTest(expectedCode=expectedCode, value=value):
				self.assertProtocolCode(expectedCode, protocol.decodeMessage, wireBytes(value))

	def test_payload_and_item_schema_rejections(self) -> None:
		base = wireObject(submitRequest())
		missing = json.loads(json.dumps(base))
		missing["payload"].pop("jobId")
		self.assertProtocolCode(protocol.ErrorCode.MISSING_FIELD, protocol.decodeMessage, wireBytes(missing))
		unknown = json.loads(json.dumps(base))
		unknown["payload"]["extra"] = 1
		self.assertProtocolCode(protocol.ErrorCode.UNKNOWN_FIELD, protocol.decodeMessage, wireBytes(unknown))
		unknownItem = json.loads(json.dumps(base))
		unknownItem["payload"]["job"]["items"] = [{"type": "future"}]
		self.assertProtocolCode(protocol.ErrorCode.UNSUPPORTED_JOB_ITEM, protocol.decodeMessage, wireBytes(unknownItem))
		malformedItem = json.loads(json.dumps(base))
		malformedItem["payload"]["job"]["items"] = [{"type": "text", "text": "safe", "extra": 1}]
		self.assertProtocolCode(protocol.ErrorCode.UNKNOWN_FIELD, protocol.decodeMessage, wireBytes(malformedItem))
		for path in (("payload", "jobId"), ("payload", "generationId"), ("payload", "job", "jobId"), ("payload", "job", "rate")):
			wrong = json.loads(json.dumps(base))
			target = wrong
			for key in path[:-1]:
				target = target[key]
			target[path[-1]] = True
			with self.subTest(path=path):
				self.assertProtocolCode(protocol.ErrorCode.INVALID_FIELD_TYPE, protocol.decodeMessage, wireBytes(wrong))

	def test_job_limits_are_enforced(self) -> None:
		tooMany = sampleJob(*(TextItem("") for _ in range(protocol.MAX_JOB_ITEMS + 1)))
		self.assertProtocolCode(protocol.ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, protocol.encodeMessage, submitRequest(tooMany))
		longText = sampleJob(TextItem("x" * (protocol.MAX_TEXT_CODEPOINTS_PER_ITEM + 1)))
		self.assertProtocolCode(protocol.ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, protocol.encodeMessage, submitRequest(longText))
		totalText = sampleJob(*(TextItem("x" * protocol.MAX_TEXT_CODEPOINTS_PER_ITEM) for _ in range(5)))
		self.assertProtocolCode(protocol.ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, protocol.encodeMessage, submitRequest(totalText))
		longIpa = sampleJob(PhonemeItem("x" * (protocol.MAX_IPA_CODEPOINTS + 1), None))
		self.assertProtocolCode(protocol.ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, protocol.encodeMessage, submitRequest(longIpa))
		longFallback = sampleJob(PhonemeItem("a", "x" * (protocol.MAX_FALLBACK_CODEPOINTS + 1)))
		self.assertProtocolCode(protocol.ErrorCode.JOB_SIZE_LIMIT_EXCEEDED, protocol.encodeMessage, submitRequest(longFallback))
		frameOverflow = sampleJob(*(TextItem("😀" * protocol.MAX_TEXT_CODEPOINTS_PER_ITEM) for _ in range(4)))
		self.assertProtocolCode(protocol.ErrorCode.OVERSIZED_FRAME, protocol.encodeMessage, submitRequest(frameOverflow))

	def test_invalid_local_items_and_non_finite_numbers_are_rejected_privately(self) -> None:
		class Hostile:
			def __repr__(self):
				raise AssertionError("hostile item was represented")
			def __str__(self):
				raise AssertionError("hostile item was formatted")
		private = "PRIVATE_PROTOCOL_TEXT"
		for job in (
			sampleJob(Hostile()),
			sampleJob(ProsodyItem(ProsodyCommandType.RATE, 0, float("nan"), False)),
			sampleJob(ProsodyItem(ProsodyCommandType.RATE, 0, float("inf"), False)),
		):
			with self.subTest(itemType=type(job.items[0])), self.assertRaises(protocol.ProtocolException) as error:
				protocol.encodeMessage(submitRequest(job))
			self.assertNotIn(private, str(error.exception))

	def test_text_bearing_representations_are_redacted(self) -> None:
		private = "PRIVATE_PROTOCOL_TEXT"
		job = sampleJob(TextItem(private), PhonemeItem(private, private))
		request = submitRequest(job)
		self.assertNotIn(private, repr(job))
		self.assertNotIn(private, repr(request))
		error = protocol.ProtocolError(protocol.ErrorCode.INVALID_JSON, private)
		self.assertNotIn(private, repr(error))


if __name__ == "__main__":
	unittest.main()
