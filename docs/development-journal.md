# Development Journal

## 2026-08-03 — Short-speech cache experiment

Added a development-only character-mode PCM cache behind two explicit
environment gates. It is lazy, memory-only, bounded, language-neutral, and
uses the existing warm worker/controller and `WavePlayer` path on misses and
hits. Portable A/B validation is still required; no production recommendation
or physical audible-onset claim is made.

## 2026-08-03 — Character event fidelity experiment

The cache exposed a scheduling limitation: one replaceable pending request and
unconditional player stop are unsuitable for repeated character echo. An
opt-in eight-entry character FIFO now preserves distinct accepted events,
while navigation and ordered speech retain their prior replacement and
ordering contracts. Portable A/B validation is required before acceptance.

## 2026-08-03 — Cancellation pipe-race classification

Package C's portable log showed four workerCrash messages. Source tracing found
that `interrupt()` terminated the child while `synthesize()` was blocked in
`_readFrame`; the closed pipe was reported as workerCrash before the
cancellation token check. The bridge now classifies that token-changing race
as cancellation while preserving genuine unchanged-token worker failures.
Portable revalidation is required before milestone acceptance.

## 2026-08-03 — Audio-only diagnostic and waveform guard

Added an excluded diagnostic for direct versus stop-before-feed PCM behavior
and content-free waveform analysis. A Lessac character fixture showed roughly
half-second duration with no exact-zero margins but low-energy edge runs. The
trim prototype therefore retains original PCM when a candidate would remove
more than half the waveform. WASAPI loopback and physical onset remain pending.

## 2026-08-03 — Portable validation harness

Added development-only `tools/portableNvdaValidation` tooling for safe archive validation, disposable `D:\NVDA` config ownership, unrelated-process refusal, child-only environment setup, PID-scoped cleanup, and content-free reports. No approved NVDA Spy/global-plugin input adapter exists in the pinned material, so objective scenarios are explicitly blocked rather than simulated or falsely passed. The production archive remains unchanged.

The restricted adapter protocol now adds per-run loopback authentication, exact command/fixture schemas, duplicate-ID and size limits, and a disposable global-plugin boundary. It intentionally returns an explicit unsupported result for UI fixture actions until the complete NVDA gesture/focus APIs are available in a verified source checkout; no arbitrary execution or false scenario pass was introduced.

## 2026-08-02 — Production chunk streaming rollback

Portable NVDA validation rejected the production incremental-chunk integration: perceived response was slower, typed characters were not spoken, document reading stopped, and navigation speech was not immediate. The preceding persistent warm full-request backend was materially better. Production stream frames, stream lifecycle states, and per-chunk `WavePlayer` feeding were reverted. Sonata/RT research and the excluded development prototype remain for reference; the runtime ADR remains Proposed.

## 2026-08-02 — Production incremental Piper chunks

The persistent local protocol now emits `streamStarted`, ordered bounded `pcmChunk`, `streamComplete`, and `streamFailed` frames. The worker retains one warm Piper voice/configuration and sends a content-free cancel frame rather than terminating the process for ordinary replacement. The background controller rejects stale chunks, feeds each current chunk immediately, calls `WavePlayer.idle()` once after segment completion, then dispatches indexes and final completion. A retained warm Lessac twelve-phrase request produced 12 ordered pipe chunks; first chunk arrival was approximately 114 ms and final arrival approximately 1,385 ms, compared with approximately 1.1–1.2 seconds before first full-buffer exposure. These remain worker/pipe metrics, not audible-onset claims. The runtime ADR remains Proposed.

## 2026-08-02 — RT model and chunk-streaming experiment

The official `en_US-lessac+RT-low` archive was inspected outside the project. Its encoder and decoder load successfully and expose a proven `z`/`y_mask` split, but Sonata publishes no public converter from a standard Piper ONNX graph. Public feasibility is therefore classified as not reproducible from an ONNX file alone. The approved standard Piper generator yields one chunk for short inputs but multiple sentence chunks for long inputs; the current production worker concatenates them before IPC. A development-only real-generator prototype now forwards each yield with generation checks and explicit environment activation. Warm tests measured first chunks around 62–109 ms for multi-sentence/long standard Piper input, while the direct RT encoder/decoder experiment produced three model chunks for navigation and first PCM around 183–242 ms. RT did not improve short first PCM and was not selected as the production backend. The runtime ADR remains Proposed.

