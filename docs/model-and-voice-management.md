# Model and voice management

## Component separation

1. **Driver:** NVDA adapter, settings, job/audio lifecycle; no model parsing beyond safe catalogue metadata.
2. **Runtime worker:** pinned Piper-compatible inference and phonemization; replaceable independently in design, packaged only after review.
3. **Voice models:** separately installed `.onnx` plus matching `.onnx.json` and project provenance record; never executable by policy but treated as hostile native-parser input.
4. **Future downloader:** optional, separately approved design; absent initially. Driver operation never requires network access.

## Initial directory design

Use a user-writable project data root outside replaceable add-on program files. Each imported voice occupies an immutable version directory: `<root>/voices/<voiceId>/<contentDigest>/model.onnx`, `model.onnx.json`, and project metadata `voice.json`. A small atomic catalogue references validated versions. Paths are conceptual until NVDA configuration/data-directory guidance is verified in Phase 2.

Manual installation is copy/import through an accessible file dialog: select local model/config (or a future safe package), display source/licence/checksum information, validate into a private staging directory, then atomically move into the managed root. No network, elevation, shell, archive extraction, or companion installer is required initially.

## Identity and metadata

`voiceId` is a stable, case-sensitive project identifier derived from publisher namespace plus declared voice/locale/speaker identity—not a display name or path. Content digest distinguishes upgrades. Display name is localized presentation metadata and collisions are disambiguated with locale/publisher. Required metadata: schema version, model/config SHA-256, exact upstream/source URL or local-origin declaration, acquisition date, model and dataset licence identifiers/text references, attribution, speaker/consent statement where supplied, locale/BCP-47-like tag, speakers, sample rate, Piper format/schema/opset/runtime range, and validation status.

Missing legal/provenance information means “unverified”; it may be usable only in explicit developer experiments and is release-ineligible. A repository licence label does not resolve model, dataset, speaker consent, commercial use, redistribution, derivatives, or attribution. No legal clearance is claimed.

## Validation and discovery

- Canonical path remains under approved roots; regular files only; reject links/reparse escapes, devices, UNC unless explicitly designed later, duplicate/conflicting names, and excessive size.
- Require exact ONNX/JSON pairing; schema/type/range/encoding validation; finite numeric values; supported sample rate, phoneme map, speakers, tensor interface/opset/runtime capabilities.
- Verify stored digests every import and before load according to cache policy; worker rechecks identity before parsing.
- Discovery never opens every model through ONNX on NVDA's main thread. Read bounded catalogue metadata asynchronously; quarantine invalid entries individually.
- Duplicate content is one physical version with aliases prohibited initially. Same voice ID/different digest is an upgrade candidate, never silent replacement.

## Selection and lifecycle

Persist stable voice ID plus digest/version preference, not an absolute path. On startup, select it only if valid. If absent/corrupt, remain `readyWithoutModel` and guide the user; do not silently speak with an unexpected language. A user-confirmed fallback may choose the latest verified version of the same voice, then a configured fallback voice. No global arbitrary fallback is automatic.

Multi-speaker models expose stable child IDs `<voiceId>#<speakerId>` when speaker metadata is verified. Language changes inside a job use the selected model only when it declares support; automatic model switching mid-job is deferred because it complicates latency, voice consistency, and indexes. Arbitrary Piper languages are supported by metadata/capability, not hardcoded lists. Persian is a primary validation locale covering script, ZWNJ, diacritics, numbers, punctuation, mixed language, and normalization; it receives no privileged code path.

Removal first cancels/changes away from a selected/loaded model, unloads it, closes handles, then atomically removes catalogue visibility. Physical deletion is explicit and recoverable where practical; failure leaves a pending-removal record. Model upgrades install side by side, validate, switch atomically, and retain rollback until user/policy cleanup. Never delete a model merely because the add-on is uninstalled without explicit consent.

## Distribution choices

| Choice | Initial decision | Reason |
|---|---|---|
| Bundle voices in driver | No | Size, updates, multilingual choice, and independent licences. |
| Separate manual import | Yes | Fully offline, explicit provenance, simplest trust boundary. |
| Companion installer | No | Extra executable/elevation/update and accessibility burden. |
| Separate voice add-ons/packages | Research later | Could aid Store delivery but creates ownership/version/uninstall questions. |
| In-add-on downloader | Future only | Requires approved network/privacy/catalogue/archive design and user consent. |

## Failure behavior and open questions

Invalid/corrupt/unsupported models remain visible only in diagnostics with safe reason codes; they never disable other voices. Deletion of an already loaded file may not invalidate runtime memory; discovery marks it missing for future loads and prompts after current safe boundary.

Unresolved: authoritative Piper compatibility schema/range, permissible managed data root for installed/portable NVDA, Store expectations for voice packages, and legally adequate metadata/source delivery. All require confirmation before public model distribution.
