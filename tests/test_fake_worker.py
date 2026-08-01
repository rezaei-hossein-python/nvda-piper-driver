"""Tests for the synchronous in-process Phase 2F fake worker."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from addon.synthDrivers._nvdaPiperDriver.fakeWorker import FakeWorker
from addon.synthDrivers._nvdaPiperDriver.jobs import SpeechJob, TextItem
from addon.synthDrivers._nvdaPiperDriver import protocol


SESSION = 17


def envelope(messageType: protocol.MessageType, sequence: int, requestId: int, session: int = SESSION):
	return protocol.Envelope(protocol.PROTOCOL_VERSION, messageType, session, sequence, requestId)


def job(jobId: int = 1, generationId: int = 1, text: str = "private text") -> SpeechJob:
	return SpeechJob(jobId, generationId, jobId, (TextItem(text),), "mockVoice", 50)


def submit(sequence: int, requestId: int, submittedJob: SpeechJob | None = None, session: int = SESSION):
	submittedJob = submittedJob or job()
	return protocol.SubmitJobRequest(
		envelope(protocol.MessageType.SUBMIT_JOB_REQUEST, sequence, requestId, session),
		submittedJob.generationId,
		submittedJob.jobId,
		submittedJob,
	)


def exchange(worker: FakeWorker, request):
	return protocol.decodeMessage(worker.handleFrame(protocol.encodeMessage(request)))


class FakeWorkerTests(unittest.TestCase):
	def hello(self, worker: FakeWorker, requestId: int = 1):
		return exchange(worker, protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST, 1, requestId)))

	def assertError(self, response, code: protocol.ErrorCode) -> None:
		self.assertIsInstance(response, protocol.ErrorResponse)
		self.assertIs(code, response.error.code)

	def test_job_before_hello_requires_handshake_without_advancing(self) -> None:
		worker = FakeWorker()
		self.assertError(exchange(worker, submit(1, 1)), protocol.ErrorCode.HANDSHAKE_REQUIRED)
		response = self.hello(worker)
		self.assertIsInstance(response, protocol.HelloResponse)
		self.assertEqual(2, worker._nextSequenceNumber)

	def test_handshake_establishes_session_and_exact_capabilities(self) -> None:
		worker = FakeWorker()
		response = self.hello(worker)
		self.assertIsInstance(response, protocol.HelloResponse)
		self.assertEqual(SESSION, worker._sessionId)
		self.assertEqual(response.envelope.requestId, 1)
		self.assertEqual(response.envelope.sequenceNumber, 1)
		self.assertEqual(protocol.PROTOCOL_VERSION, response.capabilities.protocolVersion)
		self.assertEqual("NVDA Piper Driver Phase 2F fake worker", response.capabilities.workerIdentity)
		self.assertTrue(response.capabilities.acceptsSpeechJobs)
		for fieldName in ("synthesis", "audio", "cancellation", "pause", "models", "streaming", "notifications"):
			self.assertIs(getattr(response.capabilities, fieldName), False)
		with self.assertRaises(FrozenInstanceError):
			response.capabilities.audio = True

	def test_duplicate_hello_and_wrong_session_do_not_advance(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		duplicate = exchange(worker, protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST, 2, 2)))
		self.assertError(duplicate, protocol.ErrorCode.DUPLICATE_HANDSHAKE)
		wrongSession = exchange(worker, submit(2, 2, session=SESSION + 1))
		self.assertError(wrongSession, protocol.ErrorCode.WRONG_SESSION)
		accepted = exchange(worker, submit(2, 2))
		self.assertIsInstance(accepted, protocol.JobAcceptedResponse)

	def test_strict_sequence_and_rejections_do_not_advance(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		for sequence in (1, 3, 4):
			response = exchange(worker, submit(sequence, 20 + sequence))
			self.assertError(response, protocol.ErrorCode.INVALID_SEQUENCE)
			self.assertEqual(2, worker._nextSequenceNumber)
		accepted = exchange(worker, submit(2, 2))
		self.assertIsInstance(accepted, protocol.JobAcceptedResponse)
		self.assertEqual(3, worker._nextSequenceNumber)

	def test_malformed_decode_does_not_mutate_state(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		before = {key: value.copy() if type(value) is set else value for key, value in worker.__dict__.items()}
		with self.assertRaises(protocol.ProtocolException):
			worker.handleFrame(b"{")
		self.assertEqual(before, worker.__dict__)

	def test_valid_job_is_correlated_not_mutated_or_retained(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		private = "PRIVATE_WORKER_TEXT"
		submittedJob = job(jobId=4, generationId=9, text=private)
		before = submittedJob
		response = exchange(worker, submit(2, 2, submittedJob))
		self.assertEqual(before, submittedJob)
		self.assertIsInstance(response, protocol.JobAcceptedResponse)
		self.assertEqual((2, 2, 9, 4), (response.envelope.sequenceNumber, response.envelope.requestId, response.generationId, response.jobId))
		self.assertEqual({1, 2}, worker._acceptedRequestIds)
		self.assertEqual({4}, worker._acceptedJobIds)
		self.assertNotIn(private, repr(worker.__dict__))
		self.assertFalse(any(isinstance(value, SpeechJob) for value in worker.__dict__.values()))

	def test_duplicate_request_and_job_are_rejected_without_advancing(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, job(1))), protocol.JobAcceptedResponse)
		self.assertError(exchange(worker, submit(3, 2, job(2))), protocol.ErrorCode.DUPLICATE_REQUEST)
		self.assertEqual(3, worker._nextSequenceNumber)
		self.assertError(exchange(worker, submit(3, 3, job(1))), protocol.ErrorCode.DUPLICATE_JOB)
		self.assertEqual(3, worker._nextSequenceNumber)
		self.assertIsInstance(exchange(worker, submit(3, 3, job(2))), protocol.JobAcceptedResponse)

	def test_state_error_messages_do_not_contain_job_text(self) -> None:
		worker = FakeWorker()
		private = "PRIVATE_WORKER_TEXT"
		response = exchange(worker, submit(1, 1, job(text=private)))
		self.assertError(response, protocol.ErrorCode.HANDSHAKE_REQUIRED)
		self.assertNotIn(private, response.error.message)
		self.assertNotIn(private, repr(response))

	def test_shutdown_is_irreversible_and_repeated_shutdown_fails(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		private = "PRIVATE_SHUTDOWN_TEXT"
		self.assertIsInstance(exchange(worker, submit(2, 2, job(text=private))), protocol.JobAcceptedResponse)
		shutdown = protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST, 3, 3))
		response = exchange(worker, shutdown)
		self.assertIsInstance(response, protocol.ShutdownResponse)
		self.assertTrue(worker._isShutDown)
		self.assertNotIn(private, repr(worker.__dict__))
		self.assertNotIn(private, repr(response))
		repeated = protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST, 4, 4))
		self.assertError(exchange(worker, repeated), protocol.ErrorCode.WORKER_SHUT_DOWN)
		self.assertError(exchange(worker, submit(4, 4)), protocol.ErrorCode.WORKER_SHUT_DOWN)
		self.assertEqual(4, worker._nextSequenceNumber)

	def test_response_message_is_not_accepted_as_request(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		responseMessage = protocol.ShutdownResponse(envelope(protocol.MessageType.SHUTDOWN_RESPONSE, 2, 2))
		self.assertError(exchange(worker, responseMessage), protocol.ErrorCode.UNKNOWN_MESSAGE_TYPE)
		self.assertEqual(2, worker._nextSequenceNumber)

	def test_controlled_internal_error_does_not_advance_state(self) -> None:
		class FailingFakeWorker(FakeWorker):
			def _accept(self, request):
				raise RuntimeError("private internal detail")
		worker = FailingFakeWorker()
		response = self.hello(worker)
		self.assertError(response, protocol.ErrorCode.INTERNAL_FAKE_WORKER_ERROR)
		self.assertNotIn("private internal detail", response.error.message)
		self.assertIsNone(worker._sessionId)
		self.assertEqual(1, worker._nextSequenceNumber)
		self.assertEqual(set(), worker._acceptedRequestIds)

	def test_protocol_modules_have_no_out_of_scope_imports(self) -> None:
		root = Path(__file__).resolve().parents[1]
		modulePaths = (
			root / "addon" / "synthDrivers" / "_nvdaPiperDriver" / "protocol.py",
			root / "addon" / "synthDrivers" / "_nvdaPiperDriver" / "fakeWorker.py",
		)
		forbiddenRoots = {
			"asyncio", "audio", "ctypes", "http", "multiprocessing", "onnxruntime",
			"os", "pathlib", "piper", "queue", "requests", "socket", "subprocess",
			"threading", "urllib",
		}
		for modulePath in modulePaths:
			tree = ast.parse(modulePath.read_text(encoding="utf-8"), filename=str(modulePath))
			imports = set()
			for node in ast.walk(tree):
				if isinstance(node, ast.Import):
					imports.update(alias.name.split(".", 1)[0] for alias in node.names)
				elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
					imports.add(node.module.split(".", 1)[0])
			self.assertFalse(imports & forbiddenRoots, modulePath.name)


if __name__ == "__main__":
	unittest.main()