## 2026-08-02 — Sonata architecture review

Primary-source review of the official Sonata NVDA and Rust repositories found a persistent server, long-lived `WavePlayer`, uncombined navigation strings, server-streamed PCM, and a separate `+RT` encoder/decoder voice variant. The gRPC protocol has no explicit generation or cancel RPC; dropping the stream stops delivery. RT output is model-chunk streaming, not frame streaming, and short one-shot requests can still yield one complete chunk. Cargo is unavailable and no official RT model is installed, so no real Sonata prototype measurement was fabricated. Research documents record the evidence and next development-only streaming experiment. The runtime ADR remains Proposed.

## 2026-07-30 — Repository foundation

### Context

The project was created to investigate a maintained NVDA synthesizer driver for Piper-compatible local neural voices. The initial motivation includes better multilingual neural speech and a practical path for Persian voices, while keeping the implementation useful across languages.

### Environment

Development is not tied to one primary computer. GitHub will serve as the source of truth so work can continue across two Windows laptops.

Current local project path is intentionally omitted from shareable research.

Planned GitHub repository name:

`nvda-piper-driver`

### Completed

- Installed and configured Git.
- Installed Python and Visual Studio Code.
- Installed relevant VS Code extensions.
- Initialized the local Git repository.
- Created initial project directories.
- Downloaded the official NVDA developer guide.
- Cloned the current NVDA source into a local reference directory.
- Recorded the reference commit.
- Excluded the full NVDA checkout from this repository.

### Pinned NVDA reference

Commit:

`e98b2a14cbc166294b0bbbb15fe4295cd2e4dd61`

### Decision

No driver implementation will be generated until the current NVDA `SynthDriver` contract, speech-sequence types, cancellation semantics, audio path, threading expectations, and packaging rules are documented from source.

### Reason

AI-generated implementations can easily use outdated or invented NVDA APIs. Source-backed research reduces compatibility risk and gives the project a maintainable technical foundation.

### Next step

Publish the foundational repository, then complete Phase 1 research without production driver code.

## 2026-08-01 — Phase 1B runtime, ecosystem, and Store research

### Scope and evidence

Reviewed the pinned NVDA developer/add-on documentation, add-on handler/store code, speech manager, and built-in OneCore, SAPI5, and eSpeak drivers. Current online primary sources included NV Access's NVDA, AddonTemplate, addon-datastore submission/validation/review documentation, API-version metadata and Code of Conduct; current and archived Piper repositories; Sonata source/releases/issues; and Hear2Read/Store listings. Time-sensitive status was recorded with the access date and uncertain maintenance claims were left unresolved.

### Provisional decision

Prototype a long-running, non-networked x64 worker with persistent model loading, bounded/versioned IPC, generation IDs, immediate audio cancellation, stale-result rejection, and deterministic shutdown. Evaluate the current Piper backend in that boundary; retain a verified CLI behind the same boundary as fallback.

The ADR is Proposed, not Accepted. No driver, build script, binary, model, or benchmark was created in Phase 1B.

### Reasons and negative findings

Process isolation best addresses native crash and NVDA Python-ABI risk. Sonata release evidence supports evaluating this approach but also documents locked worker/update recovery and voice-loss migration failures. Current Piper licensing changed from the archived MIT-labelled repository to a GPL-3.0 successor embedding eSpeak NG; every binary and model therefore needs independent provenance and redistribution review. The Store performs automated integrity, metadata, API, URL, and VirusTotal checks but explicitly does not promise a human security/UX audit.

### Next gate

Before accepting the runtime decision, run the cold/warm latency, cancellation, stress, resource, crash, lifecycle, clean-machine, multilingual, and Persian benchmarks listed in `docs/piper-runtime-evaluation.md`. Before any public release, complete `docs/addon-store-readiness.md`; acceptance is not guaranteed.

## 2026-08-01 — Phase 1C detailed design and quality framework

### Design outputs

Converted Phase 1A/1B evidence into separate Proposed designs for lifecycle state, immutable speech jobs, worker IPC, PCM/audio notifications, model/voice management, configuration, error recovery, and security boundaries. Added layered testing and performance methodology, staged CI, objective accessibility criteria, governance/support and documentation plans, an external-source register, a critical repository-quality review, and exact Phase 2A–2J stop gates.

