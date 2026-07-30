# AGENTS.md

## Project objective

Build a maintained, open-source NVDA synthesizer add-on that runs Piper-compatible neural voices locally.

The initial platform target is current 64-bit NVDA on 64-bit Windows.

## Required behaviour

The driver must:

- operate fully offline;
- load verified Piper-compatible ONNX voice models;
- process NVDA speech sequences safely;
- support prompt cancellation and interruption;
- remain responsive during rapid keyboard navigation;
- expose voice and supported speech settings;
- support index commands or equivalent progress signalling required by NVDA;
- avoid hardcoding Persian or any other single language;
- use Persian as a primary validation language;
- avoid blocking NVDA's main thread;
- release audio and model resources safely;
- fail accessibly when a model, runtime dependency, or audio device is missing.

## Source of truth

Before changing NVDA-facing code, inspect:

1. `docs/imported/nvda-developer-guide.html`
2. `docs/imported/source-notes.md`
3. `references/nvda-source/source/synthDriverHandler.py`
4. `references/nvda-source/source/synthDrivers/`
5. relevant files under `references/nvda-source/source/speech/`
6. current NVDA add-on documentation and developer changes

Do not invent NVDA APIs.

Verify every imported NVDA class, method, property, command type, callback, and extension point against the pinned reference source.

## Scope restrictions

Do not:

- train a TTS model;
- modify NVDA core;
- depend on cloud speech;
- collect text, speech, usage data, or telemetry;
- add network access without an approved design change;
- bundle unverified binaries or voice models;
- copy code with an incompatible licence;
- claim secure-screen support during the prototype phase;
- add broad features before the current milestone is tested.

## Development method

For each phase:

1. inspect relevant reference code;
2. record findings and assumptions;
3. update the design when necessary;
4. implement the smallest testable change;
5. add or update tests;
6. run relevant checks;
7. report changed files;
8. report unresolved risks;
9. stop at the requested milestone.

## Code quality

- Use type annotations for project-owned Python code where practical.
- Prefer small modules with explicit responsibilities.
- Keep NVDA adaptation separate from Piper runtime and audio concerns.
- Do not swallow exceptions silently.
- Log technical detail without exposing private user text.
- Keep user-facing errors concise, actionable, and screen-reader friendly.
- Avoid unnecessary dependencies.
- Pin or document external runtime versions used for development and release.

## Accessibility

All configuration dialogs, documentation, installation steps, status messages, and errors must be usable with NVDA using only the keyboard.

Do not use colour, position, icons, or visual styling as the only means of conveying information.

## Performance

Responsiveness is a correctness requirement.

Designs must account for:

- rapid cancellation;
- repeated short utterances;
- queue replacement during navigation;
- model warm-up;
- audio buffering;
- worker-thread shutdown;
- stale synthesis results arriving after cancellation.

Any performance claim must be supported by a reproducible measurement.

## Repository hygiene

- Do not commit `references/nvda-source/`.
- Do not commit downloaded voice models, generated audio, build output, caches, secrets, or local virtual environments.
- Update `CHANGELOG.md` for user-visible changes.
- Update `docs/development-journal.md` for meaningful research and engineering decisions.
- Use focused commit messages.
