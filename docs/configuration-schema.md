# Proposed configuration schema

## Principles

Configuration contains preferences, never authoritative model metadata or secrets. Values are validated on read and write; invalid values fall back safely with one redacted warning. Job-relevant values are snapshotted. Schema has an integer version and transactional migrations with backup/rollback. Identifiers below are provisional.

| ID | Type / allowed value | Default | Exposure | Apply/restart | Invalid/migration behavior |
|---|---|---|---|---|---|
| `schemaVersion` | positive integer | current | hidden | load-time | Sequential idempotent migrations; unknown newer schema → safe defaults/read-only diagnostic. |
| `modelDirectory` | canonical local directory under allowed user roots | project-managed data root | accessible dialog, not settings ring | rediscover asynchronously; no NVDA restart | Reject missing/non-directory, unsafe/reparse/UNC policy violations; retain last valid. Paths are not logged. |
| `voiceId` | stable catalogue ID plus optional digest | unset | dialog and NVDA Voice setting/ring when voices exist | cancels current generation and loads model; no promised NVDA restart | Missing ID → no-model state; migrate path-based legacy IDs through catalogue mapping. |
| `rate` | integer 0–100 | 50 pending calibration | NVDA Rate setting/ring and dialog | next job | Clamp only interactive movement; reject corrupt persisted type/range to default. Mapping benchmarked per backend. |
| `volume` | integer 0–100 | 100 | expose only after verified single ownership; ring/dialog | next job, possibly current only after proof | Default on invalid; avoid double scaling. |
| `pitch` | absent initially | — | not exposed | — | Add only with real backend capability and migration. |
| `rateBoost` | absent initially | false if later supported | not exposed initially | next job | Capability-gated future boolean; never emulate with undocumented ranges. |
| `workerStartupTimeoutMode` | enum `automatic`, `relaxed` | automatic | advanced dialog only after need | next worker start | No raw milliseconds initially; measured profiles avoid unsafe user tuning. |
| `diagnosticMode` | boolean | false | advanced dialog | immediate | Adds state/timing detail, never speech text/PCM. Auto-resets only if policy documented. |
| `loggingLevel` | enum `normal`, `debug` | normal | advanced dialog | immediate | Must not override NVDA global semantics without verified API; debug still redacted. |
| `modelCacheBehavior` | enum `keepSelectedLoaded`, `unloadWhenDeselected` | keepSelectedLoaded | advanced, after memory experiments | safe idle boundary | Capability/resource dependent; invalid → default. No multi-model cache initially. |
| `recoveryPreference` | enum `prompt`, `oneAutomaticRestart` | oneAutomaticRestart | advanced dialog | next failure | Never unlimited. Circuit breaker overrides. |

Do not expose raw IPC limits, chunk size, queue depth, inference thread count, execution provider, model scales, noise values, or retry counts during early milestones; they are experimental/system safety controls, not stable user preferences.

## Persistence and migration

Use NVDA's verified configuration mechanisms for add-on settings in Phase 2; do not invent storage hooks. Persist only after successful validation. Write atomically where project-owned files are necessary. A migration records old schema, target schema, outcome code, and duration—not values/paths. Failure restores the previous valid configuration or defaults and leaves voices untouched.

Version changes may rename IDs, convert path selection to stable voice ID, or split defaults. Each migration has pure tests, is idempotent, handles interrupted writes, and is reversible where data loss is possible. Downgrade behavior is documented; an older add-on encountering newer schema must not overwrite it silently.

## User-facing labels

Labels are concise and translatable: “Voice,” “Rate,” “Volume,” “Voice folder,” “Keep selected voice loaded,” “Recovery after speech-engine failure,” and “Diagnostic logging.” Help text explains offline behavior, memory/restart effects, and privacy. Native controls, logical focus order, associated labels, and validation focus restoration are mandatory.