### Decisions retained

The leading architecture remains a child-only, non-networked, persistent worker with generation-tagged bounded messages and NVDA-side streamed PCM playback. `synthDoneSpeaking` is provisionally associated with final current-generation playback, not inference completion. Models are initially installed manually without network access and are stored separately from replaceable add-on files. None of these benchmark-dependent choices is Accepted.

### Negative findings and next step

The design set creates cross-document maintenance risk and must be consolidated into user help and operational policies before beta. There is still no add-on skeleton, driver, runtime, model, benchmark, security audit, legal clearance, or Store approval. Stop Phase 1 research expansion and perform Phase 2A only as defined in `docs/phase-2-implementation-sequence.md`.

## 2026-08-01 — Phase 2A metadata-only package

### Template and metadata decisions

Adopted the SCons structure from official AddonTemplate commit `44fb08643974f8d30791cebe36254474251ef162` without replacing the existing repository. The manifest uses internal name `nvdaPiperDriver`, numeric version `0.1.0`, and `updateChannel = dev`; `0.1.0-dev` was rejected because current Store validation accepts only numeric `major.minor[.patch]` versions. Both API fields are provisionally `2026.1.0`, matching pinned x64/Python 3.13 compatibility and the live non-experimental Store list, but safe NVDA installation testing remains a release blocker.

### Verification and boundary

The build produced an archive containing only `manifest.ini` and `doc/en/readme.html`. Eight metadata/archive checks passed, a clean rebuild succeeded, and member SHA-256 hashes matched. No safe portable NVDA environment was available, so installation, help launch, restart, and uninstall were deferred. No synthesizer, worker, Piper/ONNX runtime, audio, model, native dependency, network behavior, or public release was added. Phase 2B is the only next milestone: a minimal driver whose verified availability check returns false.

## 2026-08-01 — Phase 2B unavailable driver

### Verified interface boundary

Pinned `synthDriverHandler.getSynthList` discovers modules in `synthDrivers`, imports their `SynthDriver` class, and includes only classes whose `check()` succeeds. Added `addon/synthDrivers/nvdaPiperDriver.py` with the required module-matching name, description, base-class inheritance, abstract `speak()` implementation, and a side-effect-free class `check()` returning exactly `False`.

### Failure and scope decision

Unexpected `speak()` calls raise a concise `RuntimeError`. Silent return was rejected because it would hide a loader/selection invariant violation; the exception never includes or examines the speech sequence. No constructor, settings, supported commands/notifications, cancellation, pause, termination, runtime detection, Piper/ONNX dependency, worker, thread, audio, model, configuration, file, or network behavior was added. Safe portable-NVDA discovery and non-selection testing remains pending. Phase 2C is limited to controlled test-only mock discovery.

## 2026-08-01 — Phase 2C controlled availability

### Mechanism decision

Selected an exact, narrowly named, process-local environment marker after comparing an in-memory test flag, dependency-injected availability probe, and environment activation. The flag could not launch a separate portable NVDA process cleanly; dependency injection would create a premature runtime abstraction. The selected marker defaults false, matches one explicit value, is re-read without caching, is never written or logged, and is unsupported outside development testing. See `docs/mock-runtime-availability.md`.

### Lifecycle and limits

Construction repeats the availability check, rejects default/uncontrolled use, then delegates NVDA base initialization and records only an idempotent termination guard. Termination delegates base cleanup once. Hostile-sentinel tests prove `speak()` fails without inspecting user content. No safe portable NVDA copy was available, so actual normal/controlled loader visibility, selection, base configuration effects, help, and uninstall remain pending. No Piper/ONNX runtime, worker, audio, model, speech, thread, queue, subprocess, file, registry, settings UI, or network behavior was added. Phase 2D is next and must remain mock-driven.

## 2026-08-01 — Phase 2D mock lifecycle and settings

Pinned NVDA inspection confirmed that `SynthDriver.initSettings` and `AutoSettings.initSettings` initialize advertised settings and configuration behavior after construction, while `getSynthInstance` performs that step after instantiating the driver. Four designs were compared: no settings, one mock voice, mock voice plus rate, and mock voice plus rate and volume. One fixed `Mock Voice — No Speech` entry plus a strict `0..100` in-memory rate was selected as the smallest useful settings boundary; volume would only duplicate an inert numeric fixture.

