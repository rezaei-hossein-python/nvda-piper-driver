# Phase 2J portable-NVDA validation

## Safety boundary

Only the portable NVDA 2026.1.1 AMD64 copy at `D:\NVDA` may be used. Before any portable operation, the user must manually close every running NVDA instance and confirm this. Project code and tooling must not terminate an unidentified NVDA process. The primary installation must not be modified or tested.

## Automated gate

Portable testing starts only after source tests, the retained-runtime controller test, syntax validation, and package-boundary checks pass. The controlled launch continues to require the exact Phase 2C marker and explicit runtime, model, and configuration paths. Those local paths are not recorded here or packaged.

The language-metadata pre-portable rerun passed 91 discovered source tests with four designed asset/archive skips, including all 15 focused driver tests. Explicit ignored-asset validation passed all 13 focused controller/bridge tests, including two real child integrations, plus the standalone model test. The built-archive run passed 95 tests with three designed runtime-asset skips. Two clean builds produced the same 11 archive members and identical per-member SHA-256 hashes. Syntax, relative-link, duplicate-heading, malformed-character, language-hardcoding, networking-import, forbidden-package-artifact, and diff checks passed.

## Launch syntax

Both launches use numeric logging because pinned NVDA accepts integer log levels. Normal mode uses:

```text
D:\NVDA\nvda.exe --config-path "D:\NVDA\phase2iConfig" --log-file "D:\NVDA\phase2iConfig\phase2j-normal-validated.log" --log-level 20
```

Controlled mode uses the same argument form plus the exact Phase 2C marker and explicit ignored runtime, model, and configuration paths inherited by that portable process. The earlier `--log-level=INFO` attempt was invalid and exited during command-line parsing; it is not validation evidence.

## Manual procedure and measurements

A successful follow-up manual run must verify normal gated absence, controlled selection, responsiveness during cold loading and rapid navigation, audible current speech, replacement of stale speech, cancellation with no resumed stale audio, switching to eSpeak, clean exit, no surviving worker, and logs free of watchdog recovery, tracebacks, critical errors, and fixture text.

Measure `speak()` caller return where observable, cold-load responsiveness, time to first audible output, cancel-to-silence, replacement behavior, and worker shutdown without claiming unsupported precision or production readiness.

## Recorded result

Normal mode started with the isolated portable configuration, loaded eSpeak, omitted NVDA Piper Driver from the synthesizer list as intended, and exited normally according to the user. Its info log contained no add-on import error, traceback, critical error, watchdog recovery, or speech fixture text.

The synthesizer-list discrepancy was resolved without a code correction. Content-free same-process diagnostics recorded three fresh constructions of pinned `SynthesizerSelectionDialog`; each received six entries from `getSynthList()` and inserted `nvdaPiperDriver` / `NVDA Piper Driver` into the visible choice. The user confirmed it through both `NVDA+Ctrl+S` and Settings → Speech → Change. The earlier observation was a UI-observation mismatch, and a modal response dialog had blocked at least one attempt.

The first controlled run selected NVDA Piper Driver successfully. Normal NVDA speech then produced no Piper audio. Pinned `SpeechManager._ensureEndUtterance()` appends an `IndexCommand` to an ordinary utterance that does not already end in one (`source/speech/manager.py`, lines 322–325); conversion preserved it as an immutable `IndexItem`, and the then index-free Phase 2J `_extractText()` rejected it. The failure occurred on NVDA's main thread before controller submission, so no child worker, PCM, playback, completion, replacement, or cancellation behavior ran.

The info log recorded 57 tracebacks with the same bounded, content-free `Phase 2J speech item is unsupported` failure. It contained no watchdog recovery, background-runtime error, speech payload, WAV, or PCM dump. The user switched back to eSpeak and confirmed audible fallback, then exited normally. No NVDA or worker process remained.

The narrow correction accepts exact `IndexItem` values as non-synthesized metadata while traversing the immutable job in order. Indexes contribute no text, separator, request field, retained state, or notification; exact `TextItem` values before and after them are concatenated unchanged. Index-only or otherwise text-empty jobs raise the bounded content-free `Phase 2J speech is empty` error. Break, character mode, language change, prosody, phoneme, and arbitrary items remain unsupported. The correction required renewed portable validation; its result follows.

The renewed controlled run deployed the corrected 11-member package, removed only the portable add-on's stale bytecode, and verified every installed file hash against the built archive. The driver selected successfully, but the user heard no Piper speech; switching back to eSpeak restored audible speech and portable NVDA then exited normally. The log recorded eight new content-free main-thread tracebacks at the non-text/non-index rejection branch, no `speech is empty` error, no background-runtime failure, and no child startup.

Pinned source and portable configuration establish the remaining item. The portable profile does not override `speech.autoLanguageSwitching`, whose pinned default is `true`. `speech.speak()` therefore inserts `LangChangeCommand` before text when the current language changes (`source/speech/speech.py`, lines 1191–1192); `SpeechManager` passes it while voice switching is enabled (`source/speech/manager.py`, lines 370–373); Phase 2E converts it to `LanguageChangeItem` (`conversion.py`, lines 66–71); and the Phase 2J extractor rejects it at `nvdaPiperDriver.py`, line 153. Supporting language changes is explicitly outside the mandatory-index correction, so Phase 2J remains **incomplete**. Objective checks found zero NVDA and worker processes, no watchdog or critical entry, no background-runtime error, no WAV/PCM/diagnostic artifact, and a clean final eSpeak load. The tracebacks themselves remain a failed exit criterion and demonstrate that unsupported speech can still flood event errors.

