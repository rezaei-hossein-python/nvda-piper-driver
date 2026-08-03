# Piper runtime backend comparison

Status: Proposed

| Area | Current Phase 2K | Sonata | Native direct worker candidate |
|---|---|---|---|
| Runtime | Python Piper API | Rust Piper engine | Rust/C++ ONNX worker |
| Transport | bounded local pipe | persistent localhost gRPC | bounded binary IPC |
| Model | standard one-file ONNX | standard or RT split model | standard or proven RT model |
| Output | one complete chunk in retained tests | server-streamed; RT model chunks | must be measured |
| Audio | NVDA WavePlayer | long-lived WavePlayer per rate | reuse NVDA WavePlayer |
| Cancel | generation plus hard worker stop for active inference | task/stream cancellation, server remains alive | generation plus cooperative stream cancel |
| Compatibility | ordinary Piper voices | RT requires transformed voice | depends on model adapter |

Sonata's material latency mechanisms are persistent model state, no navigation concatenation, early chunk feed, and a separate RT model. gRPC is an isolation and streaming interface, not evidence of lower transport latency. A native migration is justified only after the same corpus demonstrates earlier first PCM or earlier audio feed without sacrificing ordinary Piper compatibility.

The current project has not measured physical audible onset. Worker timings must not be presented as equivalent. The next implementation should add bounded chunk streaming to the current worker protocol, keep the WavePlayer alive, and use generation invalidation rather than ordinary worker termination.
