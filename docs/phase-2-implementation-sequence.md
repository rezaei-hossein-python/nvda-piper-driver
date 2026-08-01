# Phase 2 implementation sequence

## Rules for every milestone

Each milestone is a separate review and focused commit. Stop after its exit criteria; do not pre-create later files. Always forbidden: `references/nvda-source/`, imported references, downloaded/bundled unverified assets, telemetry/network, and unrelated docs. Update `CHANGELOG.md` only for user-visible behavior and `docs/development-journal.md` for meaningful decisions/results. File names below are design permissions; exact AddonTemplate layout is verified in 2A.

Mock-first development proves lifecycle, cancellation, protocol, and stale-event correctness deterministically before native crashes, model latency, licensing, and audio obscure defects. It also allows most design reversal without shipping a runtime.

## Phase 2A — AddonTemplate-aligned skeleton and manifest only

**Completed 2026-08-01.** The metadata/help package and its build evidence are documented in `docs/build-and-package.md`. Controlled NVDA installation testing remains pending and no public release exists.

- **Objective:** adopt the current official template/build metadata with no driver.
- **Allowed:** root template/config files, manifest templates, `addon/doc/`, locale placeholders, repository docs, minimal packaging fixtures explicitly produced by tests but untracked.
- **Forbidden:** `addon/synthDrivers/`, worker/runtime/audio/model code, native assets, real voice configuration.
- **Tests:** manifest/schema/API metadata, package content, UTF-8 paths, reproducible clean build where feasible.
- **Manual:** inspect archive contents; install only if a no-code package is safe and milestone plan explicitly permits it; verify help metadata/keyboard access.
- **Docs:** developer/build setup, journal, roadmap/status.
- **Commit:** `Create AddonTemplate-aligned add-on skeleton`
- **Exit:** current template provenance recorded; package contains only expected docs/metadata; no synth driver. Stop.

## Phase 2B — Minimal unavailable driver

**Completed 2026-08-01.** The package contains only the unavailable driver, manifest, and help. Isolated tests prove `check()` returns exactly `False`; controlled NVDA installation testing remains pending.

- **Objective:** define only verified `SynthDriver` identity and a safe `check()` returning false.
- **Allowed:** one driver module, pure availability tests, relevant docs.
- **Forbidden:** construction, speech, worker, audio, settings, Piper dependencies.
- **Tests:** import with NVDA test doubles/verified environment; `check` deterministic false; no side effects/network/log text.
- **Manual:** NVDA starts; driver is not selectable/discoverable per verified behavior.
- **Docs/commit:** journal and interface traceability; `Add unavailable Piper synthesizer driver`.
- **Exit:** no crash/import error and no selectable nonfunctional driver. Stop.

## Phase 2C — Controlled mock discovery

**Completed 2026-08-01.** Exact process-local test activation controls discovery and base-only lifecycle validation. The normal default remains unavailable, and real NVDA validation is pending.

- **Objective:** make `check()` true only with an explicit test-only mock-runtime marker/dependency.
- **Allowed:** availability abstraction and test fixture outside release package.
- **Forbidden:** real Piper, audio/speech, broad settings.
- **Tests:** absent/valid/invalid mock, architecture/version/error paths, package excludes marker.
- **Manual:** controlled NVDA profile shows driver only with mock; normal profile does not.
- **Docs/commit:** document activation safety; `Gate driver discovery on controlled mock runtime`.
- **Exit:** discovery is reversible, offline, and cannot be enabled accidentally in release. Stop.

## Phase 2D — Lifecycle and settings skeleton with mocks

**Complete. Phase 2E is the sole next milestone.**

- **Objective:** implement only initializing/ready/terminated lifecycle states, one fixed mock voice, and an in-memory rate fixture.
- **Allowed:** controller/state/config interfaces, fake dependencies, unit tests.
- **Forbidden:** job conversion beyond placeholders, worker process, real playback/runtime.
- **Tests:** all transitions/invariants/termination, invalid config, voice change, main-thread call duration under mocks.
- **Manual:** select/deselect, settings ring/dialog only if controls exist, shutdown without handles.
- **Docs/commit:** reconcile state/schema; `Implement mocked driver lifecycle and settings`.
- **Exit:** deterministic idempotent teardown and mock settings-boundary tests completed without speech or runtime resources. Stop.

## Phase 2E — Speech-job conversion with mocks

**Complete. Phase 2F is the sole next milestone.**

