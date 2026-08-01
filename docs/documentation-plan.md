# Documentation plan

## Ownership model

Maintainers own technical/release truth; accessibility reviewers own acceptance evidence; translators own locale contributions subject to source review. English Markdown is the source unless a document states otherwise. Generated HTML and translated artifacts follow AddonTemplate conventions once packaging exists.

| Document | Audience / gate | Owner and source of truth | Update triggers |
|---|---|---|---|
| README | all; prototype | maintainers; repository root | status, support, install path, release change |
| Installation guide | testers/users; beta | release maintainer; tested package workflow | package/NVDA/Windows/restart changes |
| Model installation guide | users; prototype before real model | model maintainer; `model-and-voice-management.md` | layout/import/licence/network changes |
| Configuration guide | users; beta | driver maintainer; schema/settings implementation | setting/default/migration changes |
| Troubleshooting | users/support; beta | triage maintainer; error taxonomy | new frequent/error recovery reports |
| Privacy statement | users/reviewers; prototype | security maintainer; threat/log/network design | any data/log/network/temp change |
| Security limitations | users/reviewers; prototype | security maintainer; threat model | boundary/dependency/secure-screen change |
| Supported versions | users/Store; every release | release maintainer; completed matrix | NVDA/Windows/runtime release/test result |
| Supported model format | users/voice publishers; real-runtime prototype | runtime maintainer; validation schema | Piper/ORT/opset/metadata change |
| Known limitations | all; prototype and every release | maintainers; issue/benchmark evidence | confirmed limitation or resolution |
| Performance expectations | users/reviewers; beta | performance owner; reproducible benchmark report | model/runtime/hardware/buffer changes |
| Developer setup | contributors; Phase 2A | maintainer; pinned tools/AddonTemplate | toolchain/dependency/layout changes |
| Architecture overview | contributors/reviewers; now | architecture maintainers; `docs/architecture.md` plus detailed designs | accepted/proposed ADR changes |
| Testing instructions | contributors; Phase 2B onward | test maintainer; `testing-strategy.md` and actual commands | suite/fixture/matrix changes |
| Build instructions | contributors/release; Phase 2A then stable detail | release maintainer; AddonTemplate config | toolchain/package/reproducibility change |
| Contribution guide | contributors; before code | maintainers; `CONTRIBUTING.md` | review/security/test workflow changes |
| Release notes/changelog | users; every release | release maintainer; `CHANGELOG.md` | release candidate changes |
| Licence/third-party notices | users/reviewers; before runtime distribution | dependency owner; inventory/SBOM/upstream texts | any dependency/model/asset change |
| Removal/uninstall behavior | users; beta | release/model maintainer; lifecycle tests | storage/retention/migration changes |
| Accessibility statement | users/reviewers; beta | accessibility reviewer; acceptance results | UI/workflow/known limitation changes |
| Persian validation notes | testers/voice reviewers; real-runtime prototype | language test owner; corpus/matrix results | normalization/model/runtime findings |

Before first public testing, require README/status, install/model/config/troubleshooting, privacy/security limitations, supported versions/model format, known limitations, developer/build/test/contribution instructions, release notes, notices, removal, accessibility statement, and Persian validation status—even if some state “not yet supported.” Stable release additionally requires measured performance expectations, full matrix evidence, translated Add-on Help, final third-party inventory/SBOM, support/security/governance files, and archived immutable release evidence.

## Consolidation policy

`docs/build-and-package.md` is now the Phase 2A source of truth for developer environment setup, package commands, archive allowlisting, and safe installation testing. Before public testing, split user installation instructions from this contributor-focused build record rather than duplicating commands across design documents.

Phase 1C intentionally creates narrow design files for implementability. Before beta, consolidate user-facing material into Add-on Help while retaining technical source documents. Avoid duplicating setting/error tables across help: generate or cross-reference from the authoritative schema/taxonomy. Merge `implementation-plan.md` and the detailed Phase 2 sequence after Phase 2 completes; archive research snapshots rather than maintaining the same current facts in multiple places.
