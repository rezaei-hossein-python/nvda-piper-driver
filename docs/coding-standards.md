# Coding Standards

## Python

- Use clear names and explicit responsibilities.
- Add type annotations to project-owned interfaces where practical.
- Prefer dataclasses or immutable value objects for synthesis jobs.
- Keep functions small enough to test independently.
- Avoid module-level mutable state unless NVDA's driver lifecycle requires it.
- Catch exceptions at clear subsystem boundaries.
- Do not use bare `except`.
- Do not log user text by default.
- Document non-obvious concurrency and lifecycle decisions.

## Architecture boundaries

Keep these concerns separate:

- NVDA API adaptation;
- speech-sequence processing;
- Piper runtime integration;
- model discovery and validation;
- audio playback;
- configuration;
- packaging.

## Concurrency

- Never perform model inference on NVDA's main thread.
- Make cancellation idempotent.
- Ensure shutdown is bounded.
- Reject stale synthesis results after cancellation or driver changes.
- Avoid holding locks while calling external runtimes or audio APIs.
- Document thread ownership for queues, workers, models, and audio objects.

## Tests

Tests should cover:

- speech-sequence conversion;
- cancellation state;
- stale-job rejection;
- model validation;
- configuration parsing;
- lifecycle transitions;
- failures from missing files or dependencies.

Hardware- or NVDA-dependent tests should be clearly marked and accompanied by manual test instructions.

## Documentation

- Explain why significant design choices were made.
- Use exact paths and symbols when citing NVDA source findings.
- Distinguish confirmed behaviour from hypotheses.
- Record important changes in the development journal.
- Update the changelog for user-visible changes.

## Commits

- Keep commits focused.
- Use imperative commit subjects.
- Do not combine formatting-only changes with functional changes.
- Do not commit generated builds, models, caches, secrets, or local environments.
