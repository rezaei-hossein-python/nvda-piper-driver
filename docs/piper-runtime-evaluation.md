# Phase 1B: Piper runtime evaluation

## Scope and evidence

This is architectural research, not a benchmark report. It was last checked on 2026-08-01. The pinned NVDA reference is commit `e98b2a14cbc166294b0bbbb15fe4295cd2e4dd61` (`docs/imported/source-notes.md`). Current Piper development is in [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl); the repository documents a Python API, CLI, C/C++ API, embedded eSpeak NG phonemization, and GPL-3.0 licensing. The former [rhasspy/piper](https://github.com/rhasspy/piper) repository was archived on 2025-10-06 and points to that successor. ONNX Runtime deployment details come from Microsoft's [official documentation](https://onnxruntime.ai/docs/install/) and [licence](https://github.com/microsoft/onnxruntime/blob/main/LICENSE).

NVDA-facing constraints come from `docs/nvda-synthdriver-research.md`, `references/nvda-source/source/synthDriverHandler.py` (`SynthDriver`), `references/nvda-source/source/speech/manager.py` (`SpeechManager`), and the built-in `oneCore.py`, `sapi5.py`, and `espeak.py` drivers. In particular, callbacks can arrive off the main thread, late indexes can follow cancellation, and expensive work must not block NVDA.

No reliable, comparable Windows/NVDA measurements were found. Every latency, cancellation, memory, and CPU comparison below is therefore a hypothesis requiring local benchmarking.

## Options

### 1. Bundled or separately installed Piper executable

Architecture: invoke the CLI and exchange text/audio over pipes or files. A fresh process per utterance reloads the model; a persistent CLI/server avoids that cost. Cancellation can terminate a child or close its stream, but graceful cancellation semantics must be measured. Streaming depends on the selected executable protocol.

Assessment: strong Python isolation and straightforward standalone testing; high cold-start risk if launched per utterance; pipe backpressure and deadlock are possible; process startup, model load, CPU, RAM, and first-audio latency require benchmarking. A separately installed binary complicates discovery and support; bundling increases add-on size and creates DLL, provenance, checksum, licence, source-offer, and security-update obligations. A verified x64 build is required. It is offline after installation. Store suitability is plausible, not assured.

### 2. Embedded Python Piper package

Architecture: package `piper-tts` and import it in NVDA's Python process, or invoke it from a project thread. The model can remain loaded and Python-level APIs may expose chunk generation. Cancellation normally stops future consumption, but whether active native inference is interruptible must be verified.

Assessment: potentially low warm latency and easy API composition, but native wheels must match NVDA's exact 64-bit Python ABI. Native crashes, allocator conflicts, DLL resolution, and GIL/native-thread behavior affect NVDA itself. Packaging transitive dependencies is complex and large. Thread safety must not be inferred from API shape. Updates are coupled to add-on releases. This is maintainable only if reproducible wheels and compatibility tests exist; it is a poor initial fault-isolation choice.

### 3. Direct ONNX Runtime integration

Architecture: project code performs Piper-compatible text normalization/phonemization, reads the model JSON, constructs tensors, owns an ONNX Runtime session, and converts output to PCM. Sessions can be long-lived; output is generally obtained per inference unless the model/API supports meaningful incremental execution.

Assessment: removes a Piper executable but does not remove Piper's preprocessing contract. It offers maximum control over queues, validation, providers, and instrumentation. It also makes this project responsible for model-schema drift, phoneme IDs, speaker/scales, phonemizer data, audio conversion, and compatibility testing. In-process ONNX Runtime has the same native-crash/DLL/ABI risk; out-of-process direct ORT mitigates it. Cancellation of an executing `Run` needs explicit proof with the chosen API/version; dropping stale output is not equivalent to saving CPU. Windows x64 support is available upstream. CPU, memory, first-audio latency, and compatibility across representative models require measurement. Store suitability depends on complete binary notices and size.

### 4. Native Piper library or binding

Architecture: call `libpiper` through a compiled extension, FFI, or a small native host. The current Piper repository exposes a C/C++ API. A host can keep model state warm and may provide a purpose-built streaming/cancellation protocol.

Assessment: potentially the smallest runtime boundary and best control, but creates a C/C++ build, ABI, CRT, symbol, DLL search, signing, and crash-debugging burden. An in-process binding can take down NVDA; a native host isolates faults. Python-version sensitivity is low for a stable IPC host but high for a CPython extension. Piper/eSpeak NG/ONNX Runtime licensing and corresponding-source obligations must be resolved before redistribution. Performance requires local measurement.

### 5. Long-running local worker process

Architecture: NVDA owns one restricted child process. A versioned framed IPC protocol carries commands (`load`, `speak`, `cancel`, `shutdown`) and events (PCM chunks, index/progress mapping, errors, done). The worker loads one model persistently; requests carry monotonically increasing generation IDs. Cancellation invalidates queued and late events, stops playback immediately, and asks the worker to abort. The worker never listens on a network socket.

Assessment: amortizes process/model startup, isolates native crashes and Python/runtime dependencies, and permits independent harness tests. Costs are an extra process, duplicated IPC buffers, lifecycle complexity, and possible orphan/update failures. Sonata's v2 release notes report responsiveness gains after moving TTS to a separate process, while v3 beta release notes tell users to kill `sonata-grpc` during a failed update; this is evidence for both the promise and the lifecycle risk, not a benchmark ([Sonata releases](https://github.com/mush42/sonata-nvda/releases), accessed 2026-08-01). A named pipe or inherited anonymous pipes are preferable to a listening TCP service. Store suitability is plausible if every binary is documented and shutdown/update behavior is proven.

### 6. In-process versus out-of-process inference

| Criterion | In process | Out of process |
|---|---|---|
| Warm-call overhead | Avoids IPC; magnitude unmeasured | Adds framing/copying; magnitude unmeasured |
| Model lifetime | Simple singleton | Worker-owned persistent session |
| Cancellation | Shared state is easy; native call may remain uninterruptible | Immediate audio/stale-result rejection plus worker abort/kill fallback |
| Main-thread risk | High if any call path or callback blocks | Lower if adapter IPC is non-blocking |
| Crash isolation | None for native faults | Worker can be detected and restarted with limits |
| Python compatibility | Native wheels must match NVDA | Worker may carry an independent runtime |
| Memory | No IPC duplication | Process/runtime and buffers add overhead |
| Packaging | Fewer components, tighter ABI coupling | More components/protocol, looser NVDA ABI coupling |
| Security | Native code handles models inside NVDA | Smaller NVDA boundary; worker still parses untrusted input/models |
| Testing | Requires NVDA-like host for failures | Protocol and worker can be fuzzed/tested independently |

## Complete comparison by required criterion

“Benchmark” means no reliable comparable measurement was found and a local test is required. “Depends” means the selected upstream artifact/protocol determines the result.

| Criterion | Executable | Python Piper | Direct ORT | Native Piper/binding | Persistent worker / process placement |
|---|---|---|---|---|---|
| Architecture | stdin/stdout/files | Python calls native packages | project preprocessing + ORT session | C/C++ API via FFI/host | versioned IPC to one warm backend; in- or out-of-process distinction above |
| First-speech latency | Fresh launch/load likely costly; benchmark | Lazy/eager load; benchmark | Lazy/eager session; benchmark | Lazy/eager load; benchmark | One startup/load then warm; benchmark cold and warm |
| Steady-state latency | Persistent mode required; benchmark | benchmark | benchmark | benchmark | IPC overhead plus warm backend; benchmark |
| Model loading | Per launch or persistent mode | Python object/session | project owns session | library object | worker owns and may switch/reload explicitly |
| Cancellation | close/terminate or protocol; verify | stop consumption; active call unknown | ORT termination support/version must be proven | API-dependent | stop audio, invalidate generation, request abort, kill only on hang |
| Streaming | stdout/protocol-dependent | generator/API-dependent | model generally returns an output; prove chunk strategy | API-dependent | protocol can stream bounded chunks if backend produces them |
| Thread safety | process/pipes still need synchronization | undocumented until audited/tested | ORT guarantees must be checked for exact calls/config | undocumented until audited/tested | serialize backend work initially; NVDA client remains non-blocking |
| NVDA main-thread risk | low only with asynchronous I/O | high if imported/called incorrectly | high in-process | high in-process | lowest candidate if all IPC/audio calls are asynchronous |
| Crash isolation | strong | none in-process | none in-process | none in-process; strong in host | strong for out-of-process worker |
| Python compatibility | independent executable | exact NVDA ABI/wheel issue | wheel/extension issue in-process | extension ABI or none for host | independent runtime if worker is self-contained |
| Windows x64 | require verified x64 artifact | require x64 compatible wheel | official x64 packages exist; pin one | require reproducible x64 build | require verified x64 worker and every DLL |
| Native dependencies | Piper/ORT/eSpeak/CRT set | transitive wheel DLLs/data | ORT + chosen phonemizer | Piper/ORT/eSpeak/CRT | those of selected backend plus worker runtime |
| Model compatibility | strongest when matching Piper version | matching package version | project must reproduce Piper contract | matching library version | equals selected backend; protocol carries validated metadata |
| Memory | process/model; benchmark | model in NVDA; benchmark | session in NVDA; benchmark | model in NVDA/host; benchmark | extra process/runtime/buffers; benchmark peak and steady |
| CPU | benchmark; cancellation may kill | benchmark; abort unknown | benchmark; provider/config-sensitive | benchmark | backend CPU plus IPC; benchmark cancel-to-idle |
| Packaging complexity | medium/high | high native-wheel bundle | high plus preprocessing | highest build burden | high protocol/lifecycle burden, but ABI decoupling |
| Add-on size | runtime-sized; model choice dominates | wheel/dependency-sized | ORT + phonemizer | native runtime set | worker/runtime-sized; no voices recommended initially |
| Installation | bundled simple/large; separate install fragile | bundled dependencies only | bundled dependencies only | bundled host/DLLs | bundled worker; no service/admin/listening port |
| Update | replace closed binary or coordinate external version | replace all wheels safely | update ORT/schema together | rebuild/retest toolchain | stop worker first; transactional migration/rollback tests |
| Security | child input, binary provenance, pipe/file safety | native parser in NVDA, DLL risk | native parser plus project preprocessing | native parser/FFI/DLL risk | isolation helps containment; authenticate/inherit IPC and bound messages |
| Licensing/redistribution | audit Piper, eSpeak, ORT, CRT, sources | audit package and transitive wheels/data | audit ORT and phonemizer | audit library and linked components | audit complete worker closure and provide required sources/notices |
| Offline capability | yes after install | yes | yes | yes | yes; no listener or silent downloader |
| Testability | good black-box | good unit tests, hard native faults | high component control | native harness required | strongest protocol/fault-injection boundary |
| Maintainability | follows CLI but protocol drift | package/API/ABI churn | project owns Piper compatibility | toolchain/API burden | protocol adds work; backend and NVDA can evolve separately |
| Store suitability | possible after provenance/size/scan validation | possible but ABI/size risk | possible but binary/licence burden | possible but highest review burden | recommended candidate; still subject to identical validation and no acceptance promise |

## Cross-cutting requirements

All options can operate offline. None is automatically safe, stream-capable, thread-safe, fast, or Store-acceptable. Model/config pairs must be allowlisted by supported schema, checked for regular-file paths within approved roots, size-limited, and identified by checksum. Text must never be logged. Runtime acquisition must be reproducible and pinned. DLL loading must use explicit application directories rather than the current directory or `PATH`. Audio and notification handling must follow the pinned NVDA contracts; `WavePlayer` examples in built-in drivers are evidence, not a guaranteed public compatibility layer.

## Weighted decision matrix

Scores are provisional engineering judgments (1 poor, 5 strong), not measurements. Weight totals 100.

| Criterion | Weight | Per-utterance executable | Embedded Python | Direct ORT in-process | Native binding in-process | Long-running worker |
|---|---:|---:|---:|---:|---:|---:|
| Responsiveness/cancellation potential | 25 | 2 | 3 | 4 | 4 | 5 |
| NVDA stability/crash isolation | 20 | 5 | 1 | 1 | 1 | 5 |
| Packaging/Store feasibility | 15 | 3 | 2 | 3 | 2 | 3 |
| Compatibility/maintenance | 15 | 3 | 2 | 2 | 2 | 4 |
| Model compatibility | 10 | 5 | 5 | 3 | 5 | 5 |
| Security/privacy control | 10 | 4 | 2 | 3 | 2 | 4 |
| Testability | 5 | 4 | 3 | 4 | 3 | 5 |
| Weighted total / 500 | 100 | 345 | 240 | 280 | 260 | 450 |

The table intentionally does not score unmeasured speed as fact. Its result mainly reflects the project's unusually high weighting of cancellation and NVDA fault isolation.

## Recommendation

Prototype a **long-running, non-networked x64 worker process** with a small versioned IPC protocol, persistent model session, bounded PCM chunks, generation IDs, explicit cancel acknowledgement, heartbeat/exit detection, and deterministic shutdown. Keep the NVDA adapter, sequence mapping, worker client, runtime backend, and audio controller separate. Initially evaluate the current Piper native/Python implementation *inside the worker*, not NVDA. Do not bundle it until provenance and GPL-3.0/eSpeak NG/ONNX Runtime obligations are documented.

Fallback: a verified bundled Piper CLI controlled by a persistent project-owned worker wrapper. It sacrifices backend control but preserves process isolation and can validate the NVDA/audio protocol sooner.

Rejected for the first prototype: a process per utterance (cold-start risk), embedded Python/native bindings inside NVDA (crash and ABI coupling), and a bespoke in-process direct-ORT reimplementation (too much compatibility responsibility before measurements). These may be reconsidered after evidence.

## Required proof-of-concept benchmarks

- Cold start, model load, first PCM, and completion latency; report distributions, not only averages.
- Warm first-PCM and real-time factor for short navigation tokens, sentences, and long reading, including Persian.
- Cancel-to-audio-silence and cancel-to-worker-idle latency during load, inference, IPC, and playback.
- Rapid queue replacement, stale-event rejection, and index/done correctness under at least thousands of deterministic operations.
- Peak/steady private memory, CPU, handle/thread counts, and IPC buffer depth per representative model quality.
- NVDA main-thread call duration and watchdog behavior.
- Worker crash, hang, malformed frame/model/config, audio-device loss, sleep/resume, shutdown, update, and orphan recovery.
- Installed and portable current 64-bit NVDA on the proposed Windows support matrix; clean x64 machines without developer runtimes.
- Compare worker-backed Piper API, worker-backed CLI, and (only if safe to build) direct ORT using identical text, model, hardware, warm-up, audio policy, and measurement scripts.
