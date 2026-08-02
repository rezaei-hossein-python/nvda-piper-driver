# NVDA Piper Driver

An open-source NVDA synthesizer add-on for running Piper-compatible neural voices locally on Windows.

## Project status

**Phase 2J remains under portable validation.** A bounded non-daemon controller owns one persistent child, loads the configured model once per session, preserves index-delimited segments, queues real `synthIndexReached` callbacks after segment playback, and isolates character-mode text. It keeps one active request plus one replaceable pending request, rejects stale PCM/index/completion events, and terminates the child for bounded hard cancellation. Language metadata is tolerated without model switching; unsupported prosody, break, and phoneme commands remain rejected. Piper, ONNX Runtime, models, WAV files, and the development environment remain outside the add-on. Warm retained-model integration passes; portable typed-echo, Read All, latency, and watchdog evidence remains pending.

Phases 1A–1C documented NVDA's interface, evaluated runtime and release constraints, and defined a mock-first implementation sequence. Phases 2A–2G established packaging, controlled discovery, immutable jobs, bounded protocol validation, and synchronous cancellation-state tests. Phase 2H verified one compatible voice outside NVDA without prioritizing a language. Phase 2I produced the first controlled portable-NVDA speech; Phase 2J replaces its blocking path while keeping behavior model-driven and language-neutral.

## Why this project exists

Blind and low-vision users benefit from speech that is responsive, intelligible, multilingual, and available offline. Traditional screen-reader synthesizers are often highly responsive but may sound robotic. Neural text-to-speech can sound more natural, but many neural systems depend on cloud services or are not designed for the interruption and latency requirements of a screen reader.

This project aims to bridge that gap by integrating Piper-compatible local neural voices with NVDA through a maintained synthesizer driver.

## Goals

- Run speech fully offline.
- Support Piper-compatible ONNX voice models.
- Integrate with current 64-bit NVDA releases.
- Keep NVDA responsive during rapid navigation.
- Support immediate cancellation and interruption.
- Expose available voices and relevant speech settings.
- Support multiple languages rather than hardcoding one language.
- Use Persian as a primary multilingual validation case.
- Provide accessible installation, configuration, errors, and documentation.
- Maintain a clear, testable, source-backed engineering process.

## Non-goals

- Training new neural TTS models.
- Replacing NVDA's speech subsystem.
- Modifying NVDA core.
- Using cloud speech services.
- Collecting telemetry, spoken text, or user activity.
- Claiming secure-screen support before it has been designed and tested.
- Bundling third-party binaries without verifying their origin, licence, architecture, and redistribution terms.

## Planned architecture

The intended design has four main layers:

1. **NVDA SynthDriver adapter** — receives NVDA speech sequences, exposes settings, handles cancellation, and reports speech progress.
2. **Speech-sequence processor** — converts supported NVDA speech commands and text into synthesis work.
3. **Piper runtime service** — loads compatible models and produces PCM audio without blocking NVDA's main thread.
4. **Audio and lifecycle controller** — streams audio, interrupts promptly, releases resources safely, and reports failures accessibly.

This architecture remains provisional until mock-worker and local Piper/audio measurements satisfy the Proposed runtime ADR.

## Repository structure

```text
addon/                  NVDA add-on source
docs/                   Architecture, plans, research, and journal
docs/imported/          Locally imported official references
references/             External source checkouts excluded from Git
tests/                  Automated tests and test support
AGENTS.md               Rules for AI coding agents
CHANGELOG.md            User-visible project changes
CONTRIBUTING.md         Contribution workflow
```

## Development principles

- Verify NVDA-facing APIs against the pinned NVDA source checkout.
- Work in small milestones.
- Document architectural decisions before large implementation changes.
- Add tests with implementation changes.
- Keep commits focused and descriptive.
- Treat responsiveness and interruption as core requirements, not optional refinements.
- Fail safely when models, dependencies, or audio devices are unavailable.

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md).

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/implementation-plan.md`](docs/implementation-plan.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/coding-standards.md`](docs/coding-standards.md)
- [`docs/development-journal.md`](docs/development-journal.md)
- [`docs/driver-state-machine.md`](docs/driver-state-machine.md)
- [`docs/speech-job-model.md`](docs/speech-job-model.md)
- [`docs/worker-protocol.md`](docs/worker-protocol.md)
- [`docs/audio-pipeline.md`](docs/audio-pipeline.md)
- [`docs/model-and-voice-management.md`](docs/model-and-voice-management.md)
- [`docs/configuration-schema.md`](docs/configuration-schema.md)
- [`docs/error-handling-and-recovery.md`](docs/error-handling-and-recovery.md)
- [`docs/security-threat-model.md`](docs/security-threat-model.md)
- [`docs/testing-strategy.md`](docs/testing-strategy.md)
- [`docs/continuous-integration-plan.md`](docs/continuous-integration-plan.md)
- [`docs/accessibility-acceptance-criteria.md`](docs/accessibility-acceptance-criteria.md)
- [`docs/project-governance-and-support.md`](docs/project-governance-and-support.md)
- [`docs/documentation-plan.md`](docs/documentation-plan.md)
- [`docs/phase-2-implementation-sequence.md`](docs/phase-2-implementation-sequence.md)
- [`docs/build-and-package.md`](docs/build-and-package.md)
- [`docs/mock-runtime-availability.md`](docs/mock-runtime-availability.md)
- [`docs/mock-lifecycle-and-settings.md`](docs/mock-lifecycle-and-settings.md)
- [`docs/speech-job-conversion.md`](docs/speech-job-conversion.md)
- [`docs/fake-worker-protocol.md`](docs/fake-worker-protocol.md)
- [`docs/mock-cancellation-and-generations.md`](docs/mock-cancellation-and-generations.md)
- [`docs/standalone-piper-runtime-results.md`](docs/standalone-piper-runtime-results.md)
- [`docs/first-nvda-piper-speech.md`](docs/first-nvda-piper-speech.md)
- [`docs/portable-nvda-validation.md`](docs/portable-nvda-validation.md)
- [`docs/espeak-interaction-baseline.md`](docs/espeak-interaction-baseline.md)
- [`docs/character-echo-and-read-all.md`](docs/character-echo-and-read-all.md)
- [`docs/piper-interactive-performance.md`](docs/piper-interactive-performance.md)
- [`docs/research-source-register.md`](docs/research-source-register.md)
- [`docs/repository-quality-review.md`](docs/repository-quality-review.md)
- [`docs/imported/source-notes.md`](docs/imported/source-notes.md)

## Contributing

This project is in an early development-validation phase with a bounded background portable-NVDA prototype awaiting manual Phase 2J verification. Contributions should be narrowly scoped, documented, and based on current NVDA interfaces. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

This project is intended to be distributed under **GNU General Public License v2.0 or later (GPL-2.0-or-later)**. The complete licence text is stored in `LICENSE`.
