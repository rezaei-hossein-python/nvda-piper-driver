# WavePlayer idle and completion

In pinned NVDA 2026.1.1, `WavePlayer.idle()` calls `sync()` and therefore waits
for previously fed audio to finish. It is a completion/drain operation, not a
first-feed operation. The Piper driver calls it after the feed loop for normal
requests; the event-fidelity loop deliberately avoids it only behind an
experimental gate.

`WavePlayer.stop()` flushes playback, clears done callbacks, resets activity,
and leaves the player reusable. It is used for cancellation and replacement,
not between ordinary character feeds in the accepted path.

NVDA's SAPI5 driver documents why its own speech thread owns `idle()`: waiting
on an audio thread can deadlock. This supports keeping completion draining off
NVDA's main thread, but does not prove that Piper's `idle()` contributes to
onset latency.
