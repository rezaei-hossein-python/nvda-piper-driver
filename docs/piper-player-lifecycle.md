# Piper player lifecycle

The Piper driver creates `nvwave.WavePlayer` lazily on the first PCM result and
reuses it while sample rate and format remain compatible. A format change closes
the old player and constructs a new one. Cancellation calls `stop()` but does
not intentionally recreate the player. Synth termination closes the player.

Pinned NVDA `WavePlayer` opens the WASAPI device in its constructor and also
reopens safely from `feed()` when needed. It keeps the device open until close,
destruction, or device failure; its ten-second idle check is an internal state
check, not evidence that the device is closed after every utterance.

No source evidence currently shows avoidable player recreation on ordinary
cache hits. Device wake-up and resampling remain unmeasured on the target
machine.
