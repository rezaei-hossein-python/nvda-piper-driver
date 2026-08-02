# Driver state machine

> Phase 2I retains the existing initializing/ready/terminated driver lifecycle and adds one owned one-shot child plus `WavePlayer`. `cancel()` is teardown only: invalidate current PCM, stop playback, and terminate the child. The broader responsive state machine below remains a design target for Phase 2J and later.

> This document remains the proposed production model. Phase 2D implements only private `initializing`, `ready`, and `terminated` mock states, with none of the runtime meanings or resources described below. See `mock-lifecycle-and-settings.md`.

> Phase 2G validates only synchronous in-process generation and cancellation metadata in the fake worker. It does not implement this controller state machine, driver `cancel()`, audio stopping, timing, or NVDA notifications. The runtime ADR remains Proposed.

## Status and authority

This is a Proposed Phase 1C design, not an implemented API. NVDA obligations derive from `docs/nvda-synthdriver-research.md` and pinned symbols `synthDriverHandler.SynthDriver`, `SpeechManager`, and the built-in drivers. Runtime behavior remains benchmark-dependent.

## State ownership model

One serialized controller owns the state, active generation, active job, model identity, worker connection, and audio player. Public NVDA calls enqueue bounded controller actions and return promptly. Worker/audio callbacks never mutate state directly; they enqueue events. “Ready” means usable, not necessarily speaking.

| State | Entry and purpose | Allowed operations | Rejected/deferred operations | Resources and side effects | Recovery, UI, logging, shutdown |
|---|---|---|---|---|---|
| `unavailable` | Class `check()` finds a required packaged runtime absent/incompatible, or platform unsupported. Justified because discovery must fail safely before construction. | `check`; diagnostics that reveal no private paths. | Selection, load, speak. | None. | Driver is not selectable; log component/version category. Shutdown is a no-op. |
| `initializing` | Instance construction starts controller/audio/worker handshake. | `cancel`, `terminate`; queue at most one selected-model load after handshake. | `speak`, pause, settings requiring capabilities. | Partial controller, child/process handles. | Failure → recoverable or unavailable. User sees concise initialization error only when selected. Termination cancels startup and closes partial resources. |
| `readyWithoutModel` | Handshake succeeded but no valid selected model exists. Distinct because runtime is healthy and model repair is possible. | enumerate/import/select/load, settings not requiring a model, terminate. | synthesize/play/pause. | Live worker, no model/audio stream. | Missing-model guidance; metadata only in logs. Terminate → `terminating`. |
| `loadingModel` | Validated load request accepted. Model load is expensive/cancellable. | cancel, terminate; newer voice selection supersedes current load. | speak is rejected with recoverable “voice still loading” until experiments justify queueing; pause has no effect. | Worker plus candidate model; generation reserved. | Success → `ready`; failure → `readyWithoutModel` or recoverable failure while retaining previous model if worker guarantees atomic switch. |
| `ready` | Worker confirms a compatible model loaded and audio is available. | speak, settings/voice change, unload, terminate. | resume without pause. | Warm model, idle audio player. | Normal state; no announcement. |
| `synthesizing` | Current-generation job accepted; no playable PCM yet. | cancel, terminate; pause records requested playback pause; newer speak follows queue policy. | model mutation until cancellation boundary. | Active job/token, worker inference. | First accepted PCM → `playing`; completed without PCM → terminal outcome then `ready`; failure → recoverable/failed. |
| `playing` | Current-generation PCM has been accepted by audio. | cancel, pause, terminate, bounded continuation chunks. | voice/model mutation without cancelling current generation. | Worker job, ordered PCM buffer/player, pending indexes. | Final played → `ready` and one done notification. Device loss → recoverable failure. |
| `paused` | Playback was paused; inference may continue only until bounded backpressure limit. Separate because NVDA `pause` preserves queue state. | resume, cancel, terminate. | unbounded PCM production; model change. | Paused player and bounded queued chunks. | Resume to `playing` or `synthesizing`; pause during inference sets this intent before first PCM. |
| `cancelling` | Generation invalidated and audio stop requested. Needed to serialize cleanup and reject late events. | repeated cancel (no-op), terminate, queue replacement metadata. | completion/index notification for cancelled generation; load/speak until cleanup boundary unless replacement policy has atomically advanced generation. | Closing stream, cancel timer, stale-event filter. | Ack/idle → `ready` or `readyWithoutModel`; timeout → restart worker/recoverable failure. No done notification unless future NVDA evidence requires it. |
| `failedRecoverable` | Current operation failed but controller can retry/restart or user can repair model/device. | cancel, diagnostics, bounded restart, model selection, terminate. | speech until prerequisites restored. | Possibly stopped worker/player; no valid active job. | Concise actionable message once; rate-limited logs. Successful repair → appropriate ready state. |
| `failedUnavailable` | Runtime/protocol/platform or repeated crash circuit breaker makes this instance unusable. | terminate; explicit later reselection creates a new instance. | all speech/model operations. | No worker/audio; diagnostic summary. | Ask user to choose another synthesizer/restart after repair; no automatic loop. |
| `terminating` | `terminate()` begins from any nonterminal state. | repeated terminate (idempotent), internal cleanup events. | all new work and notifications except cleanup bookkeeping. | Cancelled generation, stopping audio/worker, closing handles. | Bounded graceful shutdown then forced child termination; call inherited bookkeeping as verified during implementation. |
| `terminated` | All owned resources released. | repeated terminate only. | every other operation/event. | None. | Late events discarded without user output; debug counter only. |

