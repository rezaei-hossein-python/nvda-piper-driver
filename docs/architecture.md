# Architecture

## Status

This document maps the detailed provisional architecture after Phases 1A–1C. The runtime decision remains Proposed until the proof-of-concept measurements in `docs/architecture-decision-runtime.md` exist. Implementation has not begun.

Detailed specifications are in `docs/driver-state-machine.md`, `docs/speech-job-model.md`, `docs/worker-protocol.md`, `docs/audio-pipeline.md`, `docs/model-and-voice-management.md`, `docs/configuration-schema.md`, `docs/error-handling-and-recovery.md`, and `docs/security-threat-model.md`.

## Design objectives

The system should provide local neural speech without compromising NVDA responsiveness, interruption behaviour, accessibility, privacy, or stability.

## Proposed components

### 1. NVDA adapter

Responsibilities:

- implement the current NVDA synthesizer-driver contract;
- expose supported voices and settings;
- accept NVDA speech sequences;
- translate supported speech commands;
- initiate synthesis without blocking NVDA's main thread;
- cancel current and queued speech;
- report indexes and completion using current NVDA mechanisms;
- surface actionable failures.

This layer should contain as little Piper-specific logic as possible.

### 2. Speech-sequence processor

Responsibilities:

- separate text from NVDA speech commands;
- preserve ordering;
- map supported commands to runtime behaviour;
- define explicit handling for unsupported commands;
- build immutable synthesis jobs;
- avoid passing stale jobs after cancellation.

Exact behaviour will be based on the pinned NVDA speech-command definitions.

### 3. Piper runtime service

Responsibilities:

- discover and validate configured models;
- load a selected model;
- synthesize PCM audio;
- provide model metadata;
- isolate runtime failures;
- support deterministic shutdown;
- avoid network access.

Phase 1B provisionally recommends a long-running, non-networked x64 worker process with a Piper backend, generation-tagged IPC, bounded PCM chunks, explicit cancellation, and crash detection. A verified CLI behind the same worker boundary is the fallback. See `docs/piper-runtime-evaluation.md`; this is not yet an accepted implementation decision.

### 4. Audio and lifecycle controller

Responsibilities:

- deliver PCM audio using an NVDA-compatible mechanism;
- support immediate stop and queue replacement;
- avoid playback of stale results;
- control buffering and backpressure;
- report completion reliably;
- release resources during driver termination and NVDA shutdown.

## Concurrency model

The NVDA-facing `speak` path must return promptly. Expensive model loading and inference must run outside NVDA's main thread.

Each synthesis request should carry a generation identifier or cancellation token. When cancellation occurs, pending jobs and late results from earlier generations must be discarded.

The worker owns model loading and inference; the NVDA-side audio controller owns prompt interruption and discards events from stale generations. The exact audio abstraction and index-to-audio mapping still require a proof of concept against the pinned source.

One serialized controller provisionally owns lifecycle transitions. Each worker/audio event must match the current worker session, generation, job, and sequence before it may affect buffering or NVDA notifications. Normal completion is provisionally tied to final PCM playback, not inference completion.

## Distribution boundary

The add-on should initially contain no voice model. Any later downloader must require explicit consent, use HTTPS and verified metadata/checksums, and retain an offline local-file path. Every runtime and voice component needs independently recorded provenance, licence, redistribution rights, and security-update ownership. Store readiness is defined in `docs/addon-store-readiness.md` and does not imply acceptance.

## Voice discovery

Voice discovery should eventually distinguish between:

- model identifier;
- display name;
- language and locale;
- speaker or speaker set;
- sample rate;
- model configuration path;
- model checksum and provenance.

Invalid models must not crash NVDA or make the entire driver unavailable.

## Configuration

Early prototypes should minimize settings. Likely initial settings are:

- voice/model;
- rate strategy;
- output volume where supported;
- optional model directory.

Pitch support must not be promised unless the selected Piper integration can implement it safely and predictably.

## Error handling

Errors should be divided into:

- driver unavailable;
- runtime missing or incompatible;
- model missing or invalid;
- synthesis failure;
- audio failure;
- internal lifecycle failure.

Technical logs must avoid recording synthesized user text by default.

## Security and privacy

The default design is offline and must not initiate network requests. Third-party models and binaries require source, checksum, licence, architecture, and redistribution review.

Secure-screen support is outside the prototype scope and requires a separate threat and deployment review.

## Open architectural questions

- Which Piper runtime interface provides the best balance of latency, maintenance, and packaging?
- Which current NVDA audio abstraction should be used?
- How should NVDA index commands align with generated audio?
- How should rate changes be implemented without unacceptable quality loss?
- Should model loading be eager, lazy, or background-warmed?
- How should multi-speaker models be exposed?
- What minimum Windows and NVDA versions should the first release support?

Phase 1C narrows these questions but does not resolve benchmark-dependent buffer sizes, timeouts, index precision, runtime redistribution, or supported release ranges. See the detailed documents and source register.
