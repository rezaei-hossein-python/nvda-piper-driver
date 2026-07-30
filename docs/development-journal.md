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
