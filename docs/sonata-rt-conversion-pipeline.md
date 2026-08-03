# Sonata RT conversion pipeline

Status: Proposed

Research date: 2026-08-02. The public Sonata repository contains model loading and streaming inference, but no public conversion script, graph-rewrite tool, CI job, or checkpoint exporter that transforms a standard Piper ONNX file. `VitsStreamingModel::from_config` only consumes already-produced sibling `encoder.onnx` and `decoder.onnx` files. The RT dataset publishes prebuilt archives such as `en_US-lessac+RT-low.tar.gz`.

Classification: **not reproducible from a standard Piper ONNX model using public Sonata source**. The available evidence is consistent with an upstream/export-time transformation or additional private training/export tooling. An ONNX file alone is not enough to prove that conversion can be reproduced.

The official RT archive was downloaded from the `mush42/piper-rt` dataset into the external study directory. It contains `encoder.onnx`, `decoder.onnx`, and a `streaming: true` config. No project asset was changed or packaged.
