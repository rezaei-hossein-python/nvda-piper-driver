# Audio and notification pipeline

## Evidence and proposed flow

Pinned evidence: `references/nvda-source/source/nvwave.py` (`WavePlayer.feed`, `idle`, `stop`, `pause`, `setVolume`, audio-device error state), built-in `oneCore.py` and `sapi5.py`, and `speech/manager.py` notification handlers. These implementations are evidence, not a stable public guarantee.

NVDA sequence → immutable speech job → worker synthesis request → Piper inference → ordered PCM chunks → bounded NVDA-side buffer → verified player feed → feed/index callbacks → final playback completion → `synthDoneSpeaking`.

## Ownership and provisional format

The worker owns inference and declares model output format. The NVDA process owns playback, cancellation, device selection, index gating, and notifications. Prototype format is signed little-endian 16-bit PCM, mono, at the model's declared sample rate, only if the selected backend produces that without lossy conversion. Do not hardcode a sample rate. Reject inconsistent format within a job; recreate the player at a safe boundary for a new format/model.

## Buffering and backpressure

Chunk duration and prebuffer are benchmark variables, not constants. Use a bounded FIFO measured in bytes/duration. Parent grants capacity or stops reading/requesting; worker must not grow an unbounded output queue. Start playback after the smallest measured prebuffer that avoids underruns on supported hardware. Track produced, received, queued, and played positions separately.

`cancel()` advances generation, clears pending parent chunks/indexes, calls the verified player stop path, and tells the worker to cancel. Normal completion drains; cancellation/error stops and never drains obsolete PCM. Pause pauses playback and bounds inference at the high-water mark; resume preserves offsets.

## Settings

Volume is initially a per-job synthesis/playback setting only if the selected path implements it predictably; avoid double attenuation between Piper and player. Rate is a worker synthesis parameter whose mapping is empirically calibrated and snapshotted. Pitch is not advertised until a verified backend implements it without an unsafe post-processing dependency. Rate boost remains deferred. Setting changes normally affect the next job.

## Device and power lifecycle

Use NVDA's configured output path only after confirming the current API. On device loss: stop, invalidate generation, close player, report a recoverable audio error, and attempt bounded recreation on later speech. Recreate after sleep/resume or format/device changes rather than trusting stale handles. Test default-device switching, unplug/replug, installed/portable NVDA, and termination during callbacks.

## Milestone definitions

- **Synthesis completed:** worker backend will produce no more PCM; playback may remain.
- **Final PCM received:** parent validated the final chunk.
- **Final PCM queued:** all PCM was accepted by the player.
- **Final PCM played:** audio backend confirms/drains the current feed.
- **NVDA done speaking:** driver emits `synthDoneSpeaking` once for the current job.

Provisional trigger for `synthDoneSpeaking` is **final PCM played**, after all deliverable indexes, because `SpeechManager` uses completion to advance speech and OneCore/SAPI5 evidence ties completion to output completion rather than inference alone. `WavePlayer.idle()` must never block NVDA's main thread. Exact callback/drain semantics require a prototype.

## Index alignment

Worker synthesis offsets are advisory. Each index is mapped to a PCM frame offset when backend timing exists; otherwise split synthesis at safe index boundaries and associate the index with the preceding audio feed. Parent emits `synthIndexReached` from a player completion callback only when corresponding audio has played, as OneCore demonstrates conceptually. Never emit from text consumption or PCM generation alone. Coarse boundary splitting may add latency/artifacts and must be compared with timing metadata. Indexes at zero, consecutive indexes, final indexes, cancellation, and silence require experiments.

## Failure rules

Malformed/out-of-order chunks fail the job and restart the worker if protocol integrity is suspect. Player feed failure stops current audio and enters recoverable audio failure. Underrun is measured/logged without text. Duplicate/final-after-cancel events are discarded. Completion never follows failed or cancelled jobs unless NVDA integration evidence explicitly requires a distinct behavior.

## Required experiments

- Compare chunk durations/prebuffer/high-water marks across cold/warm short and long utterances.
- Measure first audible output, underruns, cancel-to-silence, pause/resume, memory, and callback accuracy.
- Compare streaming, complete-buffer, and worker playback.
- Determine `WavePlayer` thread/callback/idle guarantees at the target NVDA commit and current release.
- Validate index placement against recorded reference audio without committing generated audio.
