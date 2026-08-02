"""Deterministic Phase 2G generation, cancellation, and fake-result tests."""

from dataclasses import FrozenInstanceError
import unittest

from addon.synthDrivers._nvdaPiperDriver import protocol
from addon.synthDrivers._nvdaPiperDriver.fakeWorker import FakeWorker
from addon.synthDrivers._nvdaPiperDriver.jobs import SpeechJob, TextItem


SESSION = 29


def envelope(messageType: protocol.MessageType, sequence: int, requestId: int, session: int = SESSION) -> protocol.Envelope:
	return protocol.Envelope(protocol.PROTOCOL_VERSION, messageType, session, sequence, requestId)


def job(jobId: int, generationId: int, text: str = "private generation text") -> SpeechJob:
	return SpeechJob(jobId, generationId, jobId, (TextItem(text),), "mockVoice", 50)


def submit(sequence: int, requestId: int, jobId: int, generationId: int, *, session: int = SESSION) -> protocol.SubmitJobRequest:
	speechJob = job(jobId, generationId)
	return protocol.SubmitJobRequest(
		envelope(protocol.MessageType.SUBMIT_JOB_REQUEST, sequence, requestId, session),
		generationId,
		jobId,
		speechJob,
	)


def cancel(sequence: int, requestId: int, generationId: int, *, session: int = SESSION) -> protocol.CancelGenerationRequest:
	return protocol.CancelGenerationRequest(
		envelope(protocol.MessageType.CANCEL_GENERATION_REQUEST, sequence, requestId, session),
		generationId,
	)


def fakeResult(
	sequence: int,
	requestId: int,
	generationId: int,
	jobId: int,
	resultId: int,
	*,
	session: int = SESSION,
) -> protocol.FakeResultRequest:
	return protocol.FakeResultRequest(
		envelope(protocol.MessageType.FAKE_RESULT_REQUEST, sequence, requestId, session),
		generationId,
		jobId,
		resultId,
	)


def exchange(worker: FakeWorker, request: protocol.ProtocolMessage) -> protocol.ProtocolMessage:
	return protocol.decodeMessage(worker.handleFrame(protocol.encodeMessage(request)))


