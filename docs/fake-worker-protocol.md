# Phase 2F fake-worker protocol

## Purpose and boundary

Phase 2F implements a bounded protocol model and deterministic fake worker in one Python process. The fake worker is a synchronous state-machine test double, not an operating-system worker, IPC transport, Piper abstraction, or architecture acceptance result. It creates no subprocess, thread, queue, pipe, socket, shared memory, model, PCM, audio, or notification. `SynthDriver.speak()` remains disconnected and no speech is produced.

The implementation consists of `synthDrivers/_nvdaPiperDriver/protocol.py` and `fakeWorker.py`. The underscore package remains excluded from NVDA synth discovery by pinned `synthDriverHandler.getSynthList`.

## Serialization decision

| Format | Decision | Reason |
|---|---|---|
| Strict UTF-8 JSON | Selected | Standard-library support, explicit inspectable schemas, deterministic compact encoding, and straightforward malformed-input tests. |
| Small custom binary format | Rejected for Phase 2F | Adds parser/framing complexity before message semantics are proven. |
| Python-specific serialization | Rejected | `pickle` and similar object reconstruction formats create executable/deserialization risk and couple the wire representation to Python classes. |

Python's `json` documentation states that the decoder accepts non-standard `NaN` and infinities by default and provides `object_pairs_hook` and `parse_constant` hooks. The prototype uses those hooks to reject duplicate keys and named non-finite values, recursively rejects overflow-created infinity, sets `allow_nan=False`, uses `ensure_ascii=False`, compact separators and sorted keys, and constructs every protocol object through explicit schema code. See [Python `json` documentation](https://docs.python.org/3.12/library/json.html), accessed 2026-08-01.

The frame is one complete UTF-8 JSON document represented by `bytes`. BOM, invalid UTF-8, comments, trailing data, duplicate keys, non-finite numbers, unknown fields, and implicit defaults are rejected. No object hook imports or constructs a class named by input.

## Version and envelope

Protocol version is the exact integer `1`. It appears in every message and capability set. Any other value fails with `unsupportedProtocolVersion`; there is no downgrade. Compatibility policy is provisional until a real transport exists.

Every immutable message owns an immutable envelope:

- `protocolVersion`;
- `messageType`;
- positive `sessionId`;
- positive `sequenceNumber`;
- positive `requestId`.

Identifiers are exact integers, excluding `bool`, bounded to `1..2^63-1`, contain no text/time/randomness, and have no cross-process guarantee. Submit messages additionally contain positive `generationId` and `jobId`, which must equal the embedded immutable job.

## Message flow

| Request | Successful response | Payload |
|---|---|---|
| `HelloRequest` | `HelloResponse` | Empty request; response has fixed capabilities. |
| `SubmitJobRequest` | `JobAcceptedResponse` | Generation ID, job ID, and explicitly serialized `SpeechJob`; response repeats IDs. |
| `ShutdownRequest` | `ShutdownResponse` | Empty payload. |

`ErrorResponse` correlates the rejected valid request by session, sequence, and request ID. Response envelope sequence numbers mirror requests; no asynchronous response ordering exists.

No load/unload, synthesis completion, PCM, index event, pause, resume, cancellation, health, heartbeat, warning, restart, streaming, or notification message exists.

## Session and sequence state

A `FakeWorker` starts with no session and expects sequence `1`.

1. Only `HelloRequest` is accepted before initialization.
2. A valid hello with sequence 1 establishes its supplied deterministic session ID and advances the next sequence to 2.
3. Duplicate hello, wrong session, duplicate accepted request ID, duplicate accepted job ID, stale/duplicate sequence, and skipped sequence return stable `ErrorResponse` values.
4. State-level rejection does not advance sequence or record an ID.
5. A successful request records only its numeric request/job metadata and advances exactly once.
6. Successful shutdown closes the instance irreversibly. Repeated shutdown and every later request return `workerShutDown`; there is no restart.

Malformed frames and schema failures raise `ProtocolException` before fake-worker state is inspected or mutated. This cleanly separates framing/schema failure from a valid request rejected by worker state.

## Capabilities

`HelloResponse` contains a fixed frozen `Capabilities` record with ten fields, the maximum allowed in Phase 2F:

- protocol version 1;
- identity `NVDA Piper Driver Phase 2F fake worker`;
- accepts immutable speech jobs: true;
- synthesis, audio, cancellation, pause, models, streaming, and notifications: false.

