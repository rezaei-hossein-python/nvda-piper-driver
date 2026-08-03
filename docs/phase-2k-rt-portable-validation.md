# Phase 2K RT portable validation

Status: Proposed

No RT backend was packaged and no portable NVDA comparison was run. The real chunk prototype is explicitly gated by `NVDA_PIPER_EXPERIMENTAL_STREAM=1`, lives under `experiments/`, and is excluded from the add-on archive. Portable validation must wait for a native NVDA adapter that preserves index boundaries, completion-after-drain, stale suppression, and cancellation semantics.

Required future comparison: current Python backend, a development-only incremental backend using the same selected voice, and eSpeak, tested with continuous typing, Up/Down, controls, Read All, cancellation, recovery, and shutdown. Subjective onset must be supplied by the user; worker timings are insufficient.
