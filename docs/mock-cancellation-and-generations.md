# Phase 2G mock cancellation and generations

## Purpose and boundary

Phase 2G models cancellation and stale-generation invalidation only. It extends the immutable version-1 protocol and synchronous in-process fake worker from Phase 2F. Cancellation performs no work asynchronously and fake results are metadata-only test events. There is no operating-system worker, subprocess, IPC transport, thread, queue, delay, timer, Piper or ONNX Runtime integration, model, PCM, audio, synthesis, NVDA notification, or driver integration. `SynthDriver.speak()` remains disconnected and `SynthDriver.cancel()` is not implemented.

The runtime ADR remains **Proposed**. These tests demonstrate deterministic state rules, not production cancellation, audible interruption, performance, or process isolation.

## Generation model

Generation IDs are positive integers bounded to `1..2^63-1` and local to one fake-worker instance. They contain no time, randomness, or user content. Progression is contiguous and monotonic:

1. The first submitted job must use generation 1.
2. More jobs may use the active generation while it is not cancelled.
3. A new job may activate only `active generation + 1`; skipped generations fail with `generationOutOfOrder`.
4. Activating the next generation makes every older generation stale, whether or not it was explicitly cancelled.
5. A job for an older generation fails with `generationStale`, or `generationCancelled` if that generation was explicitly cancelled.
6. A cancelled active generation accepts no more jobs. Its immediate successor may still be activated.

The strict contiguous rule makes accidental gaps observable and allows bounded deterministic tests. It is provisional and has no cross-process meaning.

## Cancellation semantics and idempotency

`CancelGenerationRequest` contains only the standard envelope and a generation ID. A request for the active uncancelled generation records cancellation and returns `CancelGenerationResponse(changedState=true)`. Repeating it returns the same correlated response shape with `changedState=false`. A request for a known older generation also returns `false` because advancement has already made it stale. An unknown future generation fails with `generationUnknown`.

Successful and idempotent cancellation requests are accepted protocol operations: they record the numeric request ID and advance the request sequence exactly once. Wrong-session, wrong-sequence, malformed, unknown-future, tracking-limit, and post-shutdown requests do not mutate state or advance the sequence.

Cancellation does not mutate a `SpeechJob`, remove content, emit completion or indexes, stop audio, or perform cleanup because the fake worker never retains content and owns no execution or external resource.

## Fake-result simulation

`FakeResultRequest` is a test-only metadata envelope containing generation ID, job ID, and result ID. It never contains text, IPA, fallback text, indexes, completion data, audio metadata, PCM, or a synthesized result. `FakeResultResponse` returns one stable `FakeResultStatus`:

| Status | Meaning |
|---|---|
| `acceptedCurrent` | The job is known, its generation is active and uncancelled, and the result ID is new. |
| `staleGeneration` | The job is known but a newer generation is active. |
| `cancelledGeneration` | The job's generation was explicitly cancelled. |
| `unknownJob` | The job ID is unknown or does not belong to the supplied generation. |
| `duplicate` | The same result ID was already accepted for the current job. |

All five statuses are correlated protocol responses and advance the request sequence. Only `acceptedCurrent` records the numeric `(job ID, result ID)` pair. Rejected fake results are not retained, so repeated stale/cancelled/unknown deliveries remain classified by their underlying state. No status implies synthesis, playback, index delivery, or completion.

## Provisional tracking limits

All retained collections are bounded safety fixtures, not measured release limits:

| Metadata | Limit |
|---|---:|
| Accepted request IDs | 2,048 |
| Tracked generations | 64 |
| Job-to-generation mappings | 256 |
| Accepted fake-result identifiers | 512 |
| Explicitly cancelled generations | 32 |

The existing 65,536-byte frame and Phase 2F field limits remain unchanged. One request-ID slot is reserved for final shutdown; ordinary requests fail before consuming it. A limit failure returns `trackingLimitExceeded` without partial mutation or sequence advancement. Metadata is retained until shutdown; there is no eviction policy in this prototype.

## Errors, privacy, and retained state

Phase 2G adds `generationStale`, `generationCancelled`, `generationUnknown`, `generationOutOfOrder`, and `trackingLimitExceeded`. They remain bounded, deterministic, machine-readable, correlated, and free of user content, frames, environment details, and filesystem details. Decode/schema failures still raise project-owned `ProtocolException`; valid state rejections return `ErrorResponse`.

The fake worker retains only fixed capabilities, numeric session/sequence/request metadata, the active generation, sets of numeric generation/result identifiers, a numeric job-to-generation mapping, and Boolean shutdown state. It retains no frame, complete request, job, text, IPA, fallback text, serialized payload, audio, or model state. Generated representations of speech-bearing objects remain redacted.

## Stress and shutdown

Tests use deterministic synchronous loops without clocks, sleeps, timers, threads, or performance claims. They advance generations, cancel, redeliver stale results, redeliver duplicates, fill each collection to its limit, and verify atomic failure and collection bounds after hundreds or thousands of operations.

Shutdown still succeeds after cancellation. Every cancellation or fake-result request after shutdown returns `workerShutDown`; the instance cannot restart and exposes no prior job content.

## Replacement path

Phase 2H is the sole next milestone:

> Integrate and benchmark one verified Piper runtime for standalone synthesis outside NVDA, without connecting it to the NVDA driver.

Phase 2H must replace none of these metadata rules silently. Any real worker, transport, runtime cancellation, timing, PCM, audio, or NVDA integration requires its own bounded design and evidence.