These flags describe only what the fake accepts structurally. Job acceptance does not imply execution or support for the job's commands.

## Job wire schema and behavior

Each item has an explicit `type` discriminator and exact field allowlist: text, index, character mode, language, break, rate, pitch, volume, or phoneme. `None` is JSON `null` and remains distinct from an empty string. Unicode strings are encoded without normalization. Prosody retains kind, signed offset, numeric multiplier, and reset/default flag; derived NVDA prosody properties are not invoked.

The fake worker validates and accepts a fully decoded immutable job, returns `JobAcceptedResponse`, and retains only accepted numeric request/job IDs. It does not mutate or retain the job, text, IPA, fallback text, item records, or encoded frame. It does not queue, synthesize, complete, or emit indexes.

## Provisional limits

These conservative test constants are centralized in `protocol.py`; they are not measured release requirements:

| Limit | Phase 2F value | Rationale |
|---|---:|---|
| Encoded frame | 65,536 bytes | Small enough for deterministic parser tests while allowing representative Unicode jobs. Checked before decoding. |
| Nesting depth | 8 | Covers the fixed envelope/job/item schema with limited surplus. Enforced after bounded decode. |
| Job items | 64 | Exercises mixed sequences without accepting unbounded arrays. |
| Text per item | 4,096 code points | Supports representative utterances while bounding individual strings. |
| Total job text/fallback | 16,384 code points | Bounds accumulated text independently of item count. |
| IPA | 1,024 code points | Allows test phonemes without unbounded specialized text. |
| Phoneme fallback | 4,096 code points | Matches ordinary text-item bound. |
| Language | 64 code points | Sufficient for locale tags used in tests. |
| Voice ID | 128 code points | Sufficient for stable internal identifiers. |
| Capability fields | 10 | Exact fixed Phase 2F capability schema. |
| Error message | 160 code points | Keeps returned diagnostics concise and non-content-bearing. |
| Numeric identifiers | `1..2^63-1` | Matches Phase 2E positive identifier bound. |

JSON parsing necessarily allocates within the already accepted 64 KiB frame before depth/schema validation. A real framed transport must validate its length prefix before allocating the payload and must benchmark appropriate limits.

## Error taxonomy

`ProtocolError` is a frozen record with a stable `ErrorCode` and bounded message hidden from generated representations. Codes distinguish malformed/oversized frames, encoding/JSON/duplicate-key errors, unknown type/version, missing/unknown fields, invalid types/values, wrong session, required/duplicate handshake, invalid sequence, duplicate request/job, shut down state, unsupported item, job-size limit, and internal fake-worker failure.

Decoder and schema errors raise `ProtocolException`; valid request envelopes rejected by fake-worker state return encoded `ErrorResponse`. Messages contain no job text, frame content, environment information, paths, or object representations.

## Privacy and verification

Text-bearing job/request/error fields are protected from generated representations where applicable. Encoding necessarily produces caller-requested text bytes, but neither codec nor fake worker logs, hashes, persists, or globally stores them. Fake-worker state contains only session/sequence flags, fixed capabilities, and sets of accepted numeric request/job IDs.

Tests cover frozen records, all message/item round trips, deterministic UTF-8, Persian and mixed Unicode, `None`/empty distinctions, duplicate keys, BOM, invalid encoding/JSON, trailing data, non-finite numbers, strict fields/types/ranges, depth and size limits, handshake/session/sequence behavior, duplicate detection, correlation, no job mutation/retention, shutdown, redacted representations, and forbidden imports.

## Known limitations and replacement path

- No real transport, process boundary, framing prefix, timeout, crash isolation, or OS access control has been tested.
- JSON memory behavior is bounded only by the pre-decode frame size in this prototype.
- Generation IDs are correlation data only; Phase 2G must define cancellation/stale-generation semantics.
- Request/job metadata sets grow until shutdown and need a measured bound or eviction rule before long-running use.
- Private Phase 2E prosody storage remains pinned-version-sensitive.
- The runtime ADR remains **Proposed**.

Phase 2G may add mock cancellation and stale-generation behavior around fake protocol/audio test doubles, but must not reinterpret Phase 2F as real IPC or begin Piper, ONNX Runtime, model, PCM, or production audio integration.
