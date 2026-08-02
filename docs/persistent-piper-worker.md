# Persistent Piper worker

Phase 2J uses one non-daemon background controller thread and one persistent child process per driver session. The child imports Piper and ONNX Runtime once, loads the explicitly configured model once, sends a bounded `ready` frame, and accepts one framed JSON request at a time over stdin/stdout. Text never appears in the process command line and no network transport is used.

Requests contain only one segment, generation/job identifiers, a segment number, character-mode metadata, and numeric indexes that follow that segment. The worker returns validated mono signed 16-bit PCM and matching metadata. The controller has one active request and one replaceable pending request; there is no unbounded queue.

The retained Lessac validation run measured approximately 3.287 seconds for the first request and 0.093 seconds for the next warm request on CPU. These are development observations from one machine, not release thresholds.

New speech invalidates the old generation, stops playback, terminates an uninterruptible child, and starts a bounded replacement. Startup, model loading, inference, and protocol reads occur on the controller thread, never in `SynthDriver.speak()`. Cancellation returns without waiting for inference; shutdown performs bounded cleanup and a forced-stop fallback. Consecutive failed starts are capped per controller instance; a successfully handshaken worker clears that failure counter, preventing a transient failure from disabling later valid requests while still bounding repeated failed starts.

Piper's Python generator is consumed to a complete segment before the response frame is returned. This is sentence/segment granularity, not frame-level streaming. PCM is fed to `WavePlayer` in bounded slices and released after playback. No WAV, model, runtime, or PCM is packaged or persisted.

During rapid character replacement, an interrupted live worker is an expected
cancellation rather than a failed startup. The bridge resets its consecutive
start counter for that case; crashes and handshake failures without an
interrupt remain bounded by the restart limit. This prevents replacement
traffic from permanently silencing later navigation speech.
