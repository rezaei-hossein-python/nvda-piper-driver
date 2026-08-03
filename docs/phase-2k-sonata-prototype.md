# Phase 2K Sonata prototype decision

Status: Proposed

## Result

No production backend was replaced and no Sonata binary was copied. A real Sonata prototype could not be measured in this environment: Rust/Cargo is not installed, the project has only the approved standard Lessac model, and no official RT model was present in the disposable validation environment. Inventing a benchmark with a mock stream would not answer the audible-onset question.

The research prototype is therefore an evidence-backed design boundary, not a claimed performance result. It identifies the smallest next experiment: add a development-only chunk-streaming worker path, keep the existing Python backend selectable, and compare first PCM and first `WavePlayer.feed()` using the existing content-free trace IDs. If an official RT archive is later authorized, benchmark it separately and label model differences.

## Proven prototype properties to reproduce

1. One warm process and one model load per session.
2. One persistent NVDA `WavePlayer` per format.
3. No adjacent-string concatenation for navigation.
4. Incremental PCM feed as soon as a valid model chunk arrives.
5. Local stop plus stale-generation rejection; do not kill the server for ordinary replacement.
6. Completion only after the final player drain; indexes at their actual boundaries.

These are adaptations of observed behavior, not copied code. A native Rust backend remains a future candidate only after licensing, build reproducibility, and same-model measurements are available.
