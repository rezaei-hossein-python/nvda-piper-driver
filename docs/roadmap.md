# Roadmap

## Current milestone

**Phase 1 — Research the current NVDA SynthDriver contract.**

## Milestones

- [x] Create local project structure.
- [x] Initialize Git.
- [x] Import the official NVDA developer guide.
- [x] Clone and pin the current NVDA source for local reference.
- [x] Exclude the NVDA checkout from the project repository.
- [ ] Publish the foundational repository to GitHub.
- [ ] Document the current `SynthDriver` interface.
- [ ] Document NVDA speech commands, indexes, cancellation, and audio flow.
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
- [ ] Complete community testing and first stable release.

## Release philosophy

The first public release should prioritize:

1. reliable interruption;
2. predictable installation;
3. stable offline speech;
4. accessible configuration;
5. transparent limitations.

Naturalness alone is not sufficient for a screen-reader synthesizer.
