# Piper latency breakdown

Status: Proposed

Measured boundaries include persistent process creation, readiness, IPC send, worker synthesis return, PCM frame decode, and bridge return. Process creation was 9.6 ms, runtime/model initialization and silent warm-up before `ready` were 2,152.5 ms, request framing was below 1 ms, and the first warm response took 31.8 ms after send.

Ranked bottlenecks:

1. Cold process/model initialization.
2. Piper phonemization and ONNX inference for each unique short request.
3. Audio-device startup when a player is first created or reopened.
4. Complete-segment buffering; the retained Piper API yielded one chunk per tested segment.
5. JSON framing and Python scheduling, below measured synthesis cost.

NVDA-side controller scheduling, `WavePlayer` feed, and `idle()` completion remain on the background controller thread. `speak()` and `cancel()` remain nonblocking. Physical device-open time and audible onset require portable NVDA measurement.

The restored-model rerun confirms the ranking: one-shot short requests were approximately 2 seconds, while persistent warm requests were approximately 24-51 ms depending on category. Cancellation returned in under 1 ms, but hard termination makes the next request cold again; this is a proven remaining bottleneck rather than an IPC estimate. A lifecycle race that could submit to a terminating process was fixed by detaching and asynchronously reaping the old process before replacement.
