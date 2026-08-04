# Piper character time compression

Time compression is applied once, after normal character synthesis and PCM
validation, only while populating the selected-voice cache. The cache key
isolates the acceleration implementation and factor, so changing either cannot
reuse an incompatible entry. A cache hit bypasses Piper, Sonic, and IPC.

The current development implementation uses Sonic's speed control, which is
designed to preserve pitch while changing duration. Output remains mono,
16-bit signed PCM at the Piper sample rate and is rejected if empty,
unaligned, or not shorter than the original. Failure falls back to the normal
PCM without failing speech.
