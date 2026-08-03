# Piper backend first-audio comparison

Status: Proposed

| Backend | Character first PCM | Word first PCM | Navigation first PCM | Chunk behavior |
|---|---:|---:|---:|---|
| Standard Python Piper, warm | approximately 33–123 ms | approximately 98–255 ms | approximately 83–725 ms | one chunk for short inputs |
| Standard Python Piper, long | 94–109 ms | — | — | 12 sentence chunks; completion 1.1–1.2 s |
| Direct RT encoder/decoder prototype | approximately 75–160 ms | approximately 83–122 ms | approximately 183–242 ms | 1 chunk for short; 3 chunks for navigation/long |

These are worker/PCM timestamps, not physical audible-onset measurements. The RT prototype did not improve short-input first PCM on this machine and incurred additional Python/ORT boundary work. Its only proven advantage is earlier output for long utterances while later decoder work continues.

The production recommendation is therefore to preserve the current backend and prototype incremental delivery from the existing Python generator first. RT migration is not justified by these measurements alone.

The production integration was rejected after portable validation. Although worker timings exposed an early pipe chunk, the user observed slower overall response, no character echo, stopped document reading, and non-immediate navigation. The previous persistent full-request backend remains the accepted Phase 2K implementation.