The next narrow correction tolerates exact `LanguageChangeItem` values as discarded NVDA metadata alongside `IndexItem`. Language metadata before, between, or after text—including repeated values and `None`—adds no text or separator and never reaches the controller request or child. It is not logged or retained, does not validate the locale, and cannot change the explicitly configured model, configuration, or voice. Jobs containing only index/language metadata use the same bounded `Phase 2J speech is empty` rejection. All other item types and subclasses remain unsupported. This is compatibility with NVDA's ordinary sequence shape, not advertised language-command or multi-model support.

## Final controlled run after language compatibility correction

The final 11-member package was deployed only to the authorized portable profile and launched with the exact Phase 2C marker, explicit ignored runtime/model/configuration paths, portable configuration, and numeric `--log-level 20`. The driver appeared in the synthesizer list and was selected successfully. The user heard Piper review speech and confirmed that Ctrl stopped it. Piper had noticeably more delay than eSpeak. Typed-character echo remained unavailable, and NVDA Read All (`NVDA+Down`) did not proceed correctly; those paths still contain unsupported command items and were not broadened in Phase 2J. The user had previously confirmed that switching back to eSpeak produced speech and that Piper did not resume.

The final log recorded zero tracebacks, critical errors, ordinary error entries, watchdog/recovery entries, or background-runtime failures. It recorded 14 fixed `unsupportedItem` warnings for rejected out-of-scope sequences; no speech text, language value, PCM, WAV, or serialized job content was logged. No runtime worker survived. The log reached `NVDA exit`, and after the user manually closed the remaining process, objective checks found zero NVDA and worker processes.

The rejection boundary now catches only its own fixed extraction errors before they escape into NVDA's event handlers. It emits at most one content-free warning during a consecutive rejection episode, resets after a valid text utterance, submits no rejected request, and retains no rejected content. Character mode, breaks, prosody, phonemes, arbitrary objects, and other unsupported items remain unsupported. This prevents traceback/event-argument leakage but does not add character echo or Read All support.

Phase 2J remains **incomplete**. Background Piper speech and cancellation were observed, but the latency remains unsuitable for the intended interaction, typed-character echo and Read All are not supported, and exact rapid-replacement, completion-timing, and cancel-to-silence measurements were not established in this run. Phase 2K is not begun.

## Edit-box recovery correction pending portable validation

The current source correction tolerates NVDA's `SuppressUnicodeNormalizationCommand`
and `BeepCommand` in typed-spelling sequences, catches conversion failures at
the driver boundary, consumes only real rejected indexes, and returns the
background controller to `READY` after worker errors. A manual portable run is
still required to confirm edit-box entry/exit, typed character and word echo,
and later focus speech without switching synthesizers.

## Portable confirmation after restart-budget correction

The user confirmed that the rebuilt portable run now speaks letters and numbers,
reads the document with NVDA+Down, and has materially better speed. The latest
portable log contains no worker failure, restart-limit, traceback, critical, or
watchdog entries. It contains one bounded `emptySpeech` rejection and reaches
`NVDA exit` cleanly. Final cancellation, rapid replacement, and post-Read-All
navigation checks remain to be recorded.

## Phase 2J interaction-performance investigation

The pinned eSpeak and speech sources show that typed-character echo depends on `CharacterModeCommand`, while Read All depends on callback-backed `IndexCommand` notifications. The current driver deliberately supports neither behavior: CharacterMode remains rejected because silently concatenating characters can change meaning, and indexes are discarded because no valid PCM-position mapping exists. The new evidence documents this as a hard Read All boundary rather than fabricating callbacks or indexes.

Standalone Piper warm first-chunk evidence is approximately 0.061 seconds for the approved short fixture, but the one-shot NVDA path repeats approximately 1.9 seconds of model loading per request. No persistent worker, streaming protocol, cache, or eSpeak hybrid was introduced in this investigation. Portable subjective latency remains noticeably worse than eSpeak, with no synchronized event-to-audio measurement yet available.

## Persistent worker and interaction correction

The implementation now replaces the one-shot path with one persistent framed child per driver session. It loads the configured model once, preserves index boundaries as immutable segments, dispatches real `synthIndexReached` callbacks after each segment's playback, isolates `CharacterModeItem` text, and retains one active plus one replaceable pending request. Retained-model integration passed multiple warm requests and ordered index delivery; a controlled bridge measurement was approximately 3.287 seconds for the first request and 0.093 seconds for the next warm request on CPU. Portable validation is pending for typed-character echo, Read All progression, rapid replacement, cancellation, watchdog behavior, and eSpeak comparison. Phase 2J remains incomplete until those observations are confirmed.

The first correctly deployed persistent-worker portable capture recorded the expected `LanguageChangeItem`/`CharacterModeItem`/`IndexItem` sequence shapes, proving the extraction boundary is reached. It also exposed a clear controller defect: the consecutive restart counter reached `restartLimit` during rapid replacement, so later requests were rejected and character echo remained inaudible. The counter is now reset after a successful worker handshake; no further portable result is claimed yet.
