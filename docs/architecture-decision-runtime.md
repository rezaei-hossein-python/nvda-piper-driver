# ADR: isolate Piper-compatible inference in a persistent worker

## Status: Proposed

## Context

NVDA speech is interruption-sensitive. The pinned source (`references/nvda-source/source/speech/manager.py`, `SpeechManager`; `source/synthDriverHandler.py`, `SynthDriver`) requires index/completion signalling and accounts for late events after cancellation. Neural inference and model loading must not block NVDA. Current Piper embeds native ONNX Runtime and eSpeak NG components; a native failure inside NVDA would affect the screen reader. No project-local performance measurements exist.

## Decision drivers

- Fast audible cancellation and stale-result rejection.
- No blocking on NVDA's main thread.
- Native crash and Python-ABI isolation.
- Offline multilingual Piper-model compatibility, with Persian validation.
- Deterministic resource/update behavior and testability.
- Auditable native dependency and licence handling.

## Options considered

Per-utterance Piper executable; embedded Python package; direct ONNX Runtime; in-process native Piper binding; and a long-running local worker. Detailed comparison is in `docs/piper-runtime-evaluation.md`.

## Provisional decision

Prototype a long-running, child-only, non-networked x64 worker. Use a bounded, versioned IPC protocol; keep one verified model warm; tag commands/events with generation IDs; stream bounded PCM chunks; cancel playback immediately; request inference cancellation; discard all stale events; and kill/restart a hung worker under a conservative policy. The first backend evaluated in that worker will be the current Piper API/library. A worker-wrapped verified CLI is the fallback.

Phase 1C details this proposal in `docs/driver-state-machine.md`, `docs/speech-job-model.md`, `docs/worker-protocol.md`, `docs/audio-pipeline.md`, and `docs/security-threat-model.md`. Those documents add design precision but no implementation evidence.

This decision is **not accepted**. It remains Proposed until local measurements and redistribution review succeed.

## Consequences

NVDA is insulated from most native faults and its Python version need not match the worker runtime. Worker/protocol tests can run without NVDA. Costs include another process, IPC copies, more shutdown/update states, orphan prevention, and additional packaging metadata. Index placement may be approximate unless the backend supplies timing; the adapter must never report an index before its corresponding audio position.

## Risks

Worker startup or model load may still be too slow; cancellation may stop playback but not CPU work; buffering may harm latency; antivirus may flag a packaged executable; a worker can survive NVDA and block updates; GPL-3.0 and component/source obligations may constrain distribution; untrusted models may exhaust memory or exploit native parsers; no secure-screen claim is permitted.

## Required experiments

Run every benchmark and fault scenario listed in `docs/piper-runtime-evaluation.md`, verify x64 clean-machine packaging, audit all transitive components and model licences, test current installed/portable NVDA, and demonstrate deterministic install/update/remove/restart behavior.

Before changing this status, also complete the fake-worker cancellation/stale-generation milestones, compare streamed PCM with complete-buffer and worker-playback alternatives, measure index alignment and audio-device recovery, and verify IPC/process containment and protocol limits.

## Conditions that would reverse the decision

- IPC/process overhead measurably prevents acceptable navigation latency.
- The worker cannot provide bounded cancellation or deterministic shutdown.
- Antivirus/store distribution or licensing cannot be resolved.
- A supported in-process API demonstrates equal fault containment, compatibility, and materially better measured behavior.
- Current NVDA exposes a documented isolation/runtime facility that supersedes this design.
