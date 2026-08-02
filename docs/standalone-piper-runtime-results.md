# Phase 2H standalone Piper runtime results

## Outcome

Phase 2H completed its standalone exit criteria on 2026-08-01 (benchmark record date 2026-08-02 UTC). The current OHF Piper Python runtime loaded one provenance-checked compatible voice, synthesized real audio outside NVDA, produced a structurally valid WAV, passed runtime-dependent tests, and completed repeatable measurements. This is standalone evidence only: it does not prove screen-reader suitability, accept the runtime ADR, or authorize Phase 2I.

No runtime, model, experiment, WAV, or dependency entered the add-on. `SynthDriver.speak()` remains disconnected and no file under `addon/` changed.

## Runtime selection and alternatives

The experiment selected `piper-tts` 1.5.0 from [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), tag `v1.5.0`. PyPI published its CPython 3.9 stable-ABI Windows x64 wheel on 2026-07-17. Current release activity supports evaluating it, while the repository's request for maintainers remains a maintenance risk.

The CLI uses the same model/runtime stack and adds per-launch model loading. The Python API provides explicit paths, optional speaker metadata, and sentence-chunk iteration with minimal experiment code. Native `libpiper` would add an unverified C/C++ boundary. Direct ONNX Runtime would make this project own Piper phonemization and tensor compatibility. Piper Plus remains a maintained alternative, but its documented custom language coverage is narrower than the existing compatible-voice target.

Selection was based on model compatibility and testability, not a language. It does not select an eventual NVDA process architecture.

## Language-neutral boundary

`experiments/piperRuntime/runtimeAdapter.py` accepts arbitrary Unicode and explicit model/config paths. It contains no locale allowlist, language inference, translation, script detection, preferred-language ordering, language-specific runtime branch, fixed phoneme inventory, speaker-name constant, or automatic model selection. Sample rate, speaker count, speaker IDs, phoneme type, and Piper version are model metadata.

The English validation voice was chosen only as an approved, small, provenance-documented test asset. It is neither a product default nor a preferred voice. Persian has no special implementation path. The future add-on target remains every technically compatible Piper voice selected by the user, subject to compatibility, licensing, and runtime support.

## Runtime prerequisite

The first attempt established that ONNX Runtime could not import while `msvcp140.dll` was absent. The official Microsoft x64 Visual C++ installer was downloaded from `https://aka.ms/vc14/vc_redist.x64.exe`. Authenticode status was `Valid`; the signer was Microsoft Corporation; size was 18,731,856 bytes; SHA-256 was `843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`. Interactive installation exited with code 0.

After installation, `C:\Windows\System32\msvcp140.dll` was 643,512 bytes, Microsoft Corporation version 14.51.36247.0. The read-only installed-products entry reported Microsoft Visual C++ v14 Redistributable (x64) 14.51.36247.0. ONNX Runtime 1.28.0 then imported successfully and advertised `AzureExecutionProvider` and `CPUExecutionProvider`; the adapter explicitly created its session with `CPUExecutionProvider`. Piper 1.5.0 imported offline.

## Test asset and provenance

The two approved files were downloaded on 2026-08-01 from these exact official URLs:

