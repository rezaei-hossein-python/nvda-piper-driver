# Phase 2C mock-runtime availability gate

## Purpose and boundary

Phase 2C validates NVDA discovery, construction, and termination without implementing a speech runtime. The “mock runtime” is only an availability condition. It has no API, object, model, voice, text processing, PCM, audio, command, notification, worker, thread, queue, subprocess, file, registry, configuration, or network behavior. It is not Piper and does not predict the future Piper integration boundary.

The driver is unavailable by default. Normal users cannot enable it through add-on settings because the package exposes no settings or dialog. No Piper speech exists even when the test gate is enabled.

## Mechanisms considered

| Mechanism | Decision | Reason |
|---|---|---|
| Private module-level Boolean patched by tests | Rejected | Smallest unit-test mechanism, but it cannot activate discovery in a separately launched portable NVDA process without modifying installed code or adding a broader injection harness. |
| Dependency injection through an availability-probe object | Rejected | Testable, but prematurely introduces a runtime abstraction and packaged support surface before Phase 2D/2H evidence exists. |
| Exact test-only environment marker | Selected provisionally | A process-local value can be supplied to isolated tests and an existing portable NVDA launch. Exact matching is deterministic and requires no file, registry, settings, or runtime probe. |

## Exact activation method

`addon/synthDrivers/nvdaPiperDriver.py` reads this process environment entry without modifying it:

```text
Name:  NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME
Value: phase-2c-explicit-local-mock-runtime-6f4d1c8a
```

Only exact equality enables the test condition. Missing, empty, malformed, differently cased, or conventional truthy values such as `1`, `yes`, and `true` remain false. Results are not cached.

For unit tests, `unittest.mock.patch.dict` supplies and removes the entry around each case. For a controlled portable process, use a dedicated PowerShell session and assign it only for that process tree:

```powershell
$env:NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME = 'phase-2c-explicit-local-mock-runtime-6f4d1c8a'
& 'C:\path-to-disposable-portable-nvda\nvda.exe'
Remove-Item Env:NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME
```

Do not use `setx`, Windows system settings, a persistent shell profile, the registry, or an NVDA configuration file. This activation is unsupported outside isolated development testing. The marker is not secret; its safety comes from an explicit, narrowly named, exact opt-in and default-false behavior.

## Driver behavior

- `check()` returns the Boolean result of the private `_isMockRuntimeAvailable()` probe. It does not construct the driver, cache a result, or log the marker.
- Direct construction repeats the probe and raises `RuntimeError` when unavailable. In controlled mode it calls NVDA's inherited constructor, which registers NVDA's normal configuration-save callback, and records only an internal termination guard.
- `terminate()` is idempotent at this driver boundary. It delegates inherited bookkeeping once and owns no runtime resource to release.
- `speak()` always raises a concise `RuntimeError`. It does not iterate, format, compare, copy, represent, or log its argument and emits no notifications.
- The driver declares no settings, voices, commands, or notifications.

NVDA calls `initSettings()` after construction. Because this fixture advertises no settings, it adds no project setting values; NVDA's inherited bookkeeping may nevertheless create its normal empty driver configuration section in a disposable profile. This is separate from the marker, which is never persisted. Real portable validation must check and document the resulting profile state.

## Security and misuse considerations

- The marker is read-only and process-local when the documented procedure is followed.
- No value, environment dump, user text, or speech sequence is logged.
- Unrelated variables and partial values cannot activate the driver.
- Enabling the marker makes an intentionally non-speaking driver selectable. Selecting it can remove useful speech, so testing must use a disposable portable NVDA instance and retain a known method to restore a working synthesizer.
- This is not an authentication or security boundary. A process launcher that controls NVDA's environment can activate it deliberately.
- The add-on performs no secure-screen test and makes no secure-screen support claim.

## Automated testing

The isolated tests use a minimal `synthDriverHandler.SynthDriver` stub and verify:

1. absent, empty, malformed, conventional truthy, and unrelated markers remain false;
2. the exact marker returns true repeatedly;
3. loader-equivalent inclusion follows `check()`;
4. construction fails while unavailable and succeeds in controlled mode;
5. the constructed fixture owns only stub base bookkeeping and the termination guard;
6. repeated termination delegates base cleanup once;
7. import has no observed file or module-cache side effect;
8. a hostile speech-sequence sentinel is untouched when `speak()` fails;
9. imports and archive members remain allowlisted.

These tests do not prove behavior inside a real NVDA process.

## Portable-NVDA validation procedure

No safe portable/development NVDA environment was available in Phase 2C, so this procedure is deferred:

1. Use a disposable portable copy matching the provisional manifest API; never use the primary NVDA installation or profile.
2. In normal mode, install the package, restart that portable copy, confirm the add-on and help are present, and confirm the driver is absent from synthesizer selection.
3. Exit the portable copy completely and verify no NVDA process remains.
4. Start it from a dedicated PowerShell process with the exact marker above. Confirm the driver appears.
5. Select it only with an independent recovery method available. Do not intentionally invoke speech. Confirm construction causes no driver-specific log error.
6. Switch to a working synthesizer, exit portable NVDA, remove the process marker, and restart normally. Confirm the driver is absent again.
7. Inspect the disposable profile and log for unexpected driver state, private text, files, or errors; then uninstall and confirm removal.

## Removal and replacement

Phase 2D may continue using this gate solely to reach mock lifecycle/settings tests; it must not broaden marker semantics. Later mock phases may replace direct environment reads with an internal dependency boundary only when implementation needs justify it. Phase 2H must not treat this marker as evidence that Piper is available. Before any public testing or release, remove the environment gate or replace it with a separately reviewed, verified local-runtime availability design. The runtime ADR remains Proposed.
