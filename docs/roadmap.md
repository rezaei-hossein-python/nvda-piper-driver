# Roadmap

## Current milestone

**Phase 1B — Research Piper runtime, the NVDA neural-speech ecosystem, and Add-on Store readiness. No implementation code exists.**

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
- [ ] Measure and accept or reverse the proposed runtime ADR.
- [ ] Create a minimal add-on package.
- [ ] Make the driver discoverable by NVDA.
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
