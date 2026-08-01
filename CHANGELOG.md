# Changelog

All notable user-visible changes will be documented in this file.

The project has not released a public version.

## Unreleased

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

The driver remains unavailable in normal use and `speak()` produces no speech when the development gate is enabled. Converted jobs are returned only through a private internal boundary and are neither retained nor executed. No worker, protocol, Piper runtime, audio implementation, runtime binary, or voice model has been added. The package is not a public release and has not been submitted to the Add-on Store.
