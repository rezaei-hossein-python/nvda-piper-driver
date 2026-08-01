# Continuous-integration plan

## Evidence and classification

Checked 2026-08-01. The official [NV Access AddonTemplate](https://github.com/nvaccess/AddonTemplate) currently provides SCons packaging, GitHub Actions, Ruff, Pyright, gettext/doc generation, and `prek`; NVDA itself uses unit/system tests, Markdown lint, pre-commit, dependency automation, and CodeQL ([NVDA repository](https://github.com/nvaccess/nvda)). These are implementation evidence or template facilities, not Add-on Store mandates. Store validation remains described in `docs/addon-store-readiness.md`.

## Proposed checks

| Check | Purpose/tool | Merge / release | Runtime | Limits and accessibility |
|---|---|---|---|---|
| Format/lint | AddonTemplate Ruff configuration | mandatory / mandatory once Python exists | fast | Does not prove behavior; readable diagnostics. |
| Type check | Pyright per template | mandatory for project modules / mandatory | fast-medium | NVDA stubs/private APIs may need narrow documented exceptions. |
| Unit tests | pytest or repository-selected current Python runner | mandatory / mandatory | fast-medium | Fake boundaries; no audio quality proof. |
| Markdown lint | markdownlint-cli2, aligned with NVDA | warning then mandatory / mandatory | fast | Avoid rules that reduce screen-reader readability. |
| Link check | local links every PR; external scheduled/manual | mandatory local / mandatory reviewed external | fast/variable | External failures can be transient; output must name document/link. |
| Manifest validation | AddonTemplate build plus current Store schema/API checks | skeleton onward mandatory / mandatory | fast | Passing does not imply Store acceptance. |
| Add-on build | official template SCons | skeleton onward / mandatory | medium | Build only; no automatic release initially. |
| Archive inspection | project allowlist, path/duplicate/size/forbidden extension inventory | mandatory when package exists / mandatory | fast | Ensures docs/help/licences and no accidental models/secrets. |
| Dependency scan | Dependabot alerts plus `pip-audit` or equivalent after dependency selection | advisory triaged / mandatory disposition | medium | Vulnerability databases have false positives/gaps. |
| Secret scan | GitHub secret scanning/push protection | mandatory policy / mandatory | hosted | No secrets expected; avoid exposing findings in public logs. |
| CodeQL | GitHub CodeQL for Python/C++ when code exists | advisory then mandatory for relevant changes / mandatory | medium-slow | Not a security audit; tune generated/vendor exclusions. |
| Licence/SBOM | pinned inventory plus ScanCode/REUSE-compatible check after evaluation | dependency changes / mandatory | medium-slow | Automated licence classification needs human review. |
| Binary checksums | compare staged runtime inventory/SHA-256 | runtime stage / mandatory | fast | Hash proves identity, not safety. |
| Reproducibility | two clean Windows builds compare normalized package/content hashes | pre-release / mandatory stable | slow | Timestamps/toolchain may need normalization and explanation. |
| Release verification | rebuild, archive inspect, hash, malware submission workflow evidence | no / mandatory | slow/manual | Do not automate Store submission or overwrite assets. |

Windows runners are required for packaging, native/runtime, path/DLL, process, and NVDA tests. Linux may run platform-neutral lint/docs/unit tests only if parity is demonstrated. Pin actions to trusted immutable revisions where practical; grant least permissions. Caches never contain models, binaries from unverified sources, secrets, user data, or release outputs; cache keys include lockfile/toolchain and restored caches are not trusted as release evidence.

## Staged adoption

1. **Documentation/repository:** `git diff --check`, local links/headings/encoding, Markdown lint, secret scanning. Keep it small.
2. **Skeleton:** Ruff, Pyright, pure tests, manifest validation, template build, archive inspection.
3. **Runtime:** Windows fake-worker/process/audio tests, protocol fuzz/property tests, dependency/SBOM/licence/checksum and CodeQL.
4. **Pre-release:** clean x64 package, standalone verified runtime tests, matrix subsets, reproducibility, artifact/hash/malware review, localized docs build.
5. **Stable:** full release matrix evidence, two-party release review, immutable asset verification, manual current Store process.

No permanent workflow is created in Phase 1C. Expected runtime is reassessed once real suites exist; slow/soak/manual jobs are scheduled or release-gated rather than blocking every documentation change.
