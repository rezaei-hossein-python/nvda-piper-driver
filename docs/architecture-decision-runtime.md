# ADR: isolate Piper-compatible inference in a persistent worker

## Status: Proposed

Phase 2H evidence (2026-08-01) does not change this status. After interactive installation of Microsoft Visual C++ x64 runtime 14.51.36247.0, `piper-tts` 1.5.0 and ONNX Runtime 1.28.0 loaded a provenance-checked voice through `CPUExecutionProvider`. Standalone model load, sentence-chunk, completion, RTF, sampled CPU/memory, controlled failures, generator stop, and mono 16-bit WAV structure were measured. These results do not cover NVDA, IPC, playback, active-inference cancellation, crash containment, multi-model compatibility, or redistribution. See `standalone-piper-runtime-results.md` and `piper-component-inventory.md`.

Phase 2I prototypes a narrower one-shot child boundary for the first controlled portable-NVDA utterance. It keeps Piper and ONNX Runtime outside NVDA, passes bounded text through standard input, returns correlated complete-buffer PCM through standard output, and owns deterministic child teardown. It does not validate a long-running worker, streaming, responsiveness, production cancellation, indexes, packaging of dependencies, or broad model compatibility, so the status remains Proposed.

## Context

NVDA speech is interruption-sensitive. The pinned source (`references/nvda-source/source/speech/manager.py`, `SpeechManager`; `source/synthDriverHandler.py`, `SynthDriver`) requires index/completion signalling and accounts for late events after cancellation. Neural inference and model loading must not block NVDA. Current Piper embeds native ONNX Runtime and eSpeak NG components; a native failure inside NVDA would affect the screen reader. Phase 2H provides standalone measurements only, not NVDA or audio-pipeline evidence.

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