class GenerationCancellationTests(unittest.TestCase):
	def hello(self, worker: FakeWorker) -> protocol.HelloResponse:
		response = exchange(worker, protocol.HelloRequest(envelope(protocol.MessageType.HELLO_REQUEST, 1, 1)))
		self.assertIsInstance(response, protocol.HelloResponse)
		return response

	def assertError(self, response: protocol.ProtocolMessage, code: protocol.ErrorCode) -> None:
		self.assertIsInstance(response, protocol.ErrorResponse)
		self.assertIs(code, response.error.code)

	def assertResult(self, response: protocol.ProtocolMessage, status: protocol.FakeResultStatus) -> None:
		self.assertIsInstance(response, protocol.FakeResultResponse)
		self.assertIs(status, response.status)

	def test_new_protocol_values_are_immutable(self) -> None:
		values = (
			cancel(2, 2, 1),
			protocol.CancelGenerationResponse(envelope(protocol.MessageType.CANCEL_GENERATION_RESPONSE, 2, 2), 1, True),
			fakeResult(2, 2, 1, 1, 1),
			protocol.FakeResultResponse(
				envelope(protocol.MessageType.FAKE_RESULT_RESPONSE, 2, 2), 1, 1, 1, protocol.FakeResultStatus.ACCEPTED_CURRENT,
			),
		)
		for value in values:
			with self.subTest(valueType=type(value)), self.assertRaises(FrozenInstanceError):
				value.envelope = value.envelope

	def test_generation_progression_is_contiguous_and_rejections_are_atomic(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertError(exchange(worker, submit(2, 2, 1, 2)), protocol.ErrorCode.GENERATION_OUT_OF_ORDER)
		self.assertIsNone(worker._activeGenerationId)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		self.assertIsInstance(exchange(worker, submit(3, 3, 2, 1)), protocol.JobAcceptedResponse)
		before = self._stateCopy(worker)
		self.assertError(exchange(worker, submit(4, 4, 3, 3)), protocol.ErrorCode.GENERATION_OUT_OF_ORDER)
		self.assertEqual(before, worker.__dict__)
		self.assertIsInstance(exchange(worker, submit(4, 4, 3, 2)), protocol.JobAcceptedResponse)
		self.assertError(exchange(worker, submit(5, 5, 4, 1)), protocol.ErrorCode.GENERATION_STALE)
		self.assertEqual(5, worker._nextSequenceNumber)

	def test_cancellation_is_correlated_idempotent_and_non_mutating(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		speechJob = job(1, 1, "PRIVATE_CANCEL_TEXT")
		request = protocol.SubmitJobRequest(envelope(protocol.MessageType.SUBMIT_JOB_REQUEST, 2, 2), 1, 1, speechJob)
		self.assertIsInstance(exchange(worker, request), protocol.JobAcceptedResponse)
		response = exchange(worker, cancel(3, 3, 1))
		self.assertIsInstance(response, protocol.CancelGenerationResponse)
		self.assertEqual((3, 3, 1, True), (response.envelope.sequenceNumber, response.envelope.requestId, response.generationId, response.changedState))
		self.assertEqual(job(1, 1, "PRIVATE_CANCEL_TEXT"), speechJob)
		repeated = exchange(worker, cancel(4, 4, 1))
		self.assertIsInstance(repeated, protocol.CancelGenerationResponse)
		self.assertFalse(repeated.changedState)
		self.assertError(exchange(worker, submit(5, 5, 2, 1)), protocol.ErrorCode.GENERATION_CANCELLED)
		self.assertError(exchange(worker, cancel(5, 5, 2)), protocol.ErrorCode.GENERATION_UNKNOWN)
		self.assertEqual(5, worker._nextSequenceNumber)
		self.assertIsInstance(exchange(worker, submit(5, 5, 2, 2)), protocol.JobAcceptedResponse)
		older = exchange(worker, cancel(6, 6, 1))
		self.assertIsInstance(older, protocol.CancelGenerationResponse)
		self.assertFalse(older.changedState)

	def test_wrong_session_sequence_and_malformed_cancel_do_not_mutate_state(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		for request in (cancel(3, 3, 1, session=SESSION + 1), cancel(4, 4, 1)):
			before = self._stateCopy(worker)
			response = exchange(worker, request)
			self.assertError(
				response,
				protocol.ErrorCode.WRONG_SESSION if request.envelope.sessionId != SESSION else protocol.ErrorCode.INVALID_SEQUENCE,
			)
			self.assertEqual(before, worker.__dict__)
		before = self._stateCopy(worker)
		with self.assertRaises(protocol.ProtocolException):
			worker.handleFrame(b'{"messageType":"cancelGenerationRequest"}')
		self.assertEqual(before, worker.__dict__)

	def test_fake_results_are_metadata_only_and_have_stable_statuses(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		accepted = exchange(worker, fakeResult(3, 3, 1, 1, 1))
		self.assertResult(accepted, protocol.FakeResultStatus.ACCEPTED_CURRENT)
		self.assertEqual((3, 3, 1, 1, 1), (
			accepted.envelope.sequenceNumber, accepted.envelope.requestId, accepted.generationId, accepted.jobId, accepted.resultId,
		))
		self.assertResult(exchange(worker, fakeResult(4, 4, 1, 1, 1)), protocol.FakeResultStatus.DUPLICATE)
		self.assertResult(exchange(worker, fakeResult(5, 5, 1, 999, 1)), protocol.FakeResultStatus.UNKNOWN_JOB)
		self.assertIsInstance(exchange(worker, submit(6, 6, 2, 2)), protocol.JobAcceptedResponse)
		self.assertResult(exchange(worker, fakeResult(7, 7, 1, 1, 2)), protocol.FakeResultStatus.STALE_GENERATION)
		self.assertIsInstance(exchange(worker, cancel(8, 8, 2)), protocol.CancelGenerationResponse)
		self.assertResult(exchange(worker, fakeResult(9, 9, 2, 2, 1)), protocol.FakeResultStatus.CANCELLED_GENERATION)
		self.assertEqual({(1, 1)}, worker._acceptedResults)

	def test_tracking_limits_fail_without_partial_mutation(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		sequence = 2
		for jobId in range(1, protocol.MAX_TRACKED_JOBS + 1):
			self.assertIsInstance(exchange(worker, submit(sequence, sequence, jobId, 1)), protocol.JobAcceptedResponse)
			sequence += 1
		before = self._stateCopy(worker)
		self.assertError(
			exchange(worker, submit(sequence, sequence, protocol.MAX_TRACKED_JOBS + 1, 1)),
			protocol.ErrorCode.TRACKING_LIMIT_EXCEEDED,
		)
		self.assertEqual(before, worker.__dict__)

		worker = FakeWorker()
		self.hello(worker)
		sequence = 2
		for generationId in range(1, protocol.MAX_TRACKED_GENERATIONS + 1):
			self.assertIsInstance(exchange(worker, submit(sequence, sequence, generationId, generationId)), protocol.JobAcceptedResponse)
			sequence += 1
		before = self._stateCopy(worker)
		self.assertError(
			exchange(worker, submit(sequence, sequence, protocol.MAX_TRACKED_GENERATIONS + 1, protocol.MAX_TRACKED_GENERATIONS + 1)),
			protocol.ErrorCode.TRACKING_LIMIT_EXCEEDED,
		)
		self.assertEqual(before, worker.__dict__)

	def test_result_and_cancelled_generation_limits_are_bounded(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		sequence = 3
		for resultId in range(1, protocol.MAX_TRACKED_RESULTS + 1):
			self.assertResult(exchange(worker, fakeResult(sequence, sequence, 1, 1, resultId)), protocol.FakeResultStatus.ACCEPTED_CURRENT)
			sequence += 1
		before = self._stateCopy(worker)
		self.assertError(exchange(worker, fakeResult(sequence, sequence, 1, 1, protocol.MAX_TRACKED_RESULTS + 1)), protocol.ErrorCode.TRACKING_LIMIT_EXCEEDED)
		self.assertEqual(before, worker.__dict__)

		worker = FakeWorker()
		self.hello(worker)
		sequence = 2
		for generationId in range(1, protocol.MAX_CANCELLED_GENERATIONS + 1):
			self.assertIsInstance(exchange(worker, submit(sequence, sequence, generationId, generationId)), protocol.JobAcceptedResponse)
			sequence += 1
			self.assertTrue(exchange(worker, cancel(sequence, sequence, generationId)).changedState)
			sequence += 1
		generationId = protocol.MAX_CANCELLED_GENERATIONS + 1
		self.assertIsInstance(exchange(worker, submit(sequence, sequence, generationId, generationId)), protocol.JobAcceptedResponse)
		sequence += 1
		before = self._stateCopy(worker)
		self.assertError(exchange(worker, cancel(sequence, sequence, generationId)), protocol.ErrorCode.TRACKING_LIMIT_EXCEEDED)
		self.assertEqual(before, worker.__dict__)

	def test_request_tracking_limit_is_bounded_and_atomic(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		self.assertResult(exchange(worker, fakeResult(3, 3, 1, 1, 1)), protocol.FakeResultStatus.ACCEPTED_CURRENT)
		sequence = 4
		while len(worker._acceptedRequestIds) < protocol.MAX_TRACKED_REQUESTS - 1:
			self.assertResult(exchange(worker, fakeResult(sequence, sequence, 1, 1, 1)), protocol.FakeResultStatus.DUPLICATE)
			sequence += 1
		before = self._stateCopy(worker)
		self.assertError(exchange(worker, fakeResult(sequence, sequence, 1, 1, 1)), protocol.ErrorCode.TRACKING_LIMIT_EXCEEDED)
		self.assertEqual(before, worker.__dict__)
		shutdown = protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST, sequence, sequence))
		self.assertIsInstance(exchange(worker, shutdown), protocol.ShutdownResponse)
		self.assertEqual(protocol.MAX_TRACKED_REQUESTS, len(worker._acceptedRequestIds))

	def test_deterministic_stress_keeps_all_collections_bounded_and_private(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		sequence = 2
		for generationId in range(1, protocol.MAX_TRACKED_GENERATIONS + 1):
			self.assertIsInstance(exchange(worker, submit(sequence, sequence, generationId, generationId)), protocol.JobAcceptedResponse)
			sequence += 1
			if generationId <= protocol.MAX_CANCELLED_GENERATIONS:
				self.assertIsInstance(exchange(worker, cancel(sequence, sequence, generationId)), protocol.CancelGenerationResponse)
				sequence += 1
		self.assertResult(
			exchange(worker, fakeResult(sequence, sequence, protocol.MAX_TRACKED_GENERATIONS, protocol.MAX_TRACKED_GENERATIONS, 1)),
			protocol.FakeResultStatus.ACCEPTED_CURRENT,
		)
		sequence += 1
		for resultId in range(2, 302):
			self.assertResult(
				exchange(worker, fakeResult(sequence, sequence, 1, 1, resultId)),
				protocol.FakeResultStatus.CANCELLED_GENERATION,
			)
			sequence += 1
		for _ in range(300):
			self.assertResult(
				exchange(worker, fakeResult(sequence, sequence, protocol.MAX_TRACKED_GENERATIONS, protocol.MAX_TRACKED_GENERATIONS, 1)),
				protocol.FakeResultStatus.DUPLICATE,
			)
			sequence += 1
		self.assertLessEqual(len(worker._acceptedRequestIds), protocol.MAX_TRACKED_REQUESTS)
		self.assertLessEqual(len(worker._trackedGenerations), protocol.MAX_TRACKED_GENERATIONS)
		self.assertLessEqual(len(worker._acceptedJobs), protocol.MAX_TRACKED_JOBS)
		self.assertLessEqual(len(worker._acceptedResults), protocol.MAX_TRACKED_RESULTS)
		self.assertLessEqual(len(worker._cancelledGenerations), protocol.MAX_CANCELLED_GENERATIONS)
		self.assertNotIn("private generation text", repr(worker.__dict__))
		self.assertFalse(any(isinstance(value, SpeechJob) for value in worker.__dict__.values()))

	def test_shutdown_after_cancel_is_irreversible_and_private(self) -> None:
		worker = FakeWorker()
		self.hello(worker)
		self.assertIsInstance(exchange(worker, submit(2, 2, 1, 1)), protocol.JobAcceptedResponse)
		self.assertTrue(exchange(worker, cancel(3, 3, 1)).changedState)
		shutdown = protocol.ShutdownRequest(envelope(protocol.MessageType.SHUTDOWN_REQUEST, 4, 4))
		self.assertIsInstance(exchange(worker, shutdown), protocol.ShutdownResponse)
		self.assertError(exchange(worker, cancel(5, 5, 1)), protocol.ErrorCode.WORKER_SHUT_DOWN)
		self.assertError(exchange(worker, fakeResult(5, 5, 1, 1, 1)), protocol.ErrorCode.WORKER_SHUT_DOWN)
		self.assertNotIn("private generation text", repr(worker.__dict__))

	@staticmethod
	def _stateCopy(worker: FakeWorker) -> dict[str, object]:
		return {
			key: value.copy() if type(value) in (set, dict) else value
			for key, value in worker.__dict__.items()
		}


if __name__ == "__main__":
	unittest.main()