- `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx?download=true`
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx.json?download=true`

The model was 63,201,294 bytes with SHA-256 `f7d01dde371555732c4c314111ac79672b1a5ce2fc19266ab42178fd8df7f375`. The configuration was 4,882 bytes with SHA-256 `45754dfdebb3b8661c3fc564713772deec6e064feeb5b4e9594857dc7305193a`. Metadata reported one speaker, 16,000 Hz, eSpeak phonemization, and Piper model format 1.0.0. The model card identifies `en_US`, low quality, and the Lessac Blizzard 2013 dataset and its separate licence.

The files remain ignored local reproducibility assets. Repository-level MIT metadata does not settle dataset, derived-model, speaker-rights, or future redistribution questions; local experimentation is the only approved classification.

## Environment and method

- OS: Windows 11 build 26200, AMD64.
- CPU: 12th Gen Intel Core i7-1255U, 10 cores / 12 logical processors.
- RAM capacity: not recorded because the available WMI query was denied.
- Python: CPython 3.12.10, 64-bit; pip 26.2.
- Runtime: `piper-tts` 1.5.0, ONNX Runtime 1.28.0, NumPy 2.5.1, pathvalidate 3.3.1, protobuf 7.35.1, flatbuffers 25.12.19, packaging 26.2.
- Provider: CPUExecutionProvider.
- Timer: Python `time.perf_counter`; PowerShell `Measure-Command` for fresh-process measurements.
- Policy: one warm-up per case was discarded, followed by five recorded runs. Min/median/max are reported; no percentile is inferred from five runs.

The benchmark reuses one loaded model for short, medium, long, and multiline Unicode cases. Piper's default inference noise makes exact audio duration and frames vary across runs; the individual structured records preserve those values.

## Startup and cold model load

Fresh-process seconds, five runs each:

| Measurement | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Python interpreter startup | 0.033460 | 0.035660 | 0.053117 |
| ONNX Runtime import, including interpreter | 0.206921 | 0.210911 | 0.245667 |
| Piper import, including interpreter | 0.233414 | 0.237971 | 0.262603 |
| Adapter model load, internal timer | 1.828798 | 1.913707 | 2.071670 |
| Complete cold-load process wall time | 2.141263 | 2.207871 | 2.384933 |

The main benchmark's cold model load was 1.894282 seconds.

The individual fresh-process observations, in run order, were:

- Python startup: 0.053117, 0.033460, 0.035660, 0.034483, 0.035767 seconds.
- ONNX Runtime import: 0.245667, 0.210650, 0.206921, 0.212600, 0.210911 seconds.
- Piper import: 0.261980, 0.236673, 0.262603, 0.233414, 0.237971 seconds.
- Internal model load: 1.832700, 1.828798, 1.913707, 2.071670, 2.039579 seconds.
- Complete cold-load process: 2.141263, 2.142413, 2.207871, 2.384933, 2.352157 seconds.

## Warm synthesis results

Each row summarizes five recorded runs after one discarded warm-up.

| Case | Code points | Chunks | Completion seconds min / median / max | First chunk seconds min / median / max | RTF min / median / max |
|---|---:|---:|---|---|---|
| Short repeated utterance | 23 | 1 | 0.061649 / 0.063099 / 0.068118 | 0.059352 / 0.061323 / 0.066288 | 0.038531 / 0.045870 / 0.047836 |
| Medium punctuation/numbers | 65 | 1 | 0.205691 / 0.222672 / 0.237439 | 0.203181 / 0.220009 / 0.234897 | 0.033478 / 0.035969 / 0.038346 |
| Longer paragraph | 266 | 2 | 0.540915 / 0.564472 / 0.578786 | 0.244847 / 0.260063 / 0.268058 | 0.034710 / 0.035697 / 0.036174 |
| Multiline Unicode | 103 | 2 | 0.269053 / 0.300841 / 0.427774 | 0.167963 / 0.194483 / 0.252897 | 0.036716 / 0.039836 / 0.057006 |

Across those runs, generated audio ranged from 1.344 to 16.000 seconds, 21,504 to 256,000 frames, and 43,008 to 512,000 PCM bytes. All measured RTF values were below 0.058 on this machine. These standalone results do not establish NVDA responsiveness, playback latency, cancellation latency, or suitability thresholds.

### Individual warm-run evidence

Times are seconds; bytes are PCM payload bytes. Runs are listed after discarding each case's single warm-up.

| Case / run | Completion | First output | Audio duration | RTF | Frames | Bytes |
|---|---:|---:|---:|---:|---:|---:|
| Short 1 | 0.062383 | 0.060377 | 1.360 | 0.045870 | 21,760 | 43,520 |
| Short 2 | 0.064341 | 0.062617 | 1.472 | 0.043710 | 23,552 | 47,104 |
| Short 3 | 0.063099 | 0.061323 | 1.344 | 0.046949 | 21,504 | 43,008 |
| Short 4 | 0.061649 | 0.059352 | 1.600 | 0.038531 | 25,600 | 51,200 |
| Short 5 | 0.068118 | 0.066288 | 1.424 | 0.047836 | 22,784 | 45,568 |
| Medium 1 | 0.205691 | 0.203181 | 6.144 | 0.033478 | 98,304 | 196,608 |
| Medium 2 | 0.237439 | 0.234897 | 6.192 | 0.038346 | 99,072 | 198,144 |
| Medium 3 | 0.222672 | 0.220009 | 6.288 | 0.035412 | 100,608 | 201,216 |
| Medium 4 | 0.217538 | 0.215052 | 6.048 | 0.035969 | 96,768 | 193,536 |
| Medium 5 | 0.226677 | 0.224149 | 5.968 | 0.037982 | 95,488 | 190,976 |
| Long 1 | 0.543238 | 0.245534 | 15.488 | 0.035075 | 247,808 | 495,616 |
| Long 2 | 0.540915 | 0.244847 | 15.584 | 0.034710 | 249,344 | 498,688 |
| Long 3 | 0.578786 | 0.268058 | 16.000 | 0.036174 | 256,000 | 512,000 |
| Long 4 | 0.567724 | 0.260063 | 15.904 | 0.035697 | 254,464 | 508,928 |
| Long 5 | 0.564472 | 0.264718 | 15.712 | 0.035926 | 251,392 | 502,784 |
| Unicode 1 | 0.300841 | 0.194483 | 7.552 | 0.039836 | 120,832 | 241,664 |
| Unicode 2 | 0.281878 | 0.179169 | 7.456 | 0.037806 | 119,296 | 238,592 |
| Unicode 3 | 0.269053 | 0.167963 | 7.328 | 0.036716 | 117,248 | 234,496 |
| Unicode 4 | 0.357215 | 0.201897 | 7.488 | 0.047705 | 119,808 | 239,616 |
| Unicode 5 | 0.427774 | 0.252897 | 7.504 | 0.057006 | 120,064 | 240,128 |

## First WAV validation

The standalone adapter synthesized one short, model-appropriate fixture and closed cleanly. The WAV was 81,964 bytes with a standard mono, 16-bit PCM payload: 16,000 Hz, 40,960 frames, 81,920 audio bytes, one chunk, and 2.56 seconds duration. Synthesis completed in 0.147382 seconds; first yielded output was 0.144971 seconds; RTF was 0.057571. This is structural validation, not a subjective voice-quality claim.

## Controlled failures and shutdown

An invalid model path returned `invalidModel`; missing configuration returned `invalidConfig`; empty input returned `emptyText`. Unicode passed unchanged through the adapter. Runtime-dependent synthesis tests passed, and `close()` released the adapter's voice reference. Errors contained no test text or local paths.

## CPU and memory observation

A second identical 20-measurement benchmark was monitored by polling all new Python processes every 50 ms because the Windows virtual-environment launcher creates a child Python process. Approximate peak combined working set was 356,950,016 bytes (340.41 MiB). Last-sampled combined process CPU time was 87.390625 seconds over an approximately 11.2-second wall interval; ONNX Runtime uses multiple CPU threads, so CPU time can exceed wall time. This is a sampled peak and last pre-exit CPU observation, not steady-state memory, per-core utilization, or high-precision profiling. Total installed RAM and post-load steady memory remain unavailable.

## Cancellation findings

`PiperVoice.synthesize` yields one audio chunk per sentence. A two-sentence experiment requested one chunk in 0.167425 seconds (94,720 PCM bytes), then closed the generator; its frame was closed and the later sentence was never requested. This proves only that future iteration can stop at a sentence boundary. The API exposes no cancellation token for the ONNX inference inside an outstanding `next()` call, so active inference is not shown to be interruptible. A future isolated process could be terminated for hard cancellation, but Phase 2H implements no process or production cancellation and measures no cancel-to-silence behavior.

## Limits and remaining evidence

Adapter limits remain provisional: 16,384 input code points, 1 MiB configuration, 1 GiB model, 8–192 kHz sample rates, and 10,000 speakers. Output must be an explicit WAV in an existing directory; overwrite is opt-in.

Phase 2H exit criteria are met, but the runtime ADR remains Proposed. Remaining work includes a locked and hashed transitive dependency set, Microsoft runtime servicing design, licence/source-offer analysis, representative multi-model and multi-speaker testing, malformed real-model testing, longer soak measurements, active-inference cancellation, process isolation, PCM transport, audio playback, and safe disposable-NVDA validation. Those are not authorization to begin Phase 2I.
