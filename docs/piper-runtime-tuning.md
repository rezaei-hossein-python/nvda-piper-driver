# Piper runtime tuning

Status: Proposed

The tested runtime uses the existing Piper Python API and CPU ONNX Runtime provider. No machine-specific thread count, process priority, affinity, memory-arena override, or graph setting was changed. Such settings require per-voice and per-machine evidence.

The selected optimization is configuration reuse: one `SynthesisConfig` per persistent worker instead of constructing one per request. A controlled comparison showed a short-request median decrease from approximately 28.7 ms to 26.1 ms. The persistent process and model remain the primary warm-path optimization.

The worker remains isolated, offline, bounded, and restartable. No runtime or model is packaged.

Cancellation/replacement testing found that Windows process termination is asynchronous. The persistent bridge now detaches a terminating process immediately, reaps it off-thread, and allows the next request to start a clean worker. This preserves sub-millisecond caller return and prevents a terminating-process race; it does not claim active ONNX cancellation or avoid model reload after hard cancellation.
