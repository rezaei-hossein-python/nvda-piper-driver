# Latency investigation summary

## Accepted baseline

Phase 2L remains the production baseline at commit
`a15ec5a21e649e2f327e01902e36eaf2f7f32eaf`. The accepted Package C SHA-256 is
`8f20362053c0e60b258573305155a45b4c3dcb7fbb4c2fe991f6306352b88422`.

## Rejected directions

The following experiments were not accepted as production replacements:

- character-specific `length_scale=0.7`;
- held-key queue and aggregation changes;
- Sonic acceleration as a solution to repetition;
- continuous held-key feedback candidates;
- generic chunk streaming;
- unproven programming-language rewrites.

Their research documents may remain, but their production code and candidate
manifest identities do not.

## Measured findings

Direct matched PyAudio/WASAPI-loopback proxies on the tested Realtek path
measured a common synthetic median around 111 ms. The fixed Piper fixture was
544 ms with first sustained energy around 65 ms. The fixed eSpeak fixture was
243 ms with first sustained energy around 1.6 ms. Concurrent direct-output
proxies measured Piper around 172.22 ms median, synthetic around 110.67 ms,
and eSpeak around 107.60 ms. The approximately 61.55 ms Piper increment closely
matches the Piper waveform-energy delay.

These are proxy measurements, not real NVDA `WavePlayer` or full portable-NVDA
measurements. The full controller and portable matrix remains unknown.

## Remaining hypothesis

Cached Piper character waveform onset/envelope is the strongest measured
incremental latency source. Phase 2S onset shaping remains analysis-only and
unaccepted; no production package exists for it and portable listening has not
occurred.
