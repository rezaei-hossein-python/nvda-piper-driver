# Selected-voice character cache

Status: Experimental; portable A/B validation required.

The opt-in cache stores validated PCM for exact NVDA-prepared character-mode
units only. It is process-memory-only, lazy, and never logs or persists keys.
It uses a deterministic LRU bounded to 32 entries, 256 KiB total, and 32 KiB
per entry. Values contain PCM and format metadata only.

Entries are cleared on voice/rate changes, worker restart, termination, and
explicit invalidation. The cache is disabled when the explicit secure-mode
environment marker is active; the prototype does not claim secure-desktop
support. Cache behavior is absent unless both experimental environment
variables are set.
