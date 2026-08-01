# Proposed worker protocol

## Status and boundary

The worker is Proposed and benchmark-dependent. NVDA owns one child process; the child never listens on a network interface, launches commands, accesses arbitrary paths, or outlives its parent intentionally. Native runtime/model parsing occurs behind this crash boundary, but the worker is not trusted to send well-formed data.

## Transport and framing

Provisional transport is inherited anonymous pipes or a user-restricted named pipe, with separate control/event flow if backpressure experiments require it. Each frame has a fixed-size length prefix followed by UTF-8 JSON control data; PCM is either a bounded binary frame with a small validated header or base64-free binary payload. JSON was selected for prototype inspectability, not final efficiency. Python's JSON documentation warns that malicious input can consume resources, so length is validated before parsing ([Python JSON](https://docs.python.org/3/library/json.html), accessed 2026-08-01).

Common envelope: `protocolMajor`, `protocolMinor`, random per-launch `sessionId`, `messageType`, `messageId`, optional `replyTo`, `generationId`, `jobId`, `sequenceNumber`, and typed `payload`. Unknown fields may be ignored only within a compatible minor version; missing/invalid required fields fail the session.

## Startup and negotiation

1. Parent creates restricted pipes, random session ID, process/job containment, and starts the executable with a fixed argument list (`shell=False`; no interpolation).
2. Worker sends `hello`: protocol range, worker/runtime versions, architecture, build digest.
3. Parent verifies identity/version and replies with its supported protocol range and limits.
4. Worker sends `capabilities`: model formats/opsets, commands, PCM formats, cancellation/pause/streaming abilities, maximums.
5. Parent selects the intersection or shuts down with `protocolMismatch`.
6. Only then may model commands be sent. Startup has a measured timeout; silence is not treated as success.

## Commands and events

| Type | Direction | Required behavior |
|---|---|---|
| `hello`, `capabilities` | both/worker | Handshake/version/capability negotiation. |
| `loadModel` | parent → worker | Validated canonical approved-root path, expected digests, metadata; atomic success/failure. |
| `unloadModel` | parent → worker | Reject while active unless generation already cancelled. |
| `synthesize` | parent → worker | One immutable bounded job; no filesystem command/string. |
| `cancelGeneration` | parent → worker | Idempotently stop queued/current work and acknowledge idle status. |
| `pause`, `resume` | parent → worker | Capability-gated; primarily controls production/backpressure, not NVDA audio ownership. |
| `audioChunk` | worker → parent | PCM metadata, bounded bytes, ordered sequence, optional index offsets. |
| `indexEvent` | worker → parent | Synthesis-derived timing only; parent delays NVDA notification to playback position. |
| `jobCompleted` | worker → parent | Inference ended; not NVDA done speaking. |
| `jobFailed` | worker → parent | Structured safe error object. |
| `runtimeWarning` | worker → parent | Nonfatal code, never text echo. |
| `healthStatus` | worker → parent | Explicit response to health request or progress watchdog evidence. |
| `shutdown` / `shutdownComplete` | parent/worker | Stop accepting work, release model, close protocol. |

Error objects contain stable code, severity, retry hint, component, safe numeric/context fields, and optional upstream exception class—not user text, raw model metadata, stack trace, or arbitrary path. Full technical exceptions remain worker-local with redaction.

## Limits and timing

All numeric limits are configuration-independent safety constants chosen after prototype measurements: maximum frame/control/text/audio-chunk size, maximum segments/indexes/jobs, queue bytes, model path length, and total job text. Until measured, tests use deliberately small experimental limits and assert clean rejection. Queue default is one active plus a small bounded pending set; NVDA cancellation replaces obsolete work.

Use event-progress deadlines, not constant heartbeats during healthy active traffic. When idle, an infrequent parent health request may distinguish a hung worker from inactivity if experiments justify it. Startup, load, inference-progress, cancel-ack, and shutdown have separate measured timeouts. No timeout blocks NVDA's main thread.

## Audio-placement comparison

| Approach | Latency/cancel/index | Isolation/device behavior | Security/cleanup/testing/package |
|---|---|---|---|
| Stream PCM over IPC to NVDA | Extra copies; earliest chunks and immediate parent stop; parent can align feed callbacks | Inference isolated; NVDA owns selected audio device | Bounded parser/buffers; no temp files; deterministic fake-worker tests; worker still packaged |
| Temporary WAV files | Must wait or tail; cancellation/index alignment poor | Inference isolated; parent plays file | Private temp lifecycle/leak/path risk; simple inspection but cleanup/update burden |
| Shared memory | Lowest-copy potential; complex ownership/cancel/index ring | Inference isolated; parent owns device | ACL, stale mapping, bounds and cleanup complexity; harder tests; no proven need |
| Worker generates and plays | Potentially direct; cancellation local; index callbacks cross IPC | Audio faults isolated too, but bypasses NVDA audio policy/device integration | Worker gains device authority and complex testing; packaging similar |
| Worker generates, parent plays complete PCM | Simple but first audio waits for full inference | Parent device behavior; inference isolated | Large memory/messages; weak navigation latency |

Provisional choice: stream bounded PCM from worker and play in NVDA using a verified current audio path. It best separates inference from NVDA audio policy and supports early playback/cancellation. Confirm by comparing first-audible latency, cancel-to-silence, CPU/memory/copies, index accuracy, device changes, and fault handling against complete-buffer and worker-playback prototypes. Shared memory and files are rejected for the first prototype, not permanently.

## Hardening

- Validate length prefix before allocation and schema/types/enums before use; close on framing desynchronization or repeated malformed data.
- Never use shell commands, executable message fields, dynamic imports, pickle, or object deserialization.
- Canonicalize parent-side model paths; require regular `.onnx`/`.json` pairs beneath configured roots; worker rechecks. No UNC/device paths, links/reparse escape, or arbitrary output path.
- Restrict named-pipe ACL to the current user/process context; inherited handles are non-inheritable except explicit endpoints. Session ID prevents accidental cross-session acceptance but is not a substitute for ACLs.
- Parent assigns process containment and closes/terminates child on NVDA exit. Worker monitors parent/pipe closure and exits. Bounded graceful shutdown precedes forced termination.
- Apply memory/CPU/queue limits where Windows facilities and runtime behavior permit; trip a circuit breaker on repeated crashes/hangs.

## Version policy

Major changes break framing/semantics and require exact supported-range intersection. Minor versions add optional fields/types; capabilities gate their use. Patch versions do not change wire behavior. Parent supports only documented adjacent versions during a migration window; no indefinite compatibility. Release tests cover current and oldest supported protocol. Unknown major or required capability fails closed with an actionable incompatibility error.
