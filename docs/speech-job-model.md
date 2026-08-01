# Speech-job model

> Phase 2E implements only the immutable conversion subset documented in `speech-job-conversion.md`: identity, ordered items, mock voice/rate snapshots, and strict failure behavior. Queueing, cancellation tokens, outcomes, timestamps, model identity, chunking, worker events, and completion remain proposed and unimplemented.

## Purpose

An immutable `SpeechJob` captures one accepted NVDA `SpeechSequence` without retaining mutable driver settings. Names below are conceptual data fields, not production APIs.

## Representation

| Field | Meaning and rule |
|---|---|
| `jobId` | Monotonic, process-session-local unsigned identifier; never reused. |
| `generationId` | Monotonic cancellation epoch. Every event must match the current generation. |
| `requestOrder` | Monotonic acceptance order for diagnostics/tests, not scheduling authority. |
| `segments` | Ordered immutable text/command sequence after validation; text may be chunked but not reordered. |
| `voiceId` / `modelDigest` | Stable selected voice identity and verified model/config digest snapshot. |
| `settings` | Immutable normalized rate/volume and supported runtime parameters. |
| `language` | Initial locale plus ordered language-change segments; never inferred solely from display name. |
| `indexes` | Ordered NVDA integer index markers attached to segment boundaries/audio offsets when known. |
| `cancelToken` | Controller-owned one-way flag associated with generation. Not serialized as executable state. |
| `createdMonotonic` | Monotonic timestamp for measurement; wall time is optional metadata. |
| `processingStatus` | created, queued, submitted, synthesizing, receiving, playing. |
| `outcome` | exactly one of completed, cancelled, failed; initially unset. |
| `failure` | Structured non-text-bearing error code and safe context when failed. |

Supported command records correspond only to advertised pinned `SynthCommand` types. Phase 2 initially represents `IndexCommand`; text and indexes are sufficient for mock integration. Later commands are explicit tagged records for language, break, character mode, rate, volume, pitch, or phoneme only after backend tests justify advertising them.

Unknown or unadvertised commands are not forwarded to the worker. A harmless unadvertised prosody command may be skipped with a rate-limited technical warning; a command whose removal could corrupt ordering/semantics fails conversion. `PhonemeCommand` uses validated IPA only if supported; otherwise its fallback `text` is inserted, or the command is skipped if no fallback exists. These policies must be tested per command before support is declared.

## Ordering and chunking

Conversion walks the sequence once. Adjacent text with identical effective parameters may merge. Indexes remain zero-width ordered boundaries. Chunking occurs only at safe text boundaries and carries the effective language/settings plus pending indexes into each chunk. No chunk begins by inheriting mutable state from a previous job. A partially synthesized job may play only current-generation chunks in sequence; later failure stops remaining audio and produces failed, never completed.

## Completion and cancellation rules

- The controller performs a compare-and-set from unset outcome to exactly one terminal outcome. Later terminal events are ignored and counted.
- `cancel()` atomically increments generation before clearing queues/stopping audio/sending worker cancellation. Repeated cancel in the same epoch is a no-op.
- Queue replacement invalidates all queued/active jobs in the old generation and creates new jobs only under the new generation.
- Empty jobs never reach inference. Their eventual NVDA notification policy is an explicit integration experiment.
- Synthesis completion, final PCM receipt, final PCM queueing, playback completion, and NVDA completion are separate milestones.

## Race prevention

Every worker/audio event carries or is associated with `sessionId`, generation, job, and monotonic sequence number. Validation occurs before buffer or notification mutation. Index records also have a delivery flag; delivery is allowed once, in order, when their associated audio feed completes. The completion gate requires current generation, completed playback, no pending current index, and unset terminal outcome.

A voice change starts a new generation and creates no job until the new model commit succeeds. Settings are copied at job creation. Thus late PCM/indexes, duplicate completion, cancelled indexes, model-switch races, and inherited old state all fail identity checks.

## Privacy

Normal logs contain session-safe opaque IDs, state, segment count, character count, durations, sizes, model digest prefix, and error code—not text, IPA, PCM, user paths, or full metadata. Diagnostic mode does not log text. A future explicit text-capture tool would require a separate design and consent; it is out of scope.

## Pseudocode-level behavior

**Convert:** validate sequence → snapshot model/settings → walk items in order → append text or supported tagged command → apply documented fallback → attach indexes → safely chunk → reject if bounds exceeded → return immutable job.

**Submit:** if state/model/generation valid and capacity available → reserve job ID/order → enqueue → send one synthesis envelope; otherwise produce one mapped failure without worker input.

**Handle event:** verify worker session → envelope/version/type/size → generation/job → sequence monotonicity → state-allowed event → mutate buffer/index gate; otherwise discard or fail protocol according to severity.

**Cancel:** advance generation → mark every old unset outcome cancelled → clear pending indexes/audio → stop player → send generation cancel → wait bounded acknowledgement asynchronously → restart worker only if timeout policy requires it.

**Complete:** worker completion marks synthesis only; final chunk receipt marks PCM complete; player callback/drain marks played; then atomically set completed and emit one `synthDoneSpeaking`.
