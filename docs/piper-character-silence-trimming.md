# Piper character silence trimming

An opt-in conservative prototype uses a sustained amplitude threshold, retained
pre/post-roll, alignment checks, and a minimum 50% retained-duration guard. It
is enabled only with `NVDA_PIPER_EXPERIMENTAL_CHARACTER_TRIM=1`, applies only
to eligible character-cache entries, and falls back to original PCM whenever
uncertain. Initial Lessac measurements triggered the fallback; no production
benefit is claimed.
