# Piper short-utterance path

Status: Proposed

Phase 2J keeps one active request and one replaceable pending request. Phase 2K preserves that replacement model and uses the same warm worker for characters, words, controls, and navigation. No language-specific branch, eSpeak substitution, or parallel speech queue was added.

The worker now creates one `SynthesisConfig` after model load and reuses it for the session. It performs a silent empty synthesis before readiness, warming phonemizer and ONNX execution without emitting audio, indexes, completion, or user-visible text.

A PCM cache was not added. Repeated and unique short requests measured overlapping 24–30 ms ranges, while navigation text is mostly unique; cache invalidation would add model/settings identity and memory policy without demonstrated broad benefit.

The current controller already keeps one newest pending request and avoids interrupting an active short request, preventing ordinary character replacement from hard-killing the warm worker. Longer requests may still be interrupted when replacement is necessary. Stage traces now distinguish that scheduling time from first PCM receipt and first `WavePlayer.feed()`.
