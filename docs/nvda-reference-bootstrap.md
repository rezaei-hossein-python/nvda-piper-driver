# NVDA reference bootstrap

The authoritative reference is recreated with:

```powershell
.\tools\bootstrapNvdaReference.ps1
```

Verification only:

```powershell
.\tools\bootstrapNvdaReference.ps1 -VerifyOnly
```

The script reads `references/nvda-source-lock.json`, uses only `https://github.com/nvaccess/nvda.git`, checks out the detached commit, initializes submodules, verifies required source directories, and refuses dirty or mismatched existing checkouts. It never changes global Git configuration, uses no administrator privileges, and never deletes a non-empty reference path automatically.

The release tag is `release-2026.1`; the installed portable binary identifies itself as `2026.1.1.55980`. Future updates must intentionally identify the new portable file version, resolve the official release tag, update the lock file, bootstrap a clean checkout, regenerate the source map, and rerun compatibility tests. Tracking `master` is prohibited.