The implementation has exactly initializing, ready, and terminated private states. Construction remains test-gated, initializes getters before base initialization, and owns no external resources. Because pinned `Driver.terminate()` saves advertised settings, inherited cleanup runs while the state remains ready; a `finally` transition then makes termination irreversible and prevents a second inherited cleanup call. Active voice/rate access after termination and all speech calls fail predictably; hostile sentinels remain uninspected. Project code does not persist settings, although current inherited NVDA settings/configuration and voice-dictionary behavior requires validation in a disposable portable profile. No safe portable NVDA environment was used. No speech-job conversion, Piper/ONNX runtime, worker, audio, model, thread, queue, subprocess, native, filesystem-discovery, or network functionality was added. Phase 2E is next.

## 2026-08-01 — Phase 2E immutable speech-job conversion

Pinned `speech.types.SpeechSequence` and `SynthDriver.speak` confirm that the driver-facing container is a `list` of strings and `SynthCommand` objects. Pinned command storage was inspected for index, character mode, language, break, rate, pitch, volume, and phoneme commands. The converter accepts only exact list/item types and rejects pipeline-only or subclass inputs. Prosody copies `_offset` and `_multiplier` because their calculated properties may consult global synthesizer configuration.

Frozen slotted records and a tuple preserve exact text and command order. Per-driver job, generation, and request counters start at one, advance only after successful complete conversion, contain no text/time/randomness, and fail at a documented 63-bit bound. A private driver method snapshots mock voice/rate and returns the job without retaining it; `speak()` remains disconnected and unavailable. Tests cover Persian and other exact Unicode forms, every supported record, hostile unsupported objects, malformed commands, failure atomicity, lifecycle, and setting snapshots. The underscore package is skipped by pinned NVDA discovery. No worker, protocol, Piper/ONNX runtime, queue, audio, model, cancellation, pause, notification, thread, subprocess, native, filesystem-discovery, or network functionality was added. Phase 2F is next.

## 2026-08-01 — Phase 2F bounded in-process fake protocol

Strict UTF-8 JSON was selected over a custom binary parser or Python-specific serialization. Current official Python documentation confirms the hooks needed to reject duplicate keys and non-standard non-finite values. Encoding uses explicit schemas, sorted compact keys, preserved Unicode, and no arbitrary object reconstruction. A 64 KiB pre-decode frame bound and provisional depth/item/text/phoneme/metadata bounds are centralized and tested.

The immutable version-1 protocol implements only hello, job acceptance, errors, and shutdown. One synchronous `FakeWorker` owns deterministic session, sequence, accepted-request, accepted-job, and shutdown state. Schema failures raise before state handling; valid state rejections return correlated errors and do not advance sequence. Accepted jobs are neither mutated nor retained, and state contains only numeric metadata. Capabilities explicitly deny synthesis, audio, cancellation, pause, models, streaming, and notifications. No driver integration changed: `speak()` remains disconnected. No subprocess, IPC transport, pipe, socket, shared memory, thread, queue, Piper/ONNX runtime, model, PCM, audio, cancellation, pause, notification, native, filesystem-discovery, or network functionality was added. The runtime ADR remains Proposed; Phase 2G is next.

All 51 source tests passed with the four archive-only tests skipped as designed. Each of two clean SCons builds passed; the built-archive run passed all 55 tests, the exact eight-member allowlist, manifest/help validation, and per-member SHA-256 comparison across clean rebuilds. Relative Markdown links, duplicate headings, malformed characters, forbidden imports/artifacts, manifest consistency, and `git diff --check` were checked before generated outputs and local caches were removed. No real NVDA installation was used or required because the driver remains disconnected.

## 2026-08-01 — Phase 2G mock cancellation and stale generations

Pinned NVDA inspection confirmed that `SpeechManager` calls synth cancellation on interruption, clears its active indexes, and treats later unknown index callbacks as probably cancelled. Phase 2G copies no NVDA implementation. It selects a simpler fake-only rule: generation 1 starts first, the active generation may accept multiple jobs, and only the contiguous successor may advance state. Advancement makes older generations stale; explicit current-generation cancellation is idempotent.

