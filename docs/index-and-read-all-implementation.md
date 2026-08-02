# Index callbacks and Read All

Phase 2J now preserves immutable speech segments instead of flattening an utterance. Text is split at each `IndexItem`; each segment carries only its bounded numeric index metadata. The background controller synthesizes and plays one segment, then queues `synthIndexReached` through NVDA's event queue. Only after the final segment and its final callback does it queue `synthDoneSpeaking`.

This is a real audio-boundary callback, not a timestamp estimate. An index before text is represented by a no-audio boundary and dispatched before the following segment. Consecutive indexes are dispatched in order. Cancellation, replacement, stale generations, worker failures, and synthesizer teardown suppress callbacks that have not yet been delivered.

Pinned `SpeechManager` maps Read All callbacks to indexes, so this ordering allows the normal Read All callback to request the next unit. The driver advertises index notifications because it now implements them. It does not fabricate indexes, approximate timing, or retain index state after the request finishes.

Known limitation: each index-delimited segment is synthesized as a complete Piper request. This is bounded and correct for callback ordering, but can add neural inference latency at boundaries. Further optimization requires measurements and remains outside this correction.

The retained model integration test exercises multiple ordered callbacks and confirms that completion follows the final callback. Portable NVDA Read All and cancellation progression still require manual confirmation.
