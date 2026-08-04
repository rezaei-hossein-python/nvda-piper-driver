# Phase 2S character waveform onset optimization

Phase 2S is a development-only analysis. It does not modify the accepted
Phase 2L cache, scheduler, worker, playback path, or ordinary speech.

The implementation is `experiments/piperRuntime/characterOnsetOptimizer.py`
and requires `NVDA_PIPER_EXPERIMENTAL_CHARACTER_ONSET=1` in a development
harness. It accepts only validated signed 16-bit PCM and character-scoped
policies. The cache identity helper includes the onset policy so variants
cannot collide.

## Detection and safety

Onset is detected from a language-independent RMS envelope. The threshold is
derived from measured baseline energy and peak energy; a sustained run is
required before an onset is accepted. Trimming aligns the cut near the nearest
zero crossing, retains bounded pre-roll, applies a short fade-in, preserves
sample alignment, and falls back to the original bytes when uncertain.

Policies are `current`, `preserve40ms`, `preserve25ms`, `preserve15ms`, and
`adaptive`. The current policy is byte-identical. No time compression, pitch
change, resynthesis, or word/document processing is performed.

## Lessac fixture measurement

The ignored fixed Piper fixture is 16 kHz mono, 8,704 frames, 544 ms, with
first sustained energy at approximately 65 ms. Development-only analysis
produced these reductions:

| Policy | Output frames | Onset shift | Fallback |
| --- | ---: | ---: | --- |
| Current | 8,704 | 0 ms | yes |
| Preserve 40 ms | 8,303 | 25.06 ms | no |
| Preserve 25 ms | 8,063 | 40.06 ms | no |
| Preserve 15 ms | 7,903 | 50.06 ms | no |
| Adaptive | 8,011 | 43.31 ms | no |

The fixture itself reports peak full-scale samples, so clipping risk is
recorded for listening review. No portable listening validation has occurred;
no candidate is accepted or integrated into production.

## Next gate

Generate original and adaptive comparison fixtures, run the existing loopback
capture and real portable validation, and reject any policy with clipped
consonants, clicks, harsh attacks, or reduced intelligibility. Until that
portable gate passes, Phase 2L remains the only accepted behavior.
