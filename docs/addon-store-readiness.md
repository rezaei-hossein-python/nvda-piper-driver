# Phase 1B: NVDA Add-on Store readiness

## Authority and date

Checked 2026-08-01. Official requirements below come from the live [addon-datastore submission guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md), [repository README](https://github.com/nvaccess/addon-datastore), [submission review process](https://github.com/nvaccess/addon-datastore/blob/master/docs/dev/submissionReview.md), [NVDA add-on development guide](https://github.com/nvaccess/nvda/blob/master/projectDocs/dev/addons.md), [Developer Guide](https://download.nvaccess.org/documentation/developerGuide.html), [AddonTemplate](https://github.com/nvaccess/AddonTemplate), [API versions](https://github.com/nvaccess/addon-datastore/blob/master/validation/nvdaAPIVersions.json), and [Code of Conduct](https://github.com/nvaccess/nvda/blob/master/CODE_OF_CONDUCT.md). Local counterparts are `references/nvda-source/projectDocs/dev/addons.md`, `docs/imported/nvda-developer-guide.html`, and `references/nvda-source/source/addonStore/`. Requirements can change; recheck them for every submission.

Labels: **Official** means stated by those sources. **Project** means an additional release/security rule proposed here. Neither predicts acceptance.

## Repository and ownership

- **Official:** the issue form requires source/download information; first submission is manually checked for repository ownership/maintainer authority and add-on-ID conflict. Submitters must follow the Code of Conduct. Add-on files are immutable through submitted SHA-256 metadata. Store distribution is non-exclusive.
- **Project:** maintain a public source repository, OSI-compatible project licence with full text, publisher identity, Code of Conduct, security/issue templates, support policy, HTTPS source/help/download URLs, tagged releases, immutable assets, and documented ownership succession. Never replace an asset at an existing version; publish a greater unique version.

## Add-on structure

- Use the current official AddonTemplate rather than copying an old project. It provides SCons packaging, generated manifests, gettext catalogues, Markdown-to-HTML docs, GitHub Actions, Ruff, and Pyright.
- `manifest.ini` is mandatory. Required fields in the current Developer Guide are `name`, `summary`, `version`, `author`, `minimumNVDAVersion`, and `lastTestedNVDAVersion`; Store submissions additionally rely on issue-form/JSON metadata. Use a short unique filesystem-safe ID. Versions must increase and be unique per add-on ID/channel; stable, beta, and dev cannot reuse a version.
- `minimumNVDAVersion` and `lastTestedNVDAVersion` must be valid published API versions. Never raise “last tested” without completing the matrix. Experimental alpha/beta API use requires beta or dev channel.
- Store channels are `stable`, `beta`, and `dev` per official metadata. Development/prerelease behavior must follow the live schema, not invented conventions.
- Put localized help in `doc/<locale>/` and set `docFileName`; locale manifests and gettext resources belong under `locale/<locale>/`. Initialize add-on translations as documented. Provide English help, keyboard instructions, privacy/model provenance, troubleshooting, and release notes/changelog.
- Build a standard UTF-8-filename `.nvda-addon` ZIP using reproducible, pinned tooling. Avoid `installTasks.py` unless indispensable; the Developer Guide warns it should not load add-on C extensions/DLLs and explains pending-install/uninstall timing.

## Submission process

**Official current workflow:** submit the “Add-on registration” GitHub issue form. It generates an issue and PR. A first publisher is approved per add-on (up to two weeks stated); later updates normally skip that approval. Automated checks validate the form, manifest/package, URLs, API versions, hash, and scan state. All URLs must be HTTPS; the download must be a direct reachable URL ending `.nvda-addon`. If checks fail, correct the asset/manifest and resubmit the form. Passing PRs are normally auto-merged.

The Store enforces SHA-256 integrity/immutability and scans with VirusTotal. A malicious detection leaves submission pending. Investigate it; contact the detecting vendor to correct a false positive, explain it on the submission, and use NV Access's stated contact only if assistance is needed. NV Access says Store add-ons do **not** undergo mandatory human security or UX audits. Removal can be requested by metadata PR or email per the datastore README; document deprecation/replacement without hijacking another add-on ID.

**This submission process must be followed manually according to the current official instructions. It must not be invented or automated unless the official process changes.** Project CI may build and test release assets, but it must not fabricate Store metadata, approvals, or acceptance.

## Native binaries and models

For every ONNX Runtime package, Piper executable/library, DLL, phonemizer/eSpeak component, data bundle, model `.onnx`, model JSON, and third-party voice, maintain a machine-readable inventory and human third-party notice containing:

- exact upstream project/repository and component name;
- exact version/commit and x64 architecture;
- HTTPS acquisition source and SHA-256;
- licence text/SPDX identifier, copyright, and redistribution rights;
- required attribution, notices, corresponding/source-code offer obligations;
- reproducible acquisition/build instructions and toolchain;
- dependency relationship and DLL/export inventory;
- vulnerability/security-update owner and replacement cadence.

Do not assume the model licence covers its dataset, base model, speaker consent, or JSON/data files. The old Piper repository's licence discussion documents unresolved community concern around eSpeak NG, while current `piper1-gpl` is explicitly GPL-3.0 and embeds eSpeak NG. Obtain competent licence review before distribution; this document is not legal approval. Large bundled models increase scan/download/update cost, so the recommended default is no bundled voice and a consent-based verified model manager, subject to the Store's current network/UX expectations.

## Security and privacy

### Official validation

HTTPS/direct URL validation, manifest/API/schema checks, SHA-256 immutability, VirusTotal scanning, submitter authorization, and Code-of-Conduct enforcement are documented Store controls. They are not a security audit.

### Additional project release requirements

- No telemetry, synthesized-text logging, crash upload, or silent network access. Clearly disclose all optional network actions.
- Model downloads require an explicit user action, HTTPS, pinned catalogue metadata, expected length and SHA-256 verification before install, atomic rename, and accessible progress/cancel.
- Extract archives into a newly created private temporary directory; reject absolute paths, drive/UNC paths, `..`, links/reparse points, duplicate/conflicting names, excessive entries, and excessive expanded size. Clean safely after handles close.
- Scan dependencies and release artifacts; enable CodeQL (or equivalent), dependency/SBOM generation, and Dependabot (or equivalent). Triage, do not blindly upgrade native runtimes.
- Run least-privileged as the user. Do not require elevation, services, firewall rules, listening sockets, or executable writes outside approved add-on/data directories.
- Canonicalize and validate model paths, regular files, size/schema/opset, config pairing, hashes, and approved roots. Treat all models as untrusted native-parser input and prefer worker isolation.
- Configure safe DLL search directories explicitly; never rely on current working directory or arbitrary `PATH`.
- Bound text/job length, queue depth, model dimensions, PCM buffers, time, memory, and retries. Split long text without breaking NVDA command order.
- On worker crash/hang: stop audio, reject stale messages, give one concise non-text-revealing error, rate-limit restart, and leave NVDA usable. Prevent orphan workers and close them before update/removal.
- Do not claim secure-screen support. Disable or fail clearly until separately designed and tested.
- Redact speech text, filenames/usernames where unnecessary, model URLs with tokens, and IPC payloads from logs. Use event IDs and sizes.

## Accessibility and user experience

Every dialog and workflow must work by keyboard alone with meaningful programmatic labels, logical focus/tab order, default/cancel buttons, and no color/icon/position-only meaning. Announce download/install progress without flooding speech; permit cancellation; return focus predictably. Errors must name the failed item and next action without exposing private text.

First run must explain that no voice is installed, offline speech remains unavailable until a verified voice is selected, download size/source/licence, restart requirement, and local-file alternative. Show offline/network state explicitly. Handle missing runtime/model/device, invalid configuration, corruption, low disk space, permission failure, and unsupported architecture. Updates must preserve voices/settings or present an accessible, reversible migration. Uninstall must explain whether separately stored models remain and offer an explicit, non-default cleanup choice. Help must be reachable from the Store and usable in a browser with headings, lists, descriptive links, and localized text.

## Proposed compatibility and QA matrix

Test the current stable NVDA plus every explicitly supported minimum/current release; add current beta only for beta/dev builds. Test supported Windows 64-bit versions on physical/VM clean machines. Do not infer versions now: set the final matrix immediately before release from NVDA's supported OS/API documentation.

For each supported combination cover installed and portable NVDA where applicable; clean install; local/store-like install; update from previous release; settings/voice migration; downgrade policy; removal with/without models; NVDA/Windows restart; sleep/resume; audio-device removal/default change; rapid character/word/line navigation; repeated cancel during load/inference/playback; say-all; stale indexes; worker crash/hang; corrupt/missing/oversized model; missing DLL; invalid JSON/path; low disk; multiple sequential languages; at least one voice per supported phonemizer path; Persian letters, numbers, punctuation, mixed script, ZWNJ, diacritics, and long text; and a clean machine without developer runtimes.

Record hardware, power mode, model checksum, warm-up, utterance corpus, sample rate, NVDA build, Windows build, and distribution percentiles. Accessibility QA must be performed with NVDA and keyboard only.

## Readiness checklist

### Release-blocking

- [ ] Public source, ownership/publisher, licence, Code of Conduct, support/security contacts.
- [ ] Current AddonTemplate package; valid unique ID/version/channel/API metadata and localized accessible help.
- [ ] Reproducible x64 build and complete dependency/model inventory, hashes, licences, notices, source obligations, and SBOM.
- [ ] No silent network/telemetry/text logging; safe download/extraction/path/DLL behavior.
- [ ] Worker cancellation, crash, hang, shutdown, update, and orphan tests pass.
- [ ] Full supported NVDA/Windows/portable-installed/clean-machine matrix passes, including Persian and another language.
- [ ] Release asset immutable; SHA-256 independently verified; malware findings resolved, not waived locally.
- [ ] Current official submission instructions re-read and manually followed. No acceptance claim.

### Recommended, non-blocking unless risk changes

- Reproducible native builds from source, signed artifacts where feasible, public SBOM/provenance attestations, fuzzing of IPC/config/archive parsers, multiple hardware tiers, community beta, translated help beyond initial languages, and an external security review.

## Questions for NV Access/community confirmation

- Are there current practical size limits or preferences for native-runtime-heavy Store packages?
- Is a consent-based in-add-on voice catalogue/downloader acceptable, and what metadata/privacy disclosure is expected?
- Are externally stored models expected to be removed on uninstall, and what Store UX precedent is preferred?
- What current expectations apply to GPL-3.0 worker binaries inside a GPL-2.0-or-later add-on and corresponding-source delivery?
- Are process-isolated synthesizers expected to work on secure screens, or should the driver explicitly be unavailable there?
- Which Windows/NVDA versions should a new x64-only synthesizer claim at first stable submission?
- How should very large or frequently updated voice assets be represented without treating them as add-on updates?
