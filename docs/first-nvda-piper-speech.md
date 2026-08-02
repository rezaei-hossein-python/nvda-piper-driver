# First Piper speech through NVDA

## Phase 2I purpose and boundary

Phase 2I is a development-only proof that one immutable `SpeechJob` can cross a process boundary, be synthesized by the Phase 2H Piper environment, and be played as PCM by portable NVDA. It is not a production speech path. It adds no queue, background synthesis, overlap, streaming optimization, model discovery, voice download, language selection, indexes, or production cancellation.

The only authorized NVDA instance is the portable copy at `D:\NVDA`. The primary installed NVDA is neither modified nor tested.

## Architecture considered

Three approaches were reconsidered:

1. Direct in-process Piper would be the smallest call graph, but would load Piper, ONNX Runtime, and native dependencies into NVDA. A native failure or ABI conflict would affect the screen reader.
2. A child worker preserves the Proposed long-term process-isolation boundary and allows deterministic process teardown.
3. A CLI wrapper also isolates native code, but adds an interface not used by the verified Phase 2H Python API and offers no advantage for this one-model experiment.

Phase 2I therefore uses a one-shot child Python process. The parent passes a bounded UTF-8 JSON request on standard input and receives a bounded metadata header followed by raw PCM on standard output. Arguments are a list, `shell=False`, runtime/model/config paths are explicit, and no network or filesystem discovery occurs. The worker handles exactly one utterance and exits. This is deliberately narrower than the Proposed long-running worker architecture.

## Development gate

The driver remains unavailable unless all four process-local conditions hold:

- `NVDA_PIPER_DRIVER_TEST_ONLY_MOCK_RUNTIME` exactly equals the Phase 2C marker value;
- `NVDA_PIPER_RUNTIME_PYTHON` names an existing `.exe`;
- `NVDA_PIPER_MODEL_PATH` names an existing `.onnx`;
- `NVDA_PIPER_CONFIG_PATH` names an existing `.json`.

No paths are inferred, searched for, or persisted by the add-on. The runtime and model are not packaged.

## Speech and audio path

`SynthDriver.speak()` converts the exact NVDA sequence to an immutable job and accepts only text, model-language markers, and explicit phoneme fallback text. Model-language markers do not select or switch a model; they are structurally ignored because the explicit configured model controls language. Every other item, including indexes and prosody commands, fails with a fixed content-free error before a worker starts. The driver temporarily joins accepted text and sends one bounded utterance to the worker. The child loads the configured Piper model through the pinned Phase 2H environment and returns signed little-endian 16-bit mono PCM plus its model-derived sample rate. The parent validates generation ID, job ID, channel count, width, rate, and PCM bounds before constructing NVDA's pinned `nvwave.WavePlayer` with the configured output device.

The prototype feeds one complete PCM buffer, calls `idle()` to wait for playback completion, and then emits `synthDoneSpeaking`. It emits no index notifications. The full buffer and text exist only for the duration of the synchronous call and are not stored afterward.

## Teardown and stale data

`cancel()` is safe teardown only. It invalidates the active generation, stops playback, and terminates the child if one is active. A 60-second provisional worker timeout terminates and, if necessary, kills a stuck child. PCM whose generation or job correlation is wrong is rejected before playback. This does not interrupt an ONNX inference already running in a measurable production sense, and it does not establish cancel-to-silence latency.

Synthesizer termination stops playback, closes `WavePlayer`, stops the child, and delegates to NVDA's base cleanup. A new utterance starts a new child, so model loading is cold on every utterance.

## Privacy and language neutrality

No frame, WAV, `SpeechJob`, text, IPA, or fallback text is persisted. Fixed classified errors omit request text and child stderr. The parent retains only current numeric correlation state while speaking.

Runtime behavior is model-driven. There is no locale allowlist, script detection, translation, language inference, preferred language, or fixed phoneme inventory. The retained English Lessac model is only the already approved validation asset; no language receives a special implementation branch.

## Known limitations

- `speak()` performs cold model loading, synthesis, complete-buffer transfer, playback, and drain synchronously. It blocks NVDA and is not acceptable for normal navigation.
- There is no queue, overlap policy, streaming, active-inference cancellation, index support, pause/resume, model switching UI, or accessible runtime error notification.
- Rate remains a development setting snapshot and is not mapped to Piper synthesis.
- Only one verified model/runtime/environment combination has been exercised.
- Runtime and model redistribution remain unresolved.
- The binary response framing is a narrow development bridge, not the accepted production protocol.

The runtime ADR remains `Proposed`. Phase 2J is not started.

## Verification status

Automated child integration produced nonempty 16 kHz, mono, 16-bit PCM from the retained verified model and observed child exit. Portable NVDA loaded the driver, ran the single-fixture path without an info-level error, switched back to eSpeak, exited cleanly, and left no worker. The user heard both the Piper fixture and the eSpeak fixture and confirmed the switch. Phase 2I exit criteria are met; Phase 2J is not started.
