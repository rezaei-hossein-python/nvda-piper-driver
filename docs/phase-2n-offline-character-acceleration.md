# Phase 2N offline character acceleration

Status: Experimental; portable A/B validation pending.

The accepted Phase 2L cache remains the control. Phase 2M length-scale and
held-key experiments were rejected by portable testing and are not enabled by
this experiment. Phase 2N changes only PCM selected while populating an
eligible character cache entry.

Acceleration requires the existing short-speech and cache gates plus
`NVDA_PIPER_EXPERIMENTAL_CHARACTER_ACCELERATION=1` and a bounded
`NVDA_PIPER_CHARACTER_ACCELERATION_FACTOR` from 1.10 through 2.00. Cache hits
perform no transformation. Ordinary speech, navigation, mouse-over, typed
words, document reading, and Read All are unchanged.

The implementation reuses the pinned NVDA 2026.1.1 `_sonic.py` wrapper and the
Sonic DLL shipped by that portable NVDA. The wrapper is GPL-covered NVDA code;
Sonic is the upstream waywardgeek/sonic project referenced by NVDA. No Sonic
binary is copied into this add-on. If the wrapper or DLL is unavailable, the
original validated PCM remains the cache value.

An initial Lessac development benchmark tested factors 1.10, 1.20, 1.30,
1.40, 1.50, 1.60, 1.75, and 2.00 across six category fixtures. Sonic
transformation itself was approximately 0.1-5 ms per fixture in that run;
duration reductions increased with factor. For example, the representative
digit fixture measured approximately 464 ms unaccelerated, 299 ms at 1.50,
and 231 ms at 2.00. These are not quality or physical-onset results, so 1.50
and 2.00 are only the two candidates sent to portable listening evaluation.
