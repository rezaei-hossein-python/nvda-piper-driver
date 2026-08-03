# Piper RT model experiment

Status: Proposed

Official source: `https://huggingface.co/datasets/mush42/piper-rt/resolve/main/en_US-lessac%2BRT-low.tar.gz`. Archive SHA-256: `A5E076B570944A418FD5700AB2C26971FB47D44FC21BA71DBB2F3BFBFBAC7032`.

Extracted hashes:

- `encoder.onnx`: `68411193EA0AE8284C7DA1F5FCC0C877AAC63F2C8CC3F1094FFB9D188D21A133`
- `decoder.onnx`: `2AC8438D90092EA475431C605EE0750DDB494002522A123907D19DE16457DA30`
- config: `2B25C5AB6C02D5838FC8A49B40A57AF4C649A6B33F96F3F8387C8B94BC878F04`

The config identifies `en_US-lessac+RT-low`, 16 kHz mono output, one speaker, Piper 1.0.0 metadata, and `streaming: true`. Both sessions load with CPU ONNX Runtime and produce nonempty PCM. No conversion was attempted because public Sonata supplies no converter and overwriting or altering the approved standard model is prohibited.
