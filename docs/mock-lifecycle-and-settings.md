# Mock lifecycle and settings

## Purpose and scope

Phase 2D validates NVDA construction, settings initialization, and teardown while the exact Phase 2C development marker is active. It does not implement speech jobs, Piper, ONNX Runtime, models, workers, audio, commands, notifications, cancellation, pause, or network access. The driver remains unavailable by default and is not usable as a synthesizer.

The implementation is deliberately smaller than the production state machine in `driver-state-machine.md`. It has no concurrency and therefore needs no locks.

## Minimal lifecycle

The private `_MockLifecycleState` enum contains exactly these states:

| State | Entry | Permitted behavior | Exit |
|---|---|---|---|
| `initializing` | Controlled construction has passed the availability check | Base settings initialization only | Successful initialization enters `ready`; an exception escapes construction |
| `ready` | Base initialization completed | Read or change the mock voice/rate; terminate; reject speech | `terminate()` enters `terminated` |
| `terminated` | First termination begins | Repeated termination is a no-op; active setting operations and speech fail | None |

Termination is irreversible and idempotent. Inherited cleanup runs while the setting getters remain valid because pinned NVDA saves advertised settings during `Driver.terminate()`; a `finally` transition then makes the object terminated even if cleanup raises. A later call is a no-op, so inherited cleanup runs no more than once. The object owns no external resources. An initialization exception is not suppressed.

## Settings designs considered

| Design | Decision | Reason |
|---|---|---|
| No advertised settings | Rejected | Valid, but does not exercise NVDA's setting initialization boundary. |
| One fixed mock voice | Rejected | Exercises voice initialization but not bounded numeric setting validation. |
| Fixed mock voice plus in-memory rate | Selected | Exercises both current NVDA voice and numeric setting paths with a small, truthful mock surface. |
| Fixed mock voice plus rate and volume | Rejected | A second inert numeric control adds little evidence and creates another meaningless user control. |

The selection follows the pinned NVDA `SynthDriver.initSettings`, `changeVoice`, and `NumericSynthSetting` behavior in `references/nvda-source/source/synthDriverHandler.py`, plus `AutoSettings.initSettings` in `references/nvda-source/source/autoSettingsUtils/autoSettings.py`. `VoiceSetting()` and `RateSetting()` are advertised because their getters and setters exist. No command or notification support is advertised.

## Mock voice

The driver exposes exactly one in-memory `VoiceInfo`:

- ID: `mockVoice`
- Display name: `Mock Voice — No Speech`
- Language: `None`

The display name makes the fixture's limitation explicit. Selecting the sole known ID is an in-memory assignment. An unknown ID raises `LookupError`. There is no directory scan, locale claim, model load, or language support.

## Mock rate

Rate defaults to `50`, matching NVDA's default percentage-style numeric setting value. The accepted domain is an integer from `0` through `100`, inclusive.

- `type(value) is not int`, including `bool`: `TypeError`.
- Integer outside `0..100`: `ValueError`.
- Valid integer while ready: stored only on the object and returned unchanged.
- Access or mutation after termination: `RuntimeError`.

Rate does not affect speech because speech does not exist. Volume, pitch, variants, language selection, rate boost, and other settings are not advertised.

## Construction and persistence behavior

Construction repeats the exact Phase 2C availability probe, initializes the private state and setting defaults, invokes the inherited initializer, and then enters `ready`. This ordering keeps getters valid if NVDA's base initialization reads them.

Project code creates no configuration file and does not access AppData or the registry. Current inherited NVDA behavior registers a configuration-save callback, creates/reads the synthesizer section, loads advertised settings, and may load a voice dictionary. It saves settings and unregisters the callback during base termination. Unit tests replace that behavior with a narrow in-memory stub and cannot modify user configuration.

This inherited behavior is a risk for future portable-NVDA testing: use a disposable portable profile, inspect resulting configuration, and remove the add-on/profile afterward. The process environment marker is read only and is never persisted or modified.

## Speech behavior and privacy

`speak()` remains deliberately nonfunctional. While ready it raises `RuntimeError` stating that Phase 2D has no speech implementation. After termination it raises a lifecycle `RuntimeError`. Neither path reads, iterates, formats, compares, copies, serializes, or logs the speech-sequence argument. No index or completion notification is emitted.

## Verification procedure

Automated tests use narrow substitutes for NVDA's base class and setting descriptors. They cover exact availability, construction rejection, the three-state set, ready transition, irreversible/idempotent termination, inherited cleanup count, fixed voice metadata, unknown voice rejection, rate boundaries and invalid types, post-termination behavior, hostile speech sentinels, dependencies, package contents, and reproducible archive members.

Real NVDA validation remains pending unless a safe development or portable copy is already available. The future controlled procedure is:

1. Start a disposable portable NVDA without the marker and confirm the driver is absent.
2. Start that copy with the exact test-only marker and confirm the driver appears.
3. Select it only in that disposable session and confirm construction succeeds.
4. Inspect the settings ring for only Mock Voice and Rate.
5. Do not intentionally request speech; selection itself may cause NVDA to call `speak()`, so treat that as a likely limitation and do not claim selection success until tested safely.
6. Immediately return to a working synthesizer and exit portable NVDA.
7. Confirm that no marker, orphan resource, or unexpected profile state remains.

Do not use a primary NVDA installation.

## Evolution and known limitations

This fixture is not a Piper runtime. Phase 2E may add pure speech-job conversion, but must not reinterpret these inert settings as effective synthesis controls. Later phases must replace or evolve the mock lifecycle only when real resource ownership requires it, reconcile behavior with `driver-state-machine.md`, and remove the test availability marker before public testing. The runtime ADR remains Proposed.
