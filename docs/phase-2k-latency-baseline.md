# Phase 2K latency baseline

Status: Proposed

Measurements used `time.perf_counter()` on the retained local Windows Python 3.12 runtime, CPU execution, the ignored Lessac validation model, and one persistent worker. Speech content was used only as fixed benchmark input and was never written to metrics or logs. Each worker run recorded five samples per category.

| Case | Median bridge time | Range |
| --- | ---: | ---: |
| Character | 26.9 ms | 24.2–28.4 ms |
| Digit | 24.8 ms | 23.5–27.3 ms |
| Punctuation announcement | 25.6 ms | 23.5–27.2 ms |
| Short word | 26.5 ms | 24.5–31.3 ms |
| Short control | 26.1 ms | 25.7–29.7 ms |
| Navigation phrase | 39.2 ms | 37.3–50.5 ms |
| Short sentence | 79.3 ms | 71.8–80.6 ms |

The first request measured approximately 2.3 seconds before warm-up. With warm-up, process creation was 9.6 ms, readiness after process creation was 2,152.5 ms, and the first request response after IPC send was 31.8 ms. The total first-request wall time remains approximately 2.0 seconds because model loading is dominant; the cost now occurs before readiness and outside the first user utterance.

Cancellation returned to the caller in 0.18 ms and the worker returned in approximately 2.0 ms. These are bridge timings, not NVDA event-to-audible timings.

Piper yielded one complete chunk for each tested short, sentence, and long case, so frame-level streaming was not claimed. Physical audible onset, NVDA dispatch, and eSpeak comparison require portable validation.

The driver now records content-free stage timestamps through first `WavePlayer.feed()` and playback drain. These traces establish the complete in-process boundary but cannot provide a physical microphone/audible-onset timestamp; portable correlation is required.

## Restored-model rerun

After restoring the hash-verified validation files and rebuilding the local tool environment, three one-shot samples per category measured approximately 1,959-2,083 ms. Five persistent warm samples measured these medians: character 23.5 ms, digit 27.2 ms, punctuation 32.5 ms, word 28.2 ms, and navigation 50.5 ms (maximums 28.7, 32.8, 34.5, 33.1, and 53.1 ms respectively). A first persistent request after startup remained approximately 1,983 ms because model loading dominates. A cancellation caller return was 0.4 ms; the next request recovered by starting a fresh worker in approximately 1,978 ms. Hard process termination remains the cancellation fallback, so that recovery necessarily reloads the model.
