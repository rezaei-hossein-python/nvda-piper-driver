# Sonata engine review

Status: Proposed

Research date: 2026-08-02. Source commit: `451f9ebf2bd2aa2ba1be25fcec3b7593eeabf6ee`.

## Licensing boundary

The Sonata engine repository is MIT licensed; the NVDA add-on is GPL v2. Sonata's packaged binary also carries separate notices for ONNX Runtime, espeak-ng, and other dependencies. This is compatible in principle with this GPL project, but it does not authorize copying the add-on's bundled executable, voices, or notices piecemeal. A future backend must retain complete attribution and source-obligation review for Piper, ONNX Runtime, eSpeak NG, Sonic, gRPC, and each voice model. No Sonata source or binary is copied by this phase.

The Rust workspace contains `espeak-phonemizer`, `sonata-model`, `sonata-synth`, `sonata-grpc`, `libsonata`, `sonata-python`, and `sonic-sys`. Piper model loading is persistent in the gRPC server's voice map. Standard models use one `model.onnx`; a config with `streaming: true` loads sibling `encoder.onnx` and `decoder.onnx` into `VitsStreamingModel`.

The streaming model runs the encoder once, then a `SpeechStreamer` invokes the decoder over mel chunks with overlap and crossfade. The server currently calls `synthesize_streamed(..., 55, 3)`. A short utterance can still be one complete chunk (`one_shot`); this is model-chunk streaming, not frame streaming. The realtime synthesizer phonemizes before starting a Rayon worker and sends chunks through an unbounded channel.

The gRPC server initializes ONNX Runtime with the CPU provider. Thread, parallel-execution, memory-pattern, and graph-level options are present only as commented experiments in the inspected source; no tuned default was proven. `sonata-synth` applies Sonic rate, volume, and pitch processing to each output block and reads the processed PCM before sending it.

The server has no explicit cancel RPC, generation field, or cancellation token. Client task cancellation closes the response stream; failed sender delivery causes the server loop to return. This is a useful cancellation pattern, but the current project must retain bounded queues and explicit stale-result rejection.

Source: [sonata](https://github.com/mush42/sonata/tree/451f9ebf2bd2aa2ba1be25fcec3b7593eeabf6ee).
