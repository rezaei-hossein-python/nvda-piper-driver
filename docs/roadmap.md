# Roadmap

## Current milestone

**Phases 2G–2I are complete. Phase 2I produced the first controlled audible Piper utterance in portable NVDA and switched back to eSpeak. It does not provide responsive production speech, and no public release exists.**

## Milestones

- [x] Create local project structure.
- [x] Initialize Git.
- [x] Import the official NVDA developer guide.
- [x] Clone and pin the current NVDA source for local reference.
- [x] Exclude the NVDA checkout from the project repository.
- [ ] Publish the foundational repository to GitHub.
- [x] Document the current `SynthDriver` interface.
- [x] Document NVDA speech commands, indexes, cancellation, and audio flow.
- [x] Evaluate Piper runtime and process-isolation options provisionally.
- [x] Review neural-speech ecosystem evidence and current Store requirements.
- [x] Define detailed lifecycle, worker, audio, model, security, quality, accessibility, and governance designs.
- [x] Define the Phase 2A–2J mock-first implementation sequence.
- [ ] Measure and accept or reverse the proposed runtime ADR.
- [x] Phase 2A: create and validate an AddonTemplate-aligned metadata/help package; no driver.
- [x] Phase 2B: add and isolate-test a minimal safely unavailable driver.
- [x] Phase 2C: prove controlled discovery and base-only lifecycle with an exact test marker.
- [x] Phase 2D: prove minimal lifecycle and settings initialization with mocks.
- [x] Phase 2E: prove immutable, ordered, privacy-preserving speech-job conversion.
- [x] Phase 2F: prove bounded protocol, fake handshake, sequencing, correlation, errors, and shutdown in process.
- [x] Phase 2G: prove bounded synchronous cancellation and stale fake-result rejection with mocks.
- [x] Phase 2H: complete verified, language-neutral standalone Piper synthesis and measurements outside NVDA.
- [x] Phase 2I: verify one controlled audible utterance and clean switching/shutdown in portable NVDA.
- [ ] Phase 2J: separately address responsive execution, production cancellation, indexes, and completion semantics.
- [x] Make the unavailable driver module discoverable by NVDA's loader while excluding it from selection.
- [ ] Select and validate a Piper runtime integration.
- [ ] Speak the first plain-text utterance.
- [ ] Implement prompt cancellation and stale-result rejection.
- [ ] Add voice discovery and configuration.
- [ ] Add accessible installation and error handling.
- [ ] Add repeatable latency and reliability tests.
- [ ] Validate multilingual operation, including Persian.
- [ ] Produce a packaged pre-release.
- [ ] Complete dependency/model provenance, licensing, SBOM, and security review.
- [ ] Pass the documented release-readiness matrix on clean machines.
- [ ] Complete an accessible community beta and resolve release blockers.
- [ ] Manually submit under the then-current official Add-on Store process.
- [ ] Complete community testing and first stable release.

## Release philosophy

The first public release should prioritize:

1. reliable interruption;
2. predictable installation;
3. stable offline speech;
4. accessible configuration;
5. transparent limitations.

Naturalness alone is not sufficient for a screen-reader synthesizer.

Add-on Store acceptance is not guaranteed; compatibility claims and submission metadata must be revalidated at each release.
