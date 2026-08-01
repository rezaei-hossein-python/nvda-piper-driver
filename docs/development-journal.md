# Development Journal

## 2026-07-30 — Repository foundation

### Context

The project was created to investigate a maintained NVDA synthesizer driver for Piper-compatible local neural voices. The initial motivation includes better multilingual neural speech and a practical path for Persian voices, while keeping the implementation useful across languages.

### Environment

Development is not tied to one primary computer. GitHub will serve as the source of truth so work can continue across two Windows laptops.

Current local project path on this laptop:

`C:\projects\nvda piper addon`

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
