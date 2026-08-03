# Automated portable NVDA validation

Status: Development-only harness; restricted adapter protocol added, full UI scenario verification pending

`tools/portableNvdaValidation/runValidation.ps1` is the single entry point for disposable control/cache preparation. It validates the approved add-on archive, verifies that no `nvda.exe` is running, installs only beneath harness-owned `D:\NVDA\phase2lControl` or `D:\NVDA\phase2lCache`, scopes environment variables to the child, records its PID, and cleans up only a process it launched.

Use:

```powershell
.\tools\portableNvdaValidation\runValidation.ps1 -Mode All
```

Add `-ApproveLaunch` only when the user has closed all NVDA instances and intends to launch the disposable copy. The harness never uses administrator elevation, never touches the primary installed NVDA, never uses coordinates/OCR/mouse automation, and rejects archive traversal or non-approved package members.

Reports are content-free JSON under `validation-results/`; they contain package identity, scenario categories, lifecycle status, errors, and process metadata, not speech fixtures. `analyzeLog.py` scans logs for tracebacks, watchdog/restart failures, and accidental speech-content markers.

The disposable `testAdapter` now provides an authenticated loopback protocol with exact command and fixture allowlists, duplicate-ID rejection, bounded frames, and no code/path/text payloads. It supports status, metrics, cancellation, synth-selection state, and graceful adapter shutdown. UI-specific fixture actions still return `fixture-adapter-not-verified`: the pinned source snapshot lacks the complete gesture/focus/system-test APIs needed to safely implement real edit-box, navigation, and Read All injection. The harness therefore reports those cases explicitly rather than claiming a pass. Physical audible quality remains an optional manual judgment.

The complete NVDA source now confirms that NVDA's own automation uses `tests/system/libraries/NvdaLib.py` together with `tests/system/libraries/SystemTestSpy/speechSpyGlobalPlugin.py`, a speech-spy synth driver, Robot Remote Server, and keyboard gesture helpers. These are reusable as a future adapter backend, but they are not silently copied into the production add-on or widened into arbitrary remote execution.

Activation requires `NVDA_PIPER_VALIDATION_ADAPTER=1`, a fresh run ID, a fresh token, and a harness-owned port-file path. The token is never written to reports or logs. The adapter is copied only into the disposable config and removed during cleanup.
