# Production Piper chunk streaming (rejected)

Status: Rejected in current form after portable NVDA regression testing

Portable NVDA validation showed this production integration was slower overall, lost typed-character echo, stopped document reading, and made navigation non-immediate. The preceding persistent warm full-request backend was materially better. This document records the failed experiment and is not a production design.

The rejected experiment temporarily changed the persistent worker to forward each real Piper generator yield as a bounded `pcmChunk` frame. The controller accepted only the current generation and monotonically increasing chunk sequence, and fed each chunk through the existing long-lived `WavePlayer`. `idle()` ran once per completed segment. Those production changes have been reverted; the current backend again sends one complete PCM response per request.

The experiment used a local length-prefixed pipe with `streamStarted`, `pcmChunk`, `streamComplete`, and `streamFailed` frames. Chunk metadata contained only request/generation/job/segment identifiers, sequence, PCM format, frame/byte counts, and PCM bytes. These frames are no longer part of the packaged production protocol.

The experiment sent a content-free `cancel` frame to the warm worker. Portable validation showed that this production integration was not acceptable, so the current backend uses the previously verified generation invalidation and full-request cancellation path.

Short requests remain one-chunk operations and therefore should not claim a streaming latency gain. Multi-chunk requests can feed the first sentence chunk before later inference completes. Index callbacks remain after the completed segment's final playback drain, and completion remains after the final segment drain.
