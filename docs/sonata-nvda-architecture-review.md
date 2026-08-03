# Sonata NVDA architecture review

Status: Proposed

Research date: 2026-08-02. Primary sources inspected at commits `635cc2681718f7e6ce941497061af814977f7039` (`sonata-nvda`) and `451f9ebf2bd2aa2ba1be25fcec3b7593eeabf6ee` (`sonata`).

## Driver flow

`addon/synthDrivers/sonata_neural_voices/__init__.py` creates one asyncio loop and gRPC client, discovers installed voices, creates `SonataTextToSpeechSystem`, and keeps a `WavePlayer` per sample rate. `speak()` converts NVDA command sequences into tasks. Navigation uses separate text tasks rather than joining adjacent strings; Say All is the case where adjacent text is joined. `IndexCommand` becomes an `IndexReachedTask`, and completion is a `DoneSpeakingTask` that waits for `WavePlayer.idle()` before calling `synthDoneSpeaking`.

`SpeechTask` iterates the server stream and submits each sample block with `run_in_executor(player.feed, ...)`; it then synchronizes the player. `cancel()` cancels the asyncio task and calls `WavePlayer.stop()` locally. It does not terminate the server. Dropping the gRPC stream causes the server sender to stop when its channel reports failure. This is generation-like stale suppression by task ownership, not an explicit request generation in the protocol.

The driver exposes voice, variant, speaker, rate, rate boost, volume, pitch, and Piper noise settings. `+RT` is selected as a separate installed voice variant. Character-mode handling is delegated to NVDA's speech sequence and then treated as a short text task; no hardcoded character PCM cache was found.

## Comparison and reuse decision

The directly reusable behaviors are long-lived player ownership, immediate local stop, per-segment navigation submission, incremental feed, and completion after playback drain. The gRPC transport itself is not assumed to be faster than this project's bounded pipe. The current project should first adopt these behaviors behind its existing NVDA speech boundary and retain its stronger generation IDs and bounded pending slot.

Source: [sonata-nvda](https://github.com/mush42/sonata-nvda/tree/635cc2681718f7e6ce941497061af814977f7039).
