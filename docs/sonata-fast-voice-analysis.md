# Sonata fast and RT voice analysis

Status: Proposed

The inspected source and release history distinguish a fast/RT voice from a runtime switch. The NVDA voice manager downloads a separate `+RT` archive from the `mush42/piper-rt` dataset. The add-on README describes the fast variant as more responsive with a small quality trade-off. The engine recognizes it through model metadata (`streaming: true`) and separate `encoder.onnx`/`decoder.onnx` files.

Proven: RT uses an encoder/decoder model split and model-chunk output. Proven only for the inspected voice tooling: it is not a conversion performed automatically for every standard Piper model. The source does not establish quantization, FP16/FP8/INT8 calibration, pruning, cached phoneme PCM, or encoder-output reuse across independent utterances. No official evidence was found that rate boosting reduces first inference latency; Sonic changes output duration and prosody after blocks are generated.

Therefore the approved Lessac standard model is unchanged. A fast/RT benchmark requires an official RT voice archive and a disposable environment; downloading or packaging one is outside the current project's approved model asset boundary.

Relevant evidence includes commit `334768af32876c0387d4311a1406021d2889a566` (RT support and navigation de-combination) and commit `9465fcea350b5e880d0e97c3dd11fa736a01c830` (fast variants and streaming synthesis).
