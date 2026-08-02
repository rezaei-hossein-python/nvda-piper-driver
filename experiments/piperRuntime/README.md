# Standalone Piper runtime experiment

This Phase 2H experiment evaluates `piper-tts` 1.5.0 through its Python API on Windows x64. It is deliberately outside the NVDA add-on, is not imported by the driver, and produces no NVDA audio or notifications. It does not download voices or contact a service. Supply an explicit local `.onnx` model, matching `.onnx.json` configuration, and existing output directory.

The adapter is model-path driven and contains no locale detection, language allowlist, language-specific branch, phoneme inventory, or speaker-name constant. Locale and phonemizer values remain model metadata consumed by Piper. The selected English test voice is only a provenance-checkable validation asset; no language, including Persian or English, receives a special product path.

## Isolated setup

Create an environment outside Git-tracked paths and install the hash-pinned Windows x64 wheel:

```powershell
python -m venv C:\path\to\temporary-phase2h-venv
C:\path\to\temporary-phase2h-venv\Scripts\python.exe -m pip install --only-binary=:all: -r experiments\piperRuntime\requirements.txt
```

`piper-tts` declares `onnxruntime>=1,<2` and `pathvalidate>=3,<4`; a fully reproducible future bundle will need a locked, hashed transitive dependency set. The requirements file pins the directly selected runtime version and records the Windows x64 wheel hash, but does not yet make dependency resolution reproducible.

## Benchmark

Download the chosen test model and configuration manually from the official `rhasspy/piper-voices` repository, verify their recorded SHA-256 hashes, disconnect networking if desired, and run:

```powershell
C:\path\to\temporary-phase2h-venv\Scripts\python.exe experiments\piperRuntime\benchmark.py `
  --model C:\local\voice.onnx `
  --config C:\local\voice.onnx.json `
  --output-directory C:\local\benchmark-output `
  --runs 5 --warmups 1
```

The program writes WAV files and emits compact structured JSON to standard output. It never logs the supplied text. Inputs are bounded to 16,384 Unicode code points; configuration is bounded to 1 MiB and model files to 1 GiB. Existing WAV output is rejected by the adapter unless the benchmark explicitly enables overwrite for its deterministic filenames. Errors expose stable classifications without text or local paths.

Measurements cover in-process model loading, first yielded sentence chunk, completion, WAV duration, and real-time factor. They do not isolate Python interpreter startup, prove active-inference cancellation, include an audio pipeline, or establish screen-reader suitability. Stopping iteration prevents consumption of later chunks but does not prove that an ONNX inference already in progress can be interrupted.

Model and runtime files, generated WAV files, benchmark JSON containing machine details, virtual environments, and downloaded dependencies must remain outside Git and outside the add-on archive.