## Transition table

| Event | From | To | Rule |
|---|---|---|---|
| construct | — | initializing | No expensive work on NVDA main thread. |
| handshake succeeds | initializing | readyWithoutModel/loadingModel | Load only a validated persisted selection. |
| model load succeeds | loadingModel | ready | Commit model identity atomically. |
| speak accepted | ready | synthesizing | Create immutable job snapshot. |
| first current PCM | synthesizing | playing/paused | Reject stale generation before buffering. |
| final PCM played | playing | ready | Emit exactly one current-job done notification. |
| pause/resume | synthesizing/playing ↔ paused | as shown | Pause is playback intent; inference backpressure remains bounded. |
| cancel/new replacement | loadingModel/synthesizing/playing/paused | cancelling | Increment generation before worker/audio actions. |
| cancel settles | cancelling | ready/readyWithoutModel | Depends on retained loaded model. |
| recoverable fault | operational state | failedRecoverable | Stop affected job/audio first. |
| fatal/repeated fault | any live state | failedUnavailable | Open circuit; no restart loop. |
| terminate | any nonterminal | terminating → terminated | Terminal and idempotent. |

## Race-case decisions

- Cancel during load/inference/playback: increment generation synchronously, stop audio immediately, send cancel, discard all old events; a load cancelled before atomic commit cannot become selected.
- Voice change during speech: cancel current generation, then load the new validated model. Never mix model settings or PCM.
- Settings change during speech: applies to the next job; volume may affect current playback only if the chosen NVDA audio API proves safe and semantics are documented. Model-affecting settings cancel first.
- Pause during inference: record paused intent and cap worker output; pause during playback calls the verified player pause path. Resume does not regenerate indexes.
- Worker crash before/after PCM: stop player, invalidate generation, emit no further index/done, enter recoverable failure, and perform at most the bounded restart policy.
- Synthesizer change or NVDA shutdown during startup: enter terminating, cancel startup, close/kill child, ignore callbacks. Never announce from a departing synth.
- Rapid speaks: preserve calls as ordered jobs only while capacity exists; NVDA cancellation/priority semantics trigger generation replacement. No implicit unbounded backlog.
- Empty sequence/job: do not contact inference; asynchronously emit one completion only if the NVDA contract experiment confirms this is necessary.
- Unsupported command: never silently reorder. Use documented fallback/skip policy from `docs/speech-job-model.md`; structural invalidity fails the job before worker submission.
- Audio-device loss: stop current audio, invalidate generation, close player, enter recoverable failure, and recreate only on explicit/new speech with rate limiting.
- Model deleted while loaded: an already opened runtime may continue; new load/discovery marks it unavailable. Never assume deletion invalidates native memory safely.

## Invariants

1. Exactly one controller serializes transitions; state and generation change together.
2. At most one current generation and one model transition exist.
3. No PCM, index, warning, or terminal event is accepted unless process instance, protocol session, generation, job, and sequence are current.
4. Each accepted job reaches exactly one internal outcome: completed, cancelled, or failed.
5. `synthDoneSpeaking` is emitted at most once and never merely because synthesis finished.
6. Cancellation and termination are idempotent; termination is irreversible.
7. Text, phonemes, and PCM are absent from normal logs.
8. Queues, messages, text, retries, and buffers are bounded.

## Forbidden transitions

Direct transitions from terminated to any state; unavailable to initializing without a new instance; failedUnavailable to ready without reconstruction; loading one model while another uncommitted load exists; playing old-generation PCM after cancellation; and notifying indexes/completion while terminating or terminated.

## Unresolved questions

- Whether empty accepted sequences require `synthDoneSpeaking` in target NVDA versions.
- Whether current volume can change during playback without violating player/thread rules.
- Whether a previous model can be retained atomically across failed model switches.
- Exact cancellation/restart timeouts and queue capacities; experiments must set them.
