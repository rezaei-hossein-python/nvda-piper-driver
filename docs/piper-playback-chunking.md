# Piper playback chunking

The current Piper driver splits each validated PCM result into
`sampleRate // 20 * channels * sampleWidth` bytes, documented in
`addon/synthDrivers/nvdaPiperDriver.py` as a 50 ms bound. `git blame` attributes
that decision to the original persistent-worker commit `fda7471`; it was not
copied from an NVDA driver, and no test requires exactly 50 ms. The stated
rationale is to bound each potentially blocking `WavePlayer.feed()` call while
preserving cancellation checks between chunks.

The decision remains unproven as a latency optimization. A smaller chunk can
increase Python dispatch and feed-call overhead; a larger chunk can reduce
cancellation granularity. No production chunk change is made in Phase 2Q.

Pinned NVDA `nvwave.WavePlayer.feed()` explicitly blocks until buffer space is
available, while returning before playback finishes. Therefore chunk size can
affect throughput and cancellation, but source inspection alone cannot prove
first audible onset.
