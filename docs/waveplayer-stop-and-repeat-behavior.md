# WavePlayer stop and repeat behavior

The diagnostic compares repeated immutable PCM with and without `stop()`.
Package B's character FIFO avoids stopping the player for each character;
navigation and focus still stop stale local playback. Direct loopback evidence
is pending, so this document does not claim that `stop()` alone explains the
remaining audible delay.
