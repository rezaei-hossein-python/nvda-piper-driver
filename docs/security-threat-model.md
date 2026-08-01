# Practical security threat model

> Phase 2E's pure converter performs no I/O and does not log or globally retain speech text. Exact container/item checks, bounded identifiers, immutable copies, and text-free unsupported-item errors reduce accidental execution and disclosure risk, but do not establish safety of later synthesis, IPC, models, or audio.

> Phase 2F adds a pre-decode byte limit, strict UTF-8/JSON/schema validation, duplicate-key and non-finite-number rejection, bounded fields, and metadata-only fake-worker state. This reduces parser and retention risk in the in-process prototype only; no transport ACL, process containment, crash isolation, or formal security claim exists.

## Scope, assets, and boundaries

This is defensive design, not certification or legal clearance. Assets: NVDA availability, user text, local files/configuration/models, audio privacy/integrity, process and release integrity, and user trust. Boundaries: NVDA core ↔ add-on; add-on ↔ child IPC; worker ↔ native Piper/eSpeak/ONNX Runtime; runtime ↔ model/config; managed data ↔ temporary storage; repository/release pipeline ↔ installed asset; and a future downloader ↔ network/catalogue. Secure-screen use is unsupported.

Likelihood is qualitative (`low`, `medium`, `high`) before field evidence.

| Threat | Likelihood / impact | Mitigation | Residual risk and verification |
|---|---|---|---|
| Malicious/malformed model | medium / critical | verify provenance/digest/schema/size; approved roots; worker isolation; resource limits | Native zero-days remain. Fuzz metadata, corrupt models, crash containment. |
| DLL hijacking | medium / critical | absolute paths, restricted DLL directories, packaged inventory; never CWD/PATH | OS/runtime loader mistakes remain. Clean-machine loader trace and planted-DLL test. |
| Unsafe subprocess/command injection | low / critical | fixed executable/arguments, `shell=False`, no text/path interpolation or worker command field | Dependency launch behavior remains. Adversarial path/text tests and review. |
| Path/archive traversal | medium / high | canonical containment, reject absolute/drive/UNC/`..`/links/reparse; no archive import initially | Filesystem races remain. Symlink/reparse/race corpus; future extractor audit. |
| Decompression bomb | low initially / high | no archives initially; future count/compressed/expanded/ratio/time/disk limits | Parser resource use remains. Bomb fixtures only if downloader/package added. |
| IPC spoofing | low / high | inherited/restricted pipes, per-launch session, peer/ownership controls, no listener | Same-user compromise may still inject. Unauthorized client/session tests. |
| Oversized/malformed IPC | medium / high | length-before-allocation, schema/enums/order limits, close on violation | JSON/parser bugs remain. Property/fuzz tests and memory monitoring. |
| Worker DoS/hang | medium / high | progress deadlines, cancel, containment, forced termination, one restart/circuit breaker | Repeated user-triggered expensive inputs. Hang and restart-soak tests. |
| Memory/CPU exhaustion | medium / high | model/text/tensor/queue limits, one active inference, OS limits where feasible | Valid large models may exceed weak hardware. Stress/resource telemetry without text. |
| Log leakage | medium / high | no text/IPA/PCM/full paths; centralized redaction; safe error codes | Exceptions may contain data. Log-capture tests with sentinel secrets. |
| Temp/stale file leakage | low initially / high | stream PCM; private staging; restrictive ACL; atomic cleanup/startup scavenging | Crash can leave staging. Forced-crash cleanup tests. |
| Compromised release asset | low / critical | protected review, pinned actions/dependencies, immutable versions, SHA-256, Store scan, reproducibility/SBOM | Maintainer/account compromise remains. Independent hash/rebuild verification. |
| Dependency compromise | medium / critical | pin exact sources/hashes, minimal deps, Dependabot/manual triage, provenance/licence inventory | Upstream compromise before pin. Review/update sandbox and source comparison. |
| Antivirus false positive | medium / high availability | transparent provenance/checksums, no obfuscation, scan candidates, official false-positive process | Vendors can still quarantine. Clean-machine multi-engine release gate. |
| Untrusted model metadata | high / high | treat all strings as data; bounded UTF-8/schema; escape UI/log; never executable/path authority | Display spoofing remains. Control/bidi/long-string tests. |
| Insecure download | future / critical | no network initially; future explicit consent, HTTPS, signed/pinned catalogue and SHA-256, atomic staging | Server/key compromise remains. MITM/hash/catalogue tests before feature. |
| Unsupported secure-screen use | medium / critical privacy | declare unavailable; no copying runtime/models/config into secure context; separate future threat review | User expectation confusion. Manual secure-screen non-availability test and docs. |
| Stale audio/index after cancel | high / high privacy/usability | generation/session/job/sequence checks before buffer/notify; immediate player stop | Hardware buffer may retain tiny audio. Cancel-to-silence measurement. |
| Model removal/update race | medium / high | immutable version dirs, open-handle ownership, cancel/unload before deletion, atomic catalogue | Windows locks/quarantine can interrupt. Upgrade/remove/crash tests. |

## Security release gates

Threat mitigations become release requirements only when the corresponding feature exists. Before native runtime integration: dependency inventory, safe DLL loading, worker containment, IPC parser tests, redaction tests, and malformed-model containment block merging. Before any network/archive feature: a revised threat model and explicit design approval are mandatory.