- **Objective:** convert pinned NVDA sequences into immutable jobs.
- **Allowed:** pure job/command modules and fixtures.
- **Forbidden:** process/audio/runtime, advertising unimplemented commands.
- **Tests:** all cases in `speech-job-model.md`, especially indexes/order/privacy/empty/fallback.
- **Manual:** optional debug harness reports only structure/counts, never text.
- **Docs/commit:** supported-command matrix; `Convert NVDA speech sequences into immutable jobs`.
- **Exit:** pure deterministic conversion and no logs containing sentinel text. Stop.

## Phase 2F — Fake-worker protocol prototype

**Complete. Phase 2G is the sole next milestone.**

- **Objective:** validate bounded serialization, immutable envelopes, session/handshake, correlation, controlled errors, and shutdown with a synchronous in-process fake worker.
- **Allowed:** pure protocol values, strict standard-library serialization, direct fake-worker state machine, and focused unit tests.
- **Forbidden:** subprocesses, IPC or transport abstractions, threads, queues, Piper/ORT/model/audio integration, cancellation, and driver speech integration.
- **Tests:** message/item round trips, limits, malformed frames, handshake, strict sequencing, duplicate detection, metadata-only retention, and irreversible shutdown.
- **Manual:** inspect source/archive boundaries; real NVDA validation is unnecessary because `SynthDriver.speak()` remains disconnected.
- **Docs/commit:** record provisional prototype limits without accepting the worker architecture; `Prototype bounded worker protocol with fake worker`.
- **Exit:** deterministic in-process behavior with no speech, process, transport, runtime, model, PCM, or audio. Stop.

## Phase 2G — Cancellation and stale-generation behavior

**Next milestone. Do not start other Phase 2 work concurrently.**

- **Objective:** prove generation invalidation end to end with fake worker/audio.
- **Allowed:** controller/job/protocol fake-player integration and stress tests.
- **Forbidden:** real TTS/native audio claims.
- **Tests:** cancel at every phase, rapid replacement, late/duplicate/out-of-order PCM/index/done, one outcome, circuit breaker.
- **Manual:** mock NVDA navigation stress; inspect announcements/log redaction.
- **Docs/commit:** update state/job/error evidence; `Reject stale speech after cancellation`.
- **Exit:** deterministic stress suite has no stale delivery or leaks. Stop.

## Phase 2H — Verified Piper standalone synthesis

- **Objective:** acquire/build separately and integrate one reviewed Piper runtime/model in the standalone worker only.
- **Allowed:** pinned dependency acquisition/build design, inventory/notices/SBOM, standalone worker backend and marked tests.
- **Forbidden:** committing downloaded model/binary until separately authorized; NVDA audio/speech integration.
- **Tests:** provenance/hash/schema/load/synthesize/shutdown/fault/resource and baseline measurements.
- **Manual:** clean x64 standalone run; delete temporary audio; licence/security review.
- **Docs/commit:** runtime/version/model evidence and benchmark report; `Integrate verified Piper runtime in standalone worker` (only if authorized assets strategy is resolved).
- **Exit:** reproducible offline standalone synthesis and unresolved redistribution issues explicitly block packaging. Stop.

## Phase 2I — First speech inside NVDA

- **Objective:** feed verified PCM through the selected current NVDA-compatible audio path for plain text.
- **Allowed:** narrow audio adapter and plain-text integration.
- **Forbidden:** broad commands/settings/downloader/Store claims.
- **Tests:** fake/real PCM order, final playback completion, device failure, repeated short speech, cleanup.
- **Manual:** one short English and Persian utterance, select/deselect/shutdown, responsiveness observation with measured timestamps.
- **Docs/commit:** audio findings/limitations; `Speak plain text through NVDA with Piper`.
- **Exit:** first speech without hang/leak; architecture ADR still Proposed. Stop.

## Phase 2J — Real cancellation, indexes, and completion

- **Objective:** meet the minimum functional SynthDriver signaling/interruption behavior.
- **Allowed:** generation cancellation, index/audio alignment, notifications, stress/integration tests.
- **Forbidden:** downloader, extra prosody/language automation, release expansion.
- **Tests:** cancel-to-silence/idle, index order/timing, done exactly once after final played, failures, rapid navigation, soak.
- **Manual:** character/word/line/say-all interruption, pause/resume, device change, English/Persian/additional language.
- **Docs/commit:** measured results, accepted/reversed ADR proposal in a separate later decision only; `Implement Piper speech cancellation and progress signaling`.
- **Exit:** reproducible minimum behavior and benchmark evidence exist. Stop before broader phases.
