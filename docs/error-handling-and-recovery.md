# Error handling and recovery

## Policy

Stable error codes cross layers; exceptions do not. Severity is `info`, `recoverable`, `driverUnavailable`, or `internalFatal`. Retry only idempotent operations, with bounded exponential delay off NVDA's main thread. Default circuit breaker: one automatic worker restart for an isolated crash/hang, then open after repeated failure in the same session; exact window/timeouts require experiments. User action may create a new attempt, but never a tight loop.

| Category | Severity/recovery | Retry, fallback, worker/selection | User message and private logging | Required tests |
|---|---|---|---|---|
| Missing runtime | unavailable | no retry; `check()` false; another synth remains available | “Piper speech runtime is missing. Reinstall the add-on.” Log component only. | absent/quarantined files, discovery |
| Incompatible runtime | unavailable | no retry; reject protocol/architecture/version | “Speech runtime is incompatible with this add-on version.” Versions safe to log. | wrong arch/version/protocol |
| Missing model | recoverable | no worker restart; driver selectable without voice | “The selected voice is missing. Choose or install a voice.” No user path. | startup/deletion/selection |
| Invalid model configuration | recoverable | reject model; retain prior model if atomic | “This voice configuration is invalid.” Log schema field code, not content. | malformed JSON/types/ranges |
| Corrupted model | recoverable/security | no retry; quarantine catalogue entry | “Voice verification failed. Reinstall it from a trusted source.” Log expected/actual digest prefix. | bit flip/hash mismatch |
| Unsupported model | recoverable | no retry; no fallback without consent | “This Piper voice format is not supported.” Log opset/capability. | unsupported tensors/opset/rate |
| Model-load failure | recoverable | one clean retry only for transient resource error; otherwise unload/restart if native state uncertain | “The voice could not be loaded.” Exception class/redacted stack. | OOM/native exception/cancel |
| Worker startup failure | recoverable→unavailable | one restart; then circuit open | “The speech worker could not start.” Exit code/version; no command line secrets. | launch denied/early exit/timeout |
| Worker crash | recoverable | stop audio, invalidate, one restart; remain no-model until reload | “The speech engine stopped unexpectedly.” Exit code/crash phase. | before/during/after PCM |
| Worker hang | recoverable | cancel deadline then forced termination/one restart | “The speech engine stopped responding.” Durations/state only. | handshake/load/inference/cancel |
| Protocol mismatch | unavailable | fail closed; no retry same binary | “Speech components are from different versions.” Version ranges. | old/new/unknown major |
| Synthesis failure | recoverable | fail job; retry only explicit/transient classification | “Speech could not be generated.” Model digest prefix, lengths, no text. | backend errors/partial PCM |
| Malformed worker response | internal/security | fail job, terminate worker, circuit policy | “The speech engine returned invalid data.” Frame/type/size only. | fuzzed framing/enums/order |
| Cancellation timeout | recoverable | force stop worker; one restart | Normally silent; announce only if driver becomes unavailable. | missing ack/uninterruptible call |
| Audio-device failure | recoverable | stop; recreate on later speech; no inference retry loop | “Audio output is unavailable. Check the selected device.” Device ID redacted. | unplug/default change/resume |
| Unsupported command | warning/job conversion | documented fallback/skip; structural command fails before worker | Usually no UI; debug code and command class only. | every command/fallback/order |
| Invalid setting | recoverable | restore last valid/default; no worker restart unless model-affecting | “The setting was reset because its value was invalid.” ID, not value if sensitive. | type/range/newer schema |
| Disk-space failure | recoverable | abort import/update atomically; keep existing model | “Not enough disk space to install this voice.” Safe required/free sizes. | staging/commit/cleanup |
| Permission failure | recoverable | no repeated retry; choose valid directory | “The voice folder cannot be accessed.” Operation/error code, path redacted. | read/write/delete denied |
| Antivirus quarantine | unavailable/recoverable | no bypass; direct to provenance/reinstall/false-positive process | “A required speech component is unavailable, possibly removed by security software.” File basename/digest. | missing after install/start |
| Update incompatibility | unavailable | preserve data; require matching release/rollback | “The add-on and speech runtime must be updated together.” Versions. | upgrade/downgrade/migration |
| Internal programming error | internalFatal | stop current work; no blind retry; fallback synth if selection fails | “Piper speech encountered an internal error. Choose another synthesizer and report the problem.” Redacted traceback. | injected invariant/assertion faults |

## Notification and fallback rules

Errors are announced once per actionable incident, never once per keypress. A driver construction/check failure lets NVDA's verified selection fallback operate. Runtime/model/audio operational failures keep the driver selectable when repair is possible; repeated worker failure makes the instance unavailable and asks the user to choose another synthesizer. The add-on never selects a different voice/language silently.

Cancelled jobs do not become failed. Failed/cancelled jobs emit no stale index and no completion unless a target-NVDA integration experiment establishes a required failure-completion handshake; that result must update all design documents.
