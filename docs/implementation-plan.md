# Implementation Plan

## Working method

Each milestone must produce a small, demonstrable result. Later phases should not begin until the current phase has documented evidence and basic tests.

## Phase 0 — Repository foundation

Deliverables:

- repository structure;
- README and contribution guidance;
- architecture, roadmap, and journal;
- pinned NVDA source reference;
- official developer guide imported locally;
- first GitHub commit.

Exit criteria:

- Git ignores the NVDA reference checkout;
- foundational files are committed and pushed;
- repository can be cloned cleanly on another computer.

## Phase 1 — NVDA SynthDriver research

Inspect current NVDA source to determine:

- required and optional `SynthDriver` members;
- speech-sequence and command types;
- cancellation and pause semantics;
- index and completion notifications;
- voice and setting exposure;
- audio-output APIs;
- threading and shutdown expectations;
- add-on packaging requirements;
- API changes relevant to current 64-bit NVDA.

Deliverables:

- `docs/nvda-synthdriver-research.md`;
- source citations by file and symbol;
- initial interface checklist;
- identified uncertainties and test strategy.

No production driver code should be written in this phase.

## Phase 2 — Minimal add-on and driver skeleton

Deliverables:

- valid add-on structure and manifest;
- minimal driver module;
- driver discovery in a controlled NVDA development environment;
- safe availability check;
- logging and termination skeleton.

Exit criteria:

- NVDA starts normally with the add-on installed;
- the driver is discoverable or reports unavailability predictably;
- selecting and leaving the driver does not crash or hang NVDA.

## Phase 3 — Runtime proof of concept

Evaluate and select a Piper integration mechanism.

Deliverables:

- architecture decision record;
- one verified test voice;
- standalone synthesis outside NVDA;
- model provenance, licence, checksum, and performance notes;
- deterministic runtime startup and shutdown.

## Phase 4 — First speech inside NVDA

Deliverables:

- synthesis of plain text;
- audio playback through the selected NVDA-compatible path;
- basic completion handling;
- failure recovery.

Exit criteria:

- a short sentence is spoken from NVDA;
- NVDA remains operable after synthesis;
- repeated utterances do not leak workers or audio handles.

## Phase 5 — Cancellation and navigation responsiveness

Deliverables:

- immediate cancellation;
- stale-result rejection;
- queue replacement;
- rapid-navigation benchmark;
- lifecycle stress tests.

This phase blocks broader feature work.

## Phase 6 — Speech commands and indexes

Deliverables:

- explicit supported-command matrix;
- index-command handling;
- sentence and character navigation validation;
- documented fallback behaviour for unsupported commands.

## Phase 7 — Voices and settings

Deliverables:

- model discovery;
- voice selection;
- persisted configuration;
- rate and volume behaviour where supported;
- accessible errors for invalid models.

## Phase 8 — Packaging and accessible configuration

Deliverables:

- reproducible add-on build;
- keyboard-accessible configuration;
- dependency and model installation strategy;
- upgrade and removal behaviour;
- clean-machine acceptance test.

## Phase 9 — Quality and compatibility

Deliverables:

- automated tests;
- latency and cancellation measurements;
- multilingual validation including Persian;
- supported NVDA and Windows matrix;
- documented known limitations.

## Phase 10 — Release preparation

Deliverables:

- release notes;
- licence and third-party notices;
- checksums;
- installation and troubleshooting documentation;
- signed or otherwise verifiable release assets where feasible;
- community testing plan.
