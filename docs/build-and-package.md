# Build and package the unavailable-driver add-on

## Scope and provenance

Phase 2A uses NV Access [AddonTemplate](https://github.com/nvaccess/AddonTemplate) commit `44fb08643974f8d30791cebe36254474251ef162`, inspected 2026-08-01, as the structural and SCons reference. The live NV Access [add-on development links](https://github.com/nvaccess/nvda/blob/master/projectDocs/dev/addons.md), [Store submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md), [API-version data](https://github.com/nvaccess/addon-datastore/blob/master/transform/nvdaAPIVersions.json), and AddonTemplate [localization guide](https://github.com/nvaccess/AddonTemplate/blob/master/docs/l10n/addonAuthors.md) were checked on the same date.

Phases 2F–2G place `protocol.py` and `fakeWorker.py` in the underscore-prefixed private support package. Pinned NVDA `getSynthList` skips module names beginning with `_`, so it is not a separate driver. Phase 2G adds synchronous cancellation-state and metadata-only fake-result rules inside those existing files; the archive allowlist is unchanged. The fake worker has no transport or subprocess, and the main driver neither owns it nor connects `speak()` or `cancel()` to it. The package has no usable synthesizer, runtime, model, synthesis, PCM, audio code, NVDA notification, native dependency, or network behavior. Building or installing it does not validate the Proposed runtime ADR and does not imply Add-on Store acceptance.

Generated Python bytecode and `__pycache__` directories are explicitly excluded from packaging. This keeps the archive allowlist valid even when a local syntax check or isolated import has populated a source-adjacent cache.

The repository adopts the template's `buildVars.py`, manifest templates, SCons entry point, and `site_scons` builders. Deliberate deviations are narrow:

- Existing repository documentation remains at the root instead of being replaced by the template README.
- Packaged help source is `addon/doc/en/readme.md`; SCons converts it to HTML and excludes the Markdown source from the archive.
- Only the template's two pinned build dependencies are declared in `requirements-build.txt`. The full template lint, translation-service, and release dependencies are deferred until their corresponding milestones.
- No localization workflow files or fake catalogues are added. English is the source language; future reviewed translations follow the template's gettext/Crowdin structure.

## Prerequisites

- Windows PowerShell.
- Python 3.10 or newer. Python 3.12.10 was used for the Phase 2A build. This is a build-tool version, not an NVDA runtime compatibility claim.
- Network access only for the initial build-tool installation. The package build itself is offline after dependencies are present.

The dependency pins match the referenced template: SCons 4.10.1 and Markdown 3.10. Create an isolated environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-build.txt
```

The `.venv` directory is ignored and must not be committed.

## Build and clean

Build from the repository root:

```powershell
.\.venv\Scripts\scons.exe
```

The output is `nvdaPiperDriver-0.1.0.nvda-addon`. It is a generated ZIP-compatible archive and is ignored by Git.

Remove all generated package files:

```powershell
.\.venv\Scripts\scons.exe -c
```

The clean target removes the archive, generated `addon/manifest.ini`, generated help HTML, and `.sconsign.dblite`. It preserves `addon/doc/en/readme.md`.

## Manifest decisions

| Field | Phase 2A value | Rationale and limitation |
|---|---|---|
| `name` | `nvdaPiperDriver` | Lower camel case and restricted to Store-valid letters. Uniqueness still requires Store review before submission. |
| `summary` | `NVDA Piper Driver` | Localizable user-visible title. The description states the project intent and that speech is absent. |
| `description` | Explicit metadata-only status | Prevents the development package from advertising working speech. |
| `author` | `Hosein Rezaei` | Project publisher identity supplied for this phase. |
| `url` | HTTPS project repository | Current manifest supports one information URL. |
| `version` | `0.1.0` | Store validation permits numeric `major.minor[.patch]`; requested `0.1.0-dev` would be invalid. |
| `minimumNVDAVersion` | `2026.1.0` | Pinned NVDA `source/addonAPIVersion.py` has `BACK_COMPAT_TO = (2026, 1, 0)` for the Python 3.13/x64 transition, and the live Store list recognizes this API. |
| `lastTestedNVDAVersion` | `2026.1.0` | Conservative non-experimental value required by the manifest. Controlled installation testing has not occurred, so confirmation is a release blocker and this field must not be cited as completed test evidence. |
| `docFileName` | `readme.html` | Matches the generated English help file used by NVDA's add-on manager. |
| `updateChannel` | `dev` | Current AddonTemplate supports development-channel metadata; no Store submission has occurred. |

As of 2026-08-01, the live Store API list marks `2026.2.0` and `2026.3.0` experimental. They were not used. Compatibility declarations must be rechecked and tested before any public package.

## Archive allowlist and inspection

The complete allowlist is:

```text
manifest.ini
doc/en/readme.html
synthDrivers/_nvdaPiperDriver/__init__.py
synthDrivers/_nvdaPiperDriver/conversion.py
synthDrivers/_nvdaPiperDriver/fakeWorker.py
synthDrivers/_nvdaPiperDriver/jobs.py
synthDrivers/_nvdaPiperDriver/protocol.py
synthDrivers/nvdaPiperDriver.py
```

Inspect it without extracting:

```powershell
.\.venv\Scripts\python.exe -c "import zipfile; z=zipfile.ZipFile('nvdaPiperDriver-0.1.0.nvda-addon'); print('\n'.join(z.namelist()))"
```

Run the full source and archive checks after building:

```powershell
$env:NVDA_ADDON_PACKAGE = (Resolve-Path 'nvdaPiperDriver-0.1.0.nvda-addon').Path
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:NVDA_ADDON_PACKAGE
```

The checks require the exact allowlist, required manifest fields, valid internal name/version, generated help, the exact permitted Python sources, safe archive paths, and no forbidden dependency or binary member. The driver has a separate isolated test using a narrow `synthDriverHandler.SynthDriver` stub; protocol and fake-worker tests import the private support package directly.

Repository design documents, imported documentation, pinned NVDA source, tests, Git metadata, caches, local environments, binaries, models, and audio are intentionally excluded. Only the unavailable driver and its private pure Python conversion/protocol support are packaged.

## Safe NVDA installation testing

Do not use a primary NVDA installation for development validation. Use a disposable portable copy whose version matches the manifest declaration, preserve its original configuration, and close other NVDA instances. Then:

1. Start the portable NVDA copy and record its exact version.
2. Install the built archive through NVDA's add-on manager and accept a restart only in that portable copy.
3. Confirm the add-on appears as a development package and its help opens with keyboard navigation.
4. Confirm `NVDA Piper Driver` is absent from the synthesizer selection list because its availability check fails, and confirm the NVDA log has no error attributed to this add-on.
5. Remove the add-on through the same manager, restart, and confirm its directory and listing are gone.
6. Delete the disposable portable environment only after preserving redacted test evidence needed by the project.

No safe portable/development NVDA environment was available during Phases 2A–2C, so installation, help launch, normal/controlled discovery, construction, restart, and uninstall tests are pending. Do not interpret the provisional `lastTestedNVDAVersion` field as evidence that these tests ran.

## Known limitations

- The package proves metadata generation, archive contents, isolated import, identity, and deliberate unavailability only.
- AddonTemplate commit changes, Store validation changes, and new API-version data require revalidation.
- Translation extraction and translated packages were not exercised; no translations are included.
- Byte-for-byte archive reproducibility is not claimed because ZIP metadata may vary. Two clean Phase 2A builds produced identical member names and SHA-256 content hashes.
- No Add-on Store submission or antivirus scan was performed.
