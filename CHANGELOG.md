# Changelog

All notable user-visible changes will be documented in this file.

The project has not released a public version.

### Sonata architecture research

- Added primary-source Phase 2K documentation for Sonata NVDA/Rust architecture, RT voices, streaming, cancellation, licensing, and the deferred prototype decision. No Sonata binary or code is packaged.

### RT model experiment

- Added ignored-model graph analysis and a development-only, explicitly gated real Piper chunk-streaming prototype. The production backend remains unchanged.

### Production chunk streaming rollback

- Reverted the production chunk-streaming integration after portable NVDA validation showed slower perceived response, missing character echo, stopped document reading, and non-immediate navigation speech. The persistent warm full-request backend is restored; the streaming work remains documented as a rejected development experiment.

## Unreleased

### Phase 2L experiment

- Added an explicitly gated, bounded selected-voice character PCM cache and
  conservative short-unit classification. The Phase 2K control path remains
  unchanged unless both experimental environment variables are enabled.
- Added a development-only category scheduler: accepted character events use a
  bounded FIFO while navigation/focus remains newest-wins and ordered speech
  remains unchanged.
- Added an excluded audio-only diagnostic and conservative, opt-in character
  waveform analysis/trim prototype. No acceleration dependency or audible-onset
  claim is included.

### Added

- Initial repository structure.
- Project mission, goals, non-goals, and development principles.
- Architecture and implementation-planning documents.
- AI-agent development rules.
- Contribution guidance.
- Development journal and roadmap.
- Pinned local NVDA source-reference metadata.
- Phase 1B Piper runtime evaluation and proposed process-isolated runtime ADR.
- Source-backed review of Sonata, Hear2Read NG, and built-in NVDA synthesizer patterns.
- Add-on Store readiness, native dependency, security, accessibility, licensing, and release checklists.
- Phase 1C detailed lifecycle, job, worker protocol, audio, model, configuration, error-recovery, and threat-model designs.
- Testing, CI, accessibility acceptance, governance, support, documentation, source-register, repository-quality, and exact Phase 2 implementation plans.
- AddonTemplate-aligned metadata-only package generation, localizable manifest text, packaged English help, and focused archive validation.
- A minimal `nvdaPiperDriver` synthesizer module that remains deliberately unavailable because `check()` returns `False`.
- An exact, process-local, test-only availability gate for isolated discovery, construction, and termination validation.
- A three-state mock lifecycle, one explicitly non-speaking mock voice, and a bounded in-memory rate fixture for NVDA settings-boundary validation.
- Pure conversion of pinned driver-facing NVDA sequence items into immutable, ordered speech-job records with deterministic in-memory identifiers.
- A bounded, strict-JSON protocol model and synchronous in-process fake worker for handshake, correlation, validation, controlled errors, and shutdown tests.
- Synchronous in-process mock cancellation, contiguous generation invalidation, metadata-only fake-result classification, and bounded deterministic stress tests.
- A development-only one-shot child bridge and bounded PCM playback path for the first controlled portable-NVDA utterance.
- A bounded non-daemon background controller with one active request, one replaceable pending slot, prompt generation invalidation, stale PCM/completion rejection, background playback drain, and bounded shutdown.
- Narrow compatibility for NVDA's mandatory final index item: it is accepted as non-synthesized metadata, never forwarded or retained, and does not enable index notifications.
- Narrow compatibility for NVDA's automatic language-change metadata: it is ignored by the explicitly selected single-model path without validation, inference, voice switching, retention, forwarding, or notification.
- Unsupported Phase 2J speech sequences are now rejected locally with bounded content-free warnings instead of escaping into NVDA event tracebacks; no additional speech-command support was added.
- Added source-backed Phase 2J eSpeak baseline, character/Read All compatibility policy, and Piper interactive-performance evidence. Read All remains blocked on required index callbacks; no fabricated index or hybrid output path was added.

- Phase 2J now uses a persistent bounded child worker, real index-delimited segment callbacks, and isolated CharacterMode segments. The worker loads one configured model per session, supports one active plus one replaceable request, and uses bounded termination for cancellation; portable interaction validation remains pending.

- Phase 2K measured persistent-worker latency, added a silent language-neutral startup warm-up, and reused one Piper synthesis configuration per worker. Warm short bridge requests measured approximately 25–30 ms; cold startup remained dominated by model loading. No cache, language-specific optimization, runtime packaging, or eSpeak fallback was added.

- Phase 2K validation restored the approved local model and build tools. Persistent cancellation now detaches and reaps the terminating worker asynchronously so replacement cannot race a stale process; hard cancellation still requires a cold model reload.

- Phase 2K added bounded content-free monotonic latency traces through first `WavePlayer.feed()` and playback drain. These traces make worker-to-audio-device boundaries measurable without retaining speech text; physical audible onset still requires portable validation.

The driver remains unavailable in normal use. Phase 2J replaces Phase 2I's blocking call with bounded background execution around one-shot Piper children. It retains only one replaceable pending request, stops stale playback, and rechecks completion on NVDA's event queue. Text plus index/language metadata now crosses the extraction boundary; metadata is ignored, no index or language notification exists, and renewed portable validation remains pending. Active ONNX inference still has no cancellation token; termination is the fallback. There is no broader command support, pause/resume, automatic model/voice switching, model discovery, language-specific behavior, or bundled runtime/model asset. The package is not a public release.
