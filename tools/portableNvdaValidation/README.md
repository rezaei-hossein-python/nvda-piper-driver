# Automated portable NVDA validation

This is development-only tooling. It is never included in the add-on archive and never modifies the installed NVDA.

Run a safe preflight/install/report pass (no NVDA launch):

```powershell
.\tools\portableNvdaValidation\runValidation.ps1 -Mode All
```

To approve launching only the disposable `D:\NVDA` copy:

```powershell
.\tools\portableNvdaValidation\runValidation.ps1 -Mode All -ApproveLaunch
```

The harness refuses to continue if any `nvda.exe` is already running, validates the package allowlist and manifest, installs only into harness-owned `D:\NVDA\phase2lControl` or `D:\NVDA\phase2lCache`, scopes environment variables to the child, records the launched PID, and cleans up only that PID. It never terminates unrelated NVDA processes and never uses administrator elevation.

Reports are content-free JSON under `validation-results/`. The current repository does not contain an approved disposable NVDA test global plugin or NVDA Spy automation adapter, so objective speech scenarios are explicitly reported as blocked rather than falsely marked passed. A future adapter must expose only predefined scenarios, use a per-run local authentication token, and be removed after the run. No mouse coordinates, OCR, screen scraping, or arbitrary remote Python execution is used.
