# Architecture

## Status

This document describes the provisional architecture. It must be revised after completing the NVDA SynthDriver research phase.

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

The implementation choice—embedded Python runtime, native executable, library binding, or managed worker process—remains open pending evaluation.

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

The final model will be selected after studying current built-in drivers, NVDA audio APIs, and extension points.

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
