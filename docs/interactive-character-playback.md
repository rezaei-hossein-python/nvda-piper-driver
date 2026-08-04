# Interactive character playback

Status: Experimental; portable validation pending.

Phase 2O adds an opt-in held-key loop above the accepted Phase 2L character
cache. It is enabled only with `NVDA_PIPER_EXPERIMENTAL_CHARACTER_LOOP=1`.
The normal character, navigation, focus, mouse-over, document, and Read All
paths remain unchanged without that gate.

The loop reuses one cached PCM result and the existing persistent WavePlayer.
It does not submit one worker request or one unbounded queue item per operating
system repeat event. Repeated events refresh a short inactivity window; a
different character, navigation, focus event, cancellation, or shutdown
preempts the loop.
