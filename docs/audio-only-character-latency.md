# Audio-only character latency

Status: Development diagnostic; no portable audible-onset claim yet.

`experiments/piperRuntime/audioDiagnostic.py` exercises validated PCM against a
WavePlayer-like object in bounded direct-feed and stop-before-feed modes. It
does not invoke Piper, phonemization, ONNX Runtime, IPC, or model loading. The
production add-on does not import this module.

Physical onset requires WASAPI loopback or another synchronized capture on the
target machine. `WavePlayer.feed()` remains only an objective admission proxy.
