# Research source register

## Scope

External sources used in Phases 1B/1C, checked 2026-08-01 unless a row says otherwise. Local pinned evidence is registered separately at the end. “Authoritative” means official requirements/documentation; “implementation” means primary project code/releases; “community” is contextual evidence. Current status must be rechecked before implementation/release.

| Title / organization | URL | Type/status/evidence | Used by | Limits |
|---|---|---|---|---|
| NVDA repository, NV Access | https://github.com/nvaccess/nvda | repository; current; authoritative + implementation | Phase 1A, architecture, audio, testing, CI | Master changes; project pins a separate commit. |
| NVDA Developer Guide, NV Access | https://download.nvaccess.org/documentation/developerGuide.html | official docs; current; authoritative | Phase 1A, Store, localization, threading | Add-on API changes; recheck per NVDA release. |
| NVDA add-on development links | https://github.com/nvaccess/nvda/blob/master/projectDocs/dev/addons.md | official docs; current; authoritative | Store, docs, CI | Links to other evolving guides. |
| AddonTemplate, NV Access | https://github.com/nvaccess/AddonTemplate | template/repository; current; official facility | Store, CI, Phase 2A, ecosystem | Facility is not itself a Store acceptance guarantee. |
| AddonTemplate commit 44fb08643974f8d30791cebe36254474251ef162, NV Access | https://github.com/nvaccess/AddonTemplate/commit/44fb08643974f8d30791cebe36254474251ef162 | exact template revision; current at 2026-08-01; official implementation reference | Phase 2A build/package | Selected files were adapted; the repository was not replaced wholesale. |
| AddonTemplate localization for authors | https://github.com/nvaccess/AddonTemplate/blob/master/docs/l10n/addonAuthors.md | official template docs; current; authoritative for template workflow | docs/localization/CI | Must match adopted template revision. |
| Add-on Store datastore README | https://github.com/nvaccess/addon-datastore | official repository; current; authoritative | Store/security/governance | Says Store does not perform human security audit. |
| Submission Guide | https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md | official workflow; current; authoritative | Store/CI/governance | Manual workflow can change. |
| Submission review process | https://github.com/nvaccess/addon-datastore/blob/master/docs/dev/submissionReview.md | official maintainer docs; current; authoritative | Store/governance | Operational internals may change. |
| Metadata schema documentation | https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/jsonMetadata.md | official docs; current; authoritative | Store/CI | Recheck schema at submission. |
| NVDA API versions | https://github.com/nvaccess/addon-datastore/blob/master/validation/nvdaAPIVersions.json | official validation data; current; authoritative | Store/release matrix | Time-sensitive, experimental flags change. |
| NVDA Code of Conduct | https://github.com/nvaccess/nvda/blob/master/CODE_OF_CONDUCT.md | official policy; current; authoritative | governance/Store | Does not replace project support policy. |
| NVDA contributing guide | https://github.com/nvaccess/nvda/blob/master/projectDocs/dev/contributing.md | official docs; current; community-project authority | testing/CI/governance | NVDA-core requirements are not automatically add-on requirements. |
| Current Piper successor, Open Home Foundation | https://github.com/OHF-Voice/piper1-gpl | repository/docs; current; primary implementation | runtime/model/security | GPL-3.0; seeking maintainers at access; no project legal conclusion. |
| Piper 1.5.0 Python package, PyPI | https://pypi.org/project/piper-tts/ | official package metadata and Windows x64 artifact hashes; current at 2026-08-01 | Phase 2H runtime selection/provenance | PyPI metadata does not resolve transitive licences or future compatibility. |
| Piper Python API, Open Home Foundation | https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md | official implementation documentation; current at 2026-08-01 | Phase 2H adapter/streaming/cancellation investigation | Chunk iteration is not proof that active inference is cancellable. |
| Piper voices, rhasspy | https://huggingface.co/rhasspy/piper-voices | official voice repository; primary model/config files | Phase 2H local test voice | Repository licence metadata does not supersede each dataset/model card or speaker-rights review. |
| Lessac low model card | https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/lessac/low/MODEL_CARD | primary per-voice metadata | Phase 2H provenance/sample rate/speaker count | Links to a separate dataset licence; no project redistribution conclusion. |
| Current Visual C++ Redistributable, Microsoft | https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist | official deployment documentation/download; installer signature verified and version 14.51.36247.0 installed | Phase 2H native prerequisite | Installer version changes; redistribution is subject to Microsoft terms. |
| Redistribute Visual C++ files, Microsoft | https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files | official deployment/licensing guidance | Phase 2H component inventory | Project has not established redistribution eligibility or a servicing design. |
| Piper Plus, ayutaz | https://github.com/ayutaz/piper-plus | maintained alternative implementation | Phase 2H option reconsideration | Documented custom language coverage is narrower than the general compatible-voice target; claims require independent verification. |
| Archived Piper, rhasspy | https://github.com/rhasspy/piper | archived repository; historical; implementation | Phase 1B/history/licensing | Archived 2025-10-06; not current workflow. |
| ONNX Runtime documentation, Microsoft | https://onnxruntime.ai/docs/ | official runtime docs; current; authoritative implementation | runtime/worker/testing | General ORT docs do not prove Piper model compatibility. |
| ONNX Runtime installation, Microsoft | https://onnxruntime.ai/docs/install/ | official deployment docs; current; authoritative implementation | Phase 1B runtime packaging | Available packages still require exact-version and architecture verification. |
| ONNX Runtime threading | https://onnxruntime.ai/docs/performance/tune-performance/threading.html | official docs; current | worker/performance | Tuning is hardware/model-specific. |
| ONNX Runtime repository/licence, Microsoft | https://github.com/microsoft/onnxruntime | repository; current; primary | runtime/licensing/security | Transitive packaged components still need audit. |
| ONNX Runtime licence file, Microsoft | https://github.com/microsoft/onnxruntime/blob/main/LICENSE | upstream licence text; current; primary | Phase 1B licensing | One file does not resolve all bundled/transitive component obligations. |
| Python subprocess documentation, PSF | https://docs.python.org/3/library/subprocess.html | official language docs; current | worker/security | Target worker Python/version may differ. |
| Python JSON documentation, PSF | https://docs.python.org/3/library/json.html | official language docs; current | protocol/security | JSON resource warning does not choose numeric limits. |
| Sonata NVDA, Musharraf Omer | https://github.com/mush42/sonata-nvda | repository; current evidence at access; implementation | ecosystem/runtime/repository review | Activity/release does not guarantee support status. |
| Sonata releases | https://github.com/mush42/sonata-nvda/releases | releases; current evidence | ecosystem/runtime/testing | Claims are project reports, not independent benchmarks. |
| TeleNVDA, NVDA add-ons community | https://github.com/nvdaaddons/TeleNVDA | repository; current at access; community implementation | repository/governance/CI | Remote add-on differs substantially from a synth. |
| Hear2Read | https://hear2read.org/ | project site; current evidence | ecosystem/model UX | Public source/provenance evidence remained incomplete. |
| NVDA Add-ons Directory | https://nvda-addons.org/ | community directory; current | ecosystem/compatibility | Community listing, not Store authority/security audit. |
| GitHub repository security practices | https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories | platform docs; current; primary guidance | CI/governance | Recommendations, not NVDA Store mandates. |

## Local pinned evidence

`docs/imported/source-notes.md` records NVDA commit `e98b2a14cbc166294b0bbbb15fe4295cd2e4dd61` retrieved 2026-07-30. Key paths used across Phase 1C are `source/synthDriverHandler.py`, `driverHandler.py`, `speech/commands.py`, `speech/manager.py`, `synthDrivers/{espeak,oneCore,sapi5}.py`, `nvwave.py`, `addonHandler/`, `addonStore/`, the imported Developer Guide, and `projectDocs/dev/addons.md`. Pinned evidence is authoritative for the design baseline but not automatically current at release.