The version-1 protocol adds immutable cancel request/response and metadata-only fake-result request/response records. Fake-result statuses distinguish current, stale, cancelled, unknown-job, and duplicate metadata without carrying synthesis, PCM, audio, index, completion, text, or timing data. The fake worker retains bounded numeric request, generation, job, cancellation, and accepted-result identifiers only. Limit failures and malformed/state rejections are atomic; successful/idempotent cancellation and all fake-result status responses advance protocol sequencing.

Deterministic tests exercise hundreds and thousands of synchronous operations, fill every retained collection, redeliver cancelled/stale/duplicate results, and verify privacy and irreversible shutdown without sleeps, threads, queues, or performance claims. `SynthDriver.speak()` remains disconnected, `SynthDriver.cancel()` is not implemented, and no NVDA notification exists. No subprocess, IPC transport, Piper/ONNX runtime, model, synthesis, PCM, audio, native, filesystem-discovery, timing, or network functionality was added. Limits remain provisional and the runtime ADR remains Proposed. Phase 2H is limited to integrating and benchmarking one verified Piper runtime for standalone synthesis outside NVDA, without connecting it to the NVDA driver.

## 2026-08-01 — Phase 2H standalone runtime verification

Current primary-source review selected OHF-Voice `piper-tts` 1.5.0 for a standalone Python-API experiment. It offers current Windows x64 ABI3 packaging, explicit compatible-model paths, multi-speaker metadata, and sentence-chunk iteration. The CLI, native library, direct ONNX Runtime, and maintained `piper-plus` successor/fork were reconsidered. Selection was based on Piper model compatibility and testability, not a language; the adapter contains no locale or script branch and Persian is not a special path.

The official `en_US-lessac-low` model and configuration were restored to an ignored local asset directory and matched their recorded SHA-256 hashes. The prior ONNX Runtime failure was resolved by interactively installing the Authenticode-valid Microsoft Visual C++ x64 runtime 14.51.36247.0. ONNX Runtime 1.28.0 then exposed CPU and Azure providers; the adapter selected CPU. Pure and runtime-dependent tests passed, a real mono 16-bit 16 kHz WAV was structurally validated, and five-run standalone startup/load/synthesis/RTF measurements plus a sampled process-resource observation were recorded. Generator closing stopped future sentence iteration but did not prove active-inference interruption. Phase 2H exit criteria are met, while licensing, dependency locking, process isolation, playback, NVDA behavior, and hard cancellation remain unresolved. The runtime ADR remains Proposed; Phase 2I is not started or implicitly approved.

## 2026-08-01 — Phase 2I first portable-NVDA speech prototype

The authorized `D:\NVDA` 2026.1.1 AMD64 portable copy was started with explicit configuration and log paths below `D:\NVDA`, loaded bundled eSpeak NG, initialized, and exited cleanly before code changes. Pinned `nvwave.WavePlayer` evidence established the mono/sample-rate/sample-width construction and `feed`, `idle`, `stop`, and `close` path. Direct in-process Piper, a child worker, and a CLI wrapper were reconsidered. A one-shot child using the already verified Python API was selected to preserve native isolation without adding a queue, background synthesis, persistent worker, or new runtime interface.

The development driver now requires the unchanged exact Phase 2C marker plus explicit runtime, model, and configuration files. It creates an immutable job, sends bounded content to one child, validates correlated mono 16-bit PCM, and drains it through NVDA's configured `WavePlayer`. Cancellation is teardown only: invalidate current PCM, stop playback, and terminate the child. There is no language branch, WAV retention, user-text logging, runtime/model packaging, active-inference cancellation claim, index support, or Phase 2J work. The user heard the controlled Piper fixture and the subsequent eSpeak fixture, confirming synthesis and switching; both runs exited cleanly with no surviving worker or info-level error. Phase 2I exit criteria are met and the runtime ADR remains Proposed.

All 62 source tests passed with the four archive-only tests skipped as designed. The built-archive run passed all 66 tests and the unchanged exact eight-member allowlist. Two clean SCons builds succeeded and every archive member's SHA-256 digest matched. Syntax, manifest, relative-link, duplicate-heading, malformed-character, forbidden-import/artifact, and `git diff --check` validation completed before generated outputs and caches were removed.

## 2026-08-01 — Phase 2J bounded background execution

