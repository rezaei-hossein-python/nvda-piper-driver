# Piper interactive performance evidence

## Current architecture

The Phase 2J development path now uses one persistent child per driver session. The child imports Piper, loads the ONNX model once, and serves one framed segment request at a time. The controller keeps NVDA's main thread responsive, allows one active plus one newest pending request, and terminates/restarts the child for bounded hard cancellation. The generator remains segment-sized; this is not frame-level streaming. No cache or hybrid eSpeak output path was added.

## Measurements available

The approved standalone Lessac validation model was measured on the development machine with `time.perf_counter`, one discarded warm-up, and five recorded runs. The loaded in-process adapter produced one sentence chunk for the short case. Its first-chunk times were 0.059–0.066 seconds, median approximately 0.061 seconds; completion was 0.062–0.068 seconds. The standalone model load was approximately 1.83–2.07 seconds, median approximately 1.91 seconds. The current NVDA one-shot path therefore has a cold-load cost that dominates short utterances.

No synchronized `speak()`-to-audible timer, NVDA first-PCM timer, cancel-to-silence timer, Read All transition timer, CPU sample, or memory sample was captured. The user's portable observation was that Piper review speech had noticeable delay relative to eSpeak; this is qualitative evidence only. eSpeak's compact native engine was not measured with the same event probes, so no false numeric comparison is reported.

## Candidate decisions

| Option | Evidence | Decision in this task |
|---|---|---|
| Persistent Piper child, one active request | Amortizes model load while retaining process isolation; framed readiness and bounded restart are implemented | Selected for Phase 2J; portable latency and cancellation evidence remains pending |
| Sentence/chunk streaming | Piper's Python API exposes sentence-sized chunks, not verified frame callbacks | Not called frame-level streaming; current NVDA bridge buffers complete PCM |
| Dynamic text/PCM cache | No benchmark yet proves a useful hit rate; privacy and model/settings invalidation need design | Not implemented |
| Lower-latency compatible model/provider settings | Model-driven and potentially useful, but model quality/provider compatibility must be measured per voice | Not selected or hardcoded |
| Optional eSpeak character fallback | Could improve character response but creates voice/settings/language consistency and licensing questions | Research only; not implemented |

## Engineering targets

The provisional goals remain 10 ms caller return, warm character first playback below 100 ms, warm short navigation below 150 ms, and local stop below 50 ms. Current evidence proves only nonblocking caller submission and qualitative Piper delay; it does not establish those targets. Read All correctness is blocked by required index callbacks, and character echo is blocked by the unimplemented `CharacterModeItem` boundary.

The runtime ADR remains `Status: Proposed`. No production suitability, model compatibility across all voices, or screen-reader readiness is claimed. Warm multi-request and index-order integration tests pass with the retained validation model; portable typed-echo and Read All evidence is still required.

## Warm short-request measurement

With the retained worker and approved Lessac model, a direct bridge run measured
1967.2 ms for the first one-character request, then 22.0 ms for a warm
character, 32.0 ms for a warm word, and 32.7 ms for warm navigation text. The
worker PID remained constant across all four requests. These measurements
isolate the worker and protocol path; portable NVDA event-to-audio and eSpeak
comparison measurements remain pending.

The short-character replacement path now keeps an active short character in the
warm worker, invalidates its stale result, and runs only the newest pending
character without terminating the worker. A warm eight-character replacement
stress run completed in 105.4 ms with no errors and one worker PID.

## Persistent-worker measurement

Using the retained ignored Lessac model, the isolated Python 3.12 environment, CPU execution, and `time.perf_counter`, one persistent bridge run measured approximately 3.287 seconds for its first request (process startup plus model load) and 0.093 seconds for the next warm request. The returned format was mono, signed 16-bit PCM at 16 kHz with 40,960 bytes for the fixture. This is one controlled sample, not a percentile or a screen-reader suitability claim. Segment boundaries add a synthesis operation per segment; portable NVDA measurements remain required.
