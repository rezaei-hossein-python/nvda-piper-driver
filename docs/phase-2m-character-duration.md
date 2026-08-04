# Phase 2M character duration

Status: Experimental; portable A/B validation pending.

Accepted Phase 2L remains the control. Phase 2M adds an opt-in character-only
Piper `length_scale` path. It requires
`NVDA_PIPER_EXPERIMENTAL_SHORT_SPEECH=1`,
`NVDA_PIPER_EXPERIMENTAL_CACHE=1`, and
`NVDA_PIPER_EXPERIMENTAL_CHARACTER_DURATION=1`; the factor is bounded to
0.60-1.00 through `NVDA_PIPER_CHARACTER_LENGTH_SCALE`. Ordinary speech,
Read All, and document audio retain the normal configuration.

Direct Lessac measurements tested 1.00, 0.90, 0.80, 0.70, and 0.60. Results
varied by category and inference run; 0.70 is the initial conservative
candidate. In a warm direct-runtime sample, median synthesis was approximately
65 ms at 1.00, 58 ms at 0.80, 52 ms at 0.70, and 41 ms at 0.60. Observed PCM
frame counts varied by category, so these are engineering measurements, not a
quality decision or an audible-onset claim.

The development packages are ignored artifacts kept for portable A/B testing:

* Phase 2M control: `nvdaPiperDriver-phase2m-control-0.1.0.nvda-addon`
  (SHA-256 `729B625E79F809EB991E0DA74A69745DF10376CE6AD86CC6F1BAC18F2CF1CAF4`).
* Length-scale candidate: `nvdaPiperDriver-phase2m-length-scale-0.1.0.nvda-addon`
  (SHA-256 `9CF36FDA0779269969270E520EDB1F4FF262CBC4709189D3DC061A43BFC8F9DA`).

No Sonic or native backend is included. Sonic was not added because no approved
redistributable dependency and no portable quality result are available; the
language/runtime migration gate remains closed.
