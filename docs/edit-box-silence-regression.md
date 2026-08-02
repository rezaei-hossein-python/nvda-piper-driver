# Edit-box silence regression

Status: Proposed

## Diagnosis

Pinned NVDA's typed-spelling path can add `SuppressUnicodeNormalizationCommand`
and `BeepCommand` around `CharacterModeCommand` and text. The Piper converter
previously raised `UnsupportedSpeechItemError` for those speech-level metadata
items. Because `SynthDriver.speak()` allowed the conversion exception to escape,
SpeechManager retained the utterance's real index and waited for progress. A
subsequent synthesizer switch recreated state, which explains the observed
recovery without making synthesizer switching an acceptable fix.

The background controller also kept its state at `FAILED` after a worker error.
Its `finally` block now always clears the active generation and returns to
`READY` unless shutdown is in progress.

## Correction

The driver now ignores NVDA-owned normalization and beep metadata, preserving
the NVDA-provided spoken text and character-mode boundaries. If conversion or
extraction rejects a request, the driver does not submit it; it consumes only
the real `IndexCommand` values from that rejected sequence so SpeechManager can
advance without fabricated completion callbacks.

No speech text, character values, page content, PCM, or model data is logged.

## Verification

Focused controller and retained-runtime tests pass, including worker-error
recovery. Manual portable validation remains required for edit-box entry,
typed character/word echo, leaving the control, and later focus speech.

## Rapid-replacement evidence

The first controlled portable reproduction produced repeated
`NVDA Piper background runtime failure: restartLimit` entries during rapid
character/document navigation. `PersistentRuntimeBridge.interrupt()` was
terminating workers for expected replacement but leaving the consecutive-start
budget consumed. After three interrupted starts, the bridge rejected every
later request until synthesizer switching recreated the driver.

The bridge now clears only that consecutive-start budget when it interrupts a
currently live worker for replacement. Unprompted worker-start failures remain
bounded by the restart limit. A real-runtime stress run of eight rapid
character requests completed the newest request with no error and one live
worker.

## Short-character latency correction

An active short character request (one segment, character mode, at most 32 code
points) is now allowed to finish in the warm worker while its generation is
invalidated. The newest pending character replaces older pending work. Longer
speech and word/navigation requests retain hard cancellation. This avoids a
model reload for each rapid character while preserving bounded cancellation for
normal speech.
