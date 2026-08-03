# Piper audible-latency measurement

Status: Proposed

The driver now records bounded, in-memory, content-free traces keyed by request and generation IDs. Events include `speakEntry`, `speakReturn`, `controllerSubmit`, `controllerStart`, `firstPcmReceived`, `firstWavePlayerFeed`, and `playbackDrainComplete`. Timestamps use `time.monotonic_ns()`; no speech text, character value, language, or document content is retained.

`firstWavePlayerFeed` is the closest objective playback-start proxy exposed by the pinned NVDA boundary. The current Piper worker consumes each generator result into one complete PCM response, so `firstPcmReceived` occurs only after the complete segment is synthesized. The retained Lessac model yielded one chunk for each tested short and sentence case; frame-level streaming is therefore not claimed.

The current repository does not expose a safe input-hook timestamp or an audio-device callback timestamp. Portable validation must manually correlate keypresses with the trace categories and audible onset. Until that is done, worker-only medians must not be presented as input-to-audible latency.

The trace recorder is bounded to 128 records and 32 events per record, is process-memory-only, and has no output or persistence path.

For a controlled portable run, set `NVDA_PIPER_LATENCY_TRACE=1` in the same process-local environment as the other development variables. The driver then emits one debug record per completed playback containing only IDs and timestamp maps. Remove the variable after testing; it is not a user setting.
