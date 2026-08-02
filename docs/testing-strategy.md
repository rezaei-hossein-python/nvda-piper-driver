# Testing and benchmarking strategy

## Principles

Tests follow the architecture boundary: pure conversion/state logic first, fake worker/audio next, real runtime standalone, then NVDA integration. No test logs user text. Deterministic clocks, IDs, fake processes, and fault injection make races repeatable. Real-model tests use only a separately acquired, verified, licence-reviewed fixture that is never committed.

## Layers

### Pure unit tests

- Speech-job conversion for every supported command, ordering, consecutive indexes, empty text, phoneme fallback, chunk boundaries, and unsupported-command policy.
- Generation invalidation, idempotent cancellation, exactly-one outcome/completion gate, queue replacement, and every allowed/forbidden state transition.
- Configuration types/ranges/defaults/migrations and newer-schema/downgrade behavior.
- Model metadata/schema/path/digest/duplicate/size parsing without loading ONNX.
- Error-to-policy/message mapping and redaction sentinel tests.
- Protocol frame serialization, schema/version/enums/order/size validation, unknown fields, truncation, and fuzz/property cases.

### Worker tests

Fake/controlled child tests cover handshake/capability intersection, wrong versions, startup timeout, load/unload atomicity, synthesis chunks, backend failure, cancel acknowledgement, unresponsive child termination, crash at every phase, malformed frames, orderly shutdown, parent disappearance, and orphan absence. Real runtime tests are a separate marked suite.

### Audio tests

Use a fake player to assert PCM format, chunk order, bounded buffers/backpressure, stale rejection, stop versus drain, pause/resume, one completion after final played, index callbacks, and device errors. Manual/controlled-device tests cover actual default-device changes and sleep/resume. Generated audio stays temporary and untracked.

### NVDA integration tests

On pinned/current supported NVDA: discovery, unavailable `check`, selection/deselection/fallback, speech, indexes, done, cancel/priority replacement, settings and voice changes, worker failures, shutdown, installed and portable configurations. Use NVDA system-test mechanisms only after verifying current documentation; manual testing remains necessary where automation is unsafe.

Phase 2C adds a narrower pre-integration layer: isolated tests patch only the exact process environment marker, import the driver against one `SynthDriver` stub, simulate loader inclusion from `check()`, verify base construction/one-time termination, and pass a hostile non-inspectable speech sentinel. This does not replace real portable-NVDA discovery and selection-list validation, which remains deferred.

Phase 2D extends only that isolated layer. Tests require exactly the initializing/ready/terminated states, one fixed non-speaking voice, strict in-memory rate validation, irreversible one-time base termination, failure of active settings after termination, and hostile-sentinel speech failures in ready and terminated states. The stubs do not exercise NVDA's real configuration callback, settings ring, or voice-dictionary behavior; disposable portable-NVDA validation remains pending.

Phase 2E adds pure tests for frozen job/item records, exact list input, exact driver-facing command types, text fidelity including Persian and Unicode controls, command-field preservation, malformed and unsupported inputs, failure-atomic counters, identifier exhaustion, settings snapshots, and lifecycle gating. Narrow command stubs mirror the pinned field contracts without importing the full NVDA application. These tests do not establish synthesis safety or runtime support for any represented command.

Phase 2F tests immutable protocol values, deterministic UTF-8 JSON, explicit item schemas, frame/depth/text/phoneme bounds, malformed encoding/JSON and duplicate keys, non-finite numbers, handshake/session/sequence invariants, request/job correlation and duplication, metadata-only retention, state-error behavior, and irreversible fake shutdown. These synchronous tests contain no IPC, timing, process, PCM, or audio evidence.

Phase 2G adds deterministic synchronous loops for contiguous generation progression, idempotent cancellation, stale/cancelled/unknown/duplicate fake-result statuses, atomic request/generation/job/result/cancellation tracking limits, privacy, and shutdown. Fake results contain numeric metadata only. The tests use no sleeps, clocks, threads, queues, transport, synthesis, audio, or performance claims.

Phase 2H adds pure standalone adapter and benchmark tests for bounded path/config/text/output validation, Unicode preservation, optional metadata-driven speakers, content-free errors, structured metrics, WAV parsing, and network/language-hardcoding exclusions. One runtime/model-dependent test skips unless explicit local paths are supplied; with the hash-verified local model it passed model loading and real synthesis. The benchmark records one discarded warm-up, five runs per case, individual and min/median/max results, and structural WAV metadata. These tests do not establish NVDA, playback, or active-inference cancellation behavior.

### Accessibility acceptance

Execute `docs/accessibility-acceptance-criteria.md` with keyboard and NVDA: focus/order/names/states, validation and recovery, manual model import, progress/cancel, first run, restart prompts, help navigation, localization, and announcement rate.

## Performance methodology

Measure cold worker start, cold model load, warm first PCM, first audible output, synthesis completion, real-time factor, cancel-to-silence, cancel-to-worker-idle, private/working memory, CPU time/utilization, handles, threads, queue high-water, repeated short speech, rapid arrow navigation, long text, cancellation races, and language/model switching.

Record machine/CPU/RAM/storage, Windows/NVDA/add-on/runtime versions, power state, audio device/format, model/config hashes and metadata, corpus hash, warm-up count, timestamps from one monotonic clock where possible, repetitions, failures, and median/tail distributions. Separate inference from playback. Never compare unlike models/hardware as an architecture claim.

**Experimental thresholds** are explicitly labelled hypotheses used to detect gross regressions during Phase 2; derive them from baseline runs and revise openly. **Release requirements** are set only after representative hardware/community measurements and user feedback. No numeric threshold is defined in Phase 1C.

## Reliability and soak

Automate thousands of fake synthesis/cancel/voice-change cycles, worker restart/crash loops, NVDA adapter creation/termination, memory/handle/thread trend checks, and protocol fuzzing. Run real-runtime overnight synthesis/cancel with bounded retained metrics. Manually test repeated NVDA restart, sleep/resume, device changes, upgrade/downgrade/uninstall, and verify no child or temporary file remains.

## Release matrix

| Dimension | Required coverage |
|---|---|
| NVDA | Declared minimum, each supported release family, current stable; beta/dev only for matching channel |
| Windows | Every Windows x64 version NVDA and project explicitly support at release time |
| Install mode | Installed and portable NVDA where applicable; clean machine without developer runtimes |
| Lifecycle | clean install, upgrade, documented downgrade, disable/enable, uninstall/reinstall, restart |
| Faults | missing/corrupt/unsupported model, missing/quarantined runtime, invalid config, device loss, worker crash/hang |
| Languages | Persian, English, and one additional Piper language using a different locale/phoneme path where possible |

Pure, fake-worker/audio, serialization, metadata, and most standalone runtime tests automate in CI. NVDA GUI/audio/portable-installed, physical device, sleep/resume, audible correctness, keyboard UX, Persian pronunciation, and clean-machine antivirus checks require manual or dedicated Windows test environments.

## Exit evidence

Every milestone records commands, versions, machine profile, result artifacts that contain no private text/audio, known flakes, and unresolved failures in the development journal. Performance claims require a reproducible harness committed only when implementation begins.