Pinned `nvwave` confirms that `feed()` and `idle()` block, while the pinned SAPI driver uses `WavePlayer.stop()` to stop audio and release an `idle()` wait. Pinned `queueHandler.eventQueue` is explicitly the main-thread call queue. Four architectures were compared; a single non-daemon controller around repeated one-shot children was selected as the narrowest change preserving Piper/ONNX process isolation without prematurely designing a persistent production protocol.

The controller has one active request and one overwrite-only pending slot. `speak()` performs bounded immutable conversion and submission only. Child startup, cold model load, inference, complete PCM transfer, bounded playback feeds, and drain run on the controller thread. New speech and idempotent cancellation invalidate the generation, clear/replace pending work, stop local playback, and send a non-waiting child termination request. Both PCM acceptance and queued completion are generation checked. Active ONNX inference still has no cancellation token, indexes remain unsupported, and the runtime ADR remains Proposed. Automated and retained-runtime verification precede the separately authorized portable-NVDA run.

Corrected portable launches used numeric `--log-level 20`; the earlier `INFO` value was rejected by pinned argument parsing. Normal mode loaded eSpeak, hid the gated driver, and exited normally. Removable content-free UI diagnostics later proved that three fresh selection-dialog constructions received and displayed `nvdaPiperDriver`; the user confirmed both supported UI paths, resolving the earlier observation without a code change.

The final controlled run selected the driver, but ordinary NVDA speech failed before background submission. Pinned `SpeechManager` appends an `IndexCommand` to every utterance, conversion preserves it, and the Phase 2J index-free `_extractText()` rejects it. The log contained 57 content-free tracebacks, no watchdog recovery or speech payload, and no child ever started. The user restored audible eSpeak and exited normally with no surviving process. Responsive synthesis, replacement, cancellation, stale suppression, completion, and timing remain unvalidated. Phase 2J remains incomplete and the runtime ADR remains Proposed.

The minimal compatibility correction accepts immutable `IndexItem` metadata solely because NVDA appends it to ordinary managed utterances. Extraction still accepts only exact `TextItem` content, traverses items deterministically, discards indexes without separators, forwarding, retention, or notification, and rejects text-empty jobs plus every other command family with bounded content-free errors. Tests cover final and interleaved indexes, index boundaries already represented by the job model, Persian and mixed Unicode, source immutability, controller submission, completion, stale behavior, and the absence of index notification. Portable validation remains pending; the runtime ADR remains Proposed.

The corrected package was deployed only to the authorized portable configuration and its installed member hashes matched the validated archive. The driver selected, but the user heard no Piper output and restored audible eSpeak. Eight content-free rejections occurred before controller submission. The portable profile inherits pinned `autoLanguageSwitching=true`; pinned speech processing inserts and passes a `LangChangeCommand`, Phase 2E converts it to `LanguageChangeItem`, and the deliberately text/index-only Phase 2J extractor rejects it. No child, PCM, playback, or completion ran. There was no watchdog, critical/background error, audio artifact, surviving NVDA, or surviving worker, but the tracebacks fail the exit criteria and demonstrate remaining error flooding. The mandatory-index correction is retained; language-change or broader item support is not added in this task. Phase 2J remains incomplete and the runtime ADR remains Proposed.

The next minimal compatibility change accepts exact `LanguageChangeItem` metadata alongside exact `IndexItem`, ignores both without separators, and submits only concatenated `TextItem` content. It neither reads nor retains locale values, forwards no metadata, changes no explicit runtime/model/configuration path, and advertises no language command or notification. Metadata-only jobs use the existing content-free empty error; break, character mode, prosody, phoneme, subclasses, and arbitrary items remain unsupported. Tests cover language placement, repetition, `None`, multilingual Unicode, metadata-only jobs, payload/retention absence, nonblocking submission, completion/cancellation/stale gates, one-error/no-retry behavior, and later valid recovery. Portable validation remains pending and the runtime ADR remains Proposed.

## 2026-08-02 — Phase 2J language-compatible validation and rejection containment

The final controlled portable run used the exact Phase 2C marker, explicit ignored runtime/model/configuration paths, portable configuration, and numeric log level 20. NVDA listed and selected the driver. The user heard Piper review speech and stopped it with Ctrl, but reported noticeable latency; typed-character echo did not occur and Read All did not proceed correctly. These remain outside the deliberately narrow Phase 2J command boundary. The user had previously confirmed audible eSpeak fallback without Piper resuming.

