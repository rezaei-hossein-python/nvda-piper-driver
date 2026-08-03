# Piper ONNX graph analysis

Status: Proposed

Analysis used the approved `en_US-lessac-low.onnx` and official `en_US-lessac+RT-low` files with ONNX Runtime 1.28.0 and ONNX inspection package 1.18.0. Files remain outside the project package.

| Graph | Bytes | Nodes | Inputs | Outputs |
|---|---:|---:|---|---|
| Standard Lessac | 63,201,294 | 2,755 | `input`, `input_lengths`, `scales` | `output` waveform |
| RT encoder | 28,418,339 | 5,577 | same three tensors | `z` (192 channels), `y_mask` |
| RT decoder | 35,114,884 | 844 | `z`, `y_mask` | `output` waveform |

All graphs use opset 15 and CPU execution loaded successfully. The proven split boundary is the pair of encoder outputs `z` and `y_mask`; the decoder has no text or phoneme inputs. The graphs are not a simple partition of the standard serialized graph: the RT encoder and decoder have different node counts and interfaces, and the standard graph exposes only a final waveform output. Public source does not establish a lossless graph-rewrite recipe.
