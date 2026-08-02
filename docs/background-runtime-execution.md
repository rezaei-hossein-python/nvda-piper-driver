# Phase 2J bounded background runtime execution

## Purpose and decision

Phase 2J replaces the blocking Phase 2I call path. Four options were reconsidered: a background thread around the existing one-shot child, a persistent protocol worker, repeated one-shot children under a controller, and direct asynchronous inference inside NVDA. Direct inference was rejected because Piper and ONNX Runtime must stay outside NVDA. A persistent worker would reduce repeated model loads but requires a new production protocol and a larger cancellation design.

The selected development architecture is one non-daemon controller thread that owns repeated one-shot child requests. It is the smallest change that keeps native inference isolated and removes model loading, inference, process communication, PCM collection, `WavePlayer.feed`, and `WavePlayer.idle` from NVDA's main thread. The runtime ADR remains **Proposed**.

## Bounds and lifecycle

The controller owns at most one active request and one replaceable pending slot. Submitting newer speech changes the current generation, overwrites the pending slot, and sends a non-waiting termination request to an older active child. There is no list-backed queue and no overlap. Construction starts exactly one non-daemon controller thread; it imports neither Piper nor ONNX Runtime. Model loading starts in a one-shot child only when the controller accepts speech.

States are `starting`, `ready`, `active`, `failed`, `stopping`, and `stopped`. A request submitted during startup occupies the single pending slot. Newer speech during child startup, model loading, inference, PCM transfer, playback, or queued completion invalidates the older generation. Shutdown clears pending work, invalidates active work, requests child termination, and joins the controller for a provisional five-second maximum. Failure to join is reported as `shutdownTimeout`; no daemon thread is relied upon for cleanup.

## Main-thread and replacement behavior

`SynthDriver.speak()` validates driver state, performs the existing bounded immutable conversion, extracts exact text while discarding mandatory index and language-change metadata, replaces the single slot, and returns. A provisional automated guard checks a 100 ms return on test doubles; this is not a production threshold. No Piper import, ONNX import, model loading, inference, blocking subprocess communication, PCM collection, playback drain, or process wait occurs on that caller thread.

Replacement retains only the newest pending request. The bridge uses a cancellation token to close the race between generation replacement and child creation. Correlated PCM is checked again before player creation, every bounded playback feed, and completion. Queued completion is rechecked when NVDA's main-thread event queue delivers it.

## Cancellation and audio

`cancel()` is idempotent and returns after invalidating the generation, clearing the pending slot, requesting non-waiting child termination, and calling `WavePlayer.stop()`. The pinned SAPI driver documents `stop()` as stopping audio and an `idle()` wait. Active ONNX inference has no cancellation token; hard interruption therefore terminates the one-shot child. Cancel-to-worker-idle depends on process termination and is distinct from cancel-to-playback-stop.

Validated PCM remains model-rate, mono, signed 16-bit and bounded to 32 MiB. Full PCM still crosses the child boundary before playback; worker streaming is not implemented. The controller feeds fixed 50 ms slices so a feed call cannot monopolize cancellation for the whole utterance, then calls `idle()` on the controller thread. No WAV is written. PCM and request content are released after completion, cancellation, replacement, or failure.

`synthDoneSpeaking` is queued through pinned `queueHandler.queueFunction(queueHandler.eventQueue, ...)`, the documented NVDA main-thread queue. It is emitted only after successful final playback and a final current-generation check. It is not emitted after cancellation, failure, stale output, replacement, or shutdown. Index and language-change items are accepted solely because NVDA includes them in ordinary speech sequences. They are ignored during Phase 2J synthesis, are not inspected, sent to the child, or retained, and produce no metadata notification. Command support remains unadvertised.

## Failures, privacy, and limitations

Fixed classifications cover runtime initialization, model load, worker startup/crash/hang, protocol and PCM failures, stale/cancelled output, playback, internal controller errors, and shutdown timeout. Worker stderr is matched only against fixed content-free messages. Speech text, subprocess payloads, PCM, environment values, and local paths are not logged. There is no network access, telemetry, WAV retention, global job cache, filesystem discovery, or language-specific branch.

Repeated cold model loading remains inefficient. Hard cancellation is process termination, shutdown still has a provisional bounded join, and no production restart policy, index notification, pause/resume, model UI, runtime bundling, or multi-model caching exists. Portable-NVDA results are development evidence only and do not accept the runtime architecture. Controlled discovery, visible listing, and selection succeeded. The final controlled run produced audible Piper review speech and Ctrl cancellation, but with noticeable latency; typed-character echo and Read All did not proceed because their out-of-scope command items remain rejected. The rejection boundary now catches fixed extraction failures and emits one content-free warning per consecutive rejection episode, preventing NVDA event traceback leakage. The final log had no traceback, critical/error, watchdog, recovery, or worker-survival entry, and the user manually closed the final NVDA process. Exact replacement/completion timing remains unmeasured, so Phase 2J remains incomplete. Future multi-model behavior requires a separate design.

## Tests

Pure tests cover immutable requests, one-slot replacement, caller responsiveness, cancellation, stale PCM/completion rejection, bounded shutdown, process races, safe command construction, PCM validation, privacy, and scope. Focused extraction tests cover exact multilingual Unicode and whitespace, index/language placement and multiplicity, `None`, metadata non-retention, metadata-only rejection, absent metadata notification, later recovery after one unsupported item, and continued rejection of all other command families. A retained ignored runtime/model test loads and synthesizes through the controller with a playback double. Portable evidence is recorded separately in `phase-2j-portable-validation.md`.

## Current Phase 2J implementation correction

The controller now owns a persistent child rather than starting a one-shot child for every request. The child loads the configured model once per session and serves framed, one-segment requests. `IndexItem` boundaries are preserved; after each segment's playback the controller dispatches `synthIndexReached` on NVDA's event queue, then emits final completion only after the last segment. `CharacterModeItem` creates an isolated character-mode segment and is advertised through `CharacterModeCommand` support. Language changes remain metadata-tolerated and never switch models.

The worker still buffers each Piper segment before playback because the available generator is sentence/segment-granular, not frame-streaming. There is one active request and one replaceable pending request. Replacement and cancellation terminate the persistent child when inference cannot be interrupted; restart attempts are bounded. Portable validation remains required for typed echo, Read All progression, replacement, latency, and watchdog behavior. The runtime ADR remains **Proposed**. Phase 2K is not begun.