Pinned NVDA event handling does not catch exceptions from `SynthDriver.speak()`. The driver now catches only its own fixed extraction rejections and emits at most one content-free warning during a consecutive rejection episode, resetting after valid text. This keeps unsupported character/prosody/break/phoneme commands unsupported while preventing traceback event arguments from exposing input. The final log had zero tracebacks, critical/error, watchdog, recovery, or worker entries; 14 fixed unsupported-item warnings were recorded, with no speech text or language values. After manual closure, no NVDA or runtime worker remained. Phase 2J remains incomplete because latency, Read All/typed-character behavior, exact replacement, and completion timing do not meet or establish the phase exit criteria. The runtime ADR remains Proposed.

## 2026-08-02 — eSpeak baseline and Read All boundary

Pinned eSpeak source handles character mode, breaks, prosody, phonemes, language tags, SSML marks, native cancellation, and both index and completion notifications. The corresponding NVDA paths show typed characters wrapped in `CharacterModeCommand`, typed words submitted as ordinary text, and Read All callbacks converted into indexes by `SpeechManager`. Read All's `lineReached`/next callbacks run only from `_handleIndex()` after `synthIndexReached`; `synthDoneSpeaking` alone cannot advance the reader.

Because Phase 2J intentionally discards indexes and advertises no index notification, Read All cannot be made correct by changing completion timing. The task explicitly requires stopping when this dependency is proven, so no fabricated index, callback interception, or Read All workaround was implemented. CharacterMode, Break, prosody, and phoneme items remain explicitly unsupported rather than silently discarded. New documents record the command policy, source-derived sequence shapes, qualitative eSpeak comparison, standalone warm Piper measurements, and the decision matrix for a future persistent worker, streaming, cache, lower-latency model, or optional eSpeak character fallback. The runtime ADR remains Proposed.
## 2026-08-02 — Persistent worker and real index boundaries

Phase 2J was extended after portable evidence showed that completion could not advance Read All and CharacterMode was rejected. The selected development design is one non-daemon controller thread with one persistent child, one active request, and one replaceable pending request. Piper model loading now occurs once per session; framed segment requests preserve CharacterMode and IndexItem boundaries. The controller queues `synthIndexReached` after each segment's actual playback and queues final completion afterward. Cancellation invalidates the generation and terminates the child without waiting on the caller thread. Retained Lessac integration passed multiple warm requests and ordered callbacks; portable validation remains required. The runtime ADR remains Proposed.

Phase 2K established a reproducible bridge baseline using the retained Lessac model and CPU runtime. Warm character, digit, punctuation, word, and control requests measured approximately 25–30 ms; a short navigation phrase measured approximately 39 ms; a short sentence measured approximately 79 ms. Fresh-worker startup remained approximately 2 seconds after model load, so cold latency is dominated by model initialization rather than framing. Piper yielded one complete chunk for each tested short, sentence, and long case; frame-level streaming was not claimed. The worker now performs a silent empty synthesis before readiness and reuses one `SynthesisConfig` for its lifetime. A bounded PCM cache and ONNX thread/affinity tuning were rejected because the benchmark did not prove broad benefit and would add settings/invalidation complexity. Phase 2K remains focused on latency and the runtime ADR remains Proposed.

The hash-verified validation model and pinned local build environment were restored. A rerun measured one-shot short requests at approximately 2 seconds and persistent warm requests at approximately 24–51 ms; cancellation returned in under 1 ms, with a cold restart required after hard termination. The persistent bridge now detaches and asynchronously reaps a terminating process, eliminating the replacement race observed when a new request arrived before Windows updated `poll()`. Focused bridge/controller tests pass with ResourceWarnings treated as errors. The runtime ADR remains Proposed.

Phase 2K follow-up investigation added bounded monotonic traces for speech entry/return, controller submission/start, first PCM receipt, first `WavePlayer.feed()`, and playback drain. The trace contains request/generation IDs and timestamps only. The available Piper generator produced one complete chunk per retained-model request, so no frame-streaming improvement was claimed. Input-hook and physical audio callback timestamps are not exposed safely by the current development boundary; portable correlation remains required.
