# Repository quality review

## Scope

Review performed 2026-08-01 against the repository after Phase 1B and proposed Phase 1C documentation. This is a critical readiness assessment, not endorsement.

## Perspectives

| Perspective | Evidence-based strengths | Material gaps |
|---|---|---|
| Experienced NVDA add-on developer | Pinned symbols distinguish contract/examples; cancellation/index uncertainty is visible; milestones are narrow. | No AddonTemplate skeleton, executable tests, current NVDA trial, or proof that private audio APIs are safe for an add-on. |
| Store submitter | Current manual workflow, metadata, integrity, VirusTotal, licences, accessibility and matrix are documented. | No publisher/support/security identity, manifest, package, asset, SBOM, notices, validation run, or Store approval. |
| Blind technical user | Offline/no-telemetry goals, keyboard acceptance, errors/model install/uninstall are explicit. | No usable add-on, voice, measured latency, installation path, or user help; research volume can obscure current status. |
| Prospective contributor | AGENTS, contributing rules, architecture boundaries, exact Phase 2 steps, test/CI plans are clear. | No developer environment, issue labels/templates, good-first tasks, test commands, maintainers, or code to orient around. |
| Security-conscious reviewer | Threats, trust boundaries, redaction, process isolation, dependency/model provenance and residual risk are explicit. | No implementation, fuzz results, binary inventory, private reporting policy, reproducibility, or external review. |
| Hiring/portfolio reviewer | Shows disciplined primary-source research, negative findings, ADR restraint, and accessible systems thinking. | Excess documentation before empirical validation risks appearing process-heavy; credibility now depends on executing small milestones and reporting measurements. |

## Quality dimensions

- **Purpose/scope:** clear and realistic in README/AGENTS, but “maintained” is an aspiration until releases/support exist.
- **Evidence:** strong local symbol/path citations and dated primary sources; source register improves auditability. Some ecosystem gaps (Hear2Read source, Sonata forks) remain properly unresolved.
- **Architecture transparency:** strong after Phase 1C; state, job, protocol, audio, model, config, errors, threats and reversal conditions are explicit. It remains speculative until mock/native experiments.
- **Roadmap:** incremental and safety-oriented. Existing Phase 3–11 numbering overlaps with detailed 2A–2J and should be consolidated after Phase 2, not now.
- **Contribution readiness:** policy exists but operational entry points do not. Add templates/security/support only near public testing to avoid empty bureaucracy.
- **Accessibility/security maturity:** criteria are unusually explicit but entirely unvalidated. Avoid describing them as achieved.
- **Maintainability:** separation of concerns and source ownership help; fifteen Phase 1C files create maintenance cost and cross-document drift risk.

## Useful versus redundant documentation

Keep distinct through implementation: state machine, speech job, worker protocol, audio, model management, error taxonomy, threat model, tests, accessibility criteria, Phase 2 sequence, and ADR. They define different review boundaries.

Likely consolidation before beta:

- Merge configuration tables and user-facing error guidance into generated/central Add-on Help sources while retaining technical schemas.
- Merge `implementation-plan.md` and completed portions of `phase-2-implementation-sequence.md`; archive completed milestone details in the journal.
- Make `research-source-register.md` the single external-source index; Phase 1B documents should link rather than duplicate changing status.
- Combine governance, support, and documentation-plan user policies into `SUPPORT.md`, `SECURITY.md`, contribution/release checklists when actual channels/owners exist.
- Keep `architecture.md` as a short map linking detailed documents rather than duplicating them.

## Priority recommendations

1. Stop research expansion after Phase 1C and execute Phase 2A only.
2. Preserve “Proposed” until fake-worker cancellation and real-runtime/audio measurements exist.
3. Add minimal CI in stages; do not deploy every planned scanner on an empty codebase.
4. Establish publisher/support/security ownership before public beta.
5. Publish measured limitations and failures as prominently as successes.

The repository is research-complete for beginning a skeleton, not implementation-complete, release-ready, security-reviewed, legally cleared, or Store-approved.
