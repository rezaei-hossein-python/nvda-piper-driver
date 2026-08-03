# Piper audio-start latency

The existing long-lived NVDA `WavePlayer` remains the audio owner. Cached PCM
uses the same validation, feed, and drain path as worker PCM, so the experiment
does not change device configuration or introduce per-chunk `idle()` calls.
`firstWavePlayerFeed` is the content-free objective proxy recorded by the
existing latency trace. Physical audible onset is not inferred from this event.
