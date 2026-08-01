# Project governance and support

## Maintainer responsibilities

Maintainers protect NVDA stability and user privacy; review changes and dependencies; keep compatibility, licences, provenance, security, localization, docs, and release evidence current; triage reports; record architecture decisions; and avoid unsupported claims. At least one approving maintainer reviews each code change; security/native/release changes should receive a second independent review when the project has enough maintainers.

Supported releases are explicitly listed current stable versions for which the release matrix passed. Development builds and older/unlisted NVDA, Windows, runtime, and model formats are unsupported experiments. “Last tested” changes only with evidence. No response-time, fix-time, release cadence, or long-term support guarantee is offered.

## Reports and support boundaries

Bug reports request add-on/NVDA/Windows/runtime versions, installed/portable mode, voice ID and digest (not voice data), reproducible steps, expected/actual result, frequency, and redacted log. Reporters must remove speech text, usernames, paths, tokens, and private documents. A future issue template should repeat this warning.

Driver defects include crashes, hangs, cancellation/index/audio/settings/installation behavior, verified-model compatibility, and accessibility. Pronunciation/naturalness/training-data complaints are model-quality issues unless preprocessing is demonstrably wrong; route them to the voice publisher with no promise this project can fix them. Feature requests require use case, accessibility/privacy/performance impact, and fit with current milestone; broad/network/cloud/training work may be declined.

Security reports must eventually use a private channel described in `SECURITY.md`, not public issues. Until created, do not solicit sensitive exploit details publicly; repository hosting's private vulnerability reporting is the preferred future option if enabled. Public support belongs in issues/discussions; private individual support and remote-machine access are out of scope.

## Change and release policy

- Pin dependencies; review upstream release notes, licence/provenance, vulnerabilities, binary hashes, ABI/protocol, and matrix tests before updating. Dependabot is a signal, not authority.
- Release when evidence is ready, not on a promised cadence. Stable, beta, and dev semantics follow current Store metadata.
- Deprecations receive rationale, replacement/migration, warnings where accessible, and at least one documented transition release when feasible. Security/compatibility may require faster removal.
- End of life states last supported release, known risks, model-data handling, and successor/fork information if verified. Do not silently transfer Store ID/publisher trust.
- Contributors are credited in changelog/release notes where appropriate and preserved in history; conduct follows the NVDA Code of Conduct.
- Architecture changes use ADRs with Proposed/Accepted/Superseded status and evidence. The runtime ADR remains Proposed.

## If maintenance stops

Mark the README/repository and Store metadata accurately, stop claiming current compatibility, publish a final advisory if safe, disable unsafe download/update services, preserve source/issues/releases, document how users remove the add-on/models, and seek a transparent successor. Transfer publishing rights only through the official authorization process and with public maintainer consent. If known risk is material, request Store deprecation/removal through current official procedures.

## Files recommended later, not created now

- `SECURITY.md` before accepting external runtime/security reports.
- Bug, accessibility, model-quality, and feature-request issue forms before public beta.
- Pull-request template and release checklist before implementation/release.
- `SUPPORT.md` before public testing.
- `MAINTAINERS.md` when roles exceed repository ownership metadata.
- `CODEOWNERS` only when multiple stable reviewers make it meaningful.

Creating these now would duplicate design without established contacts/workflows. Their timing is tracked in `docs/documentation-plan.md` and `docs/phase-2-implementation-sequence.md`.
