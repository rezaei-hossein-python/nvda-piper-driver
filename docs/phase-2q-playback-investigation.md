# Phase 2Q playback investigation

## Scope and baseline

Phase 2Q preserves the accepted Phase 2L baseline at commit
`a15ec5a21e649e2f327e01902e36eaf2f7f32eaf` and Package C SHA-256
`8f20362053c0e60b258573305155a45b4c3dcb7fbb4c2fe991f6306352b88422`.
Uncommitted Phase 2M–2P experiments remain in the working tree and are not
part of this investigation or production packaging.

## Playback sequence

```text
worker frame → runtime bridge validation → BackgroundController._playResult
→ SynthDriver._playResult → format/player selection → 50 ms feed loop
→ WavePlayer.feed → WavePlayer.idle/sync → drain/completion
→ synthIndexReached and synthDoneSpeaking callbacks
```

The worker frame is read and validated off the NVDA UI thread. Controller
generation checks occur before playback and before each chunk. PCM is sliced
into temporary `bytes` chunks by the driver; each `feed()` may block for output
buffer capacity. `idle()` affects completion/drain after all feeds, not the
timestamp of the first feed. Cancellation advances generation, stops the
player, and rejects stale completion.

## Evidence and decision

Source archaeology found no NVDA requirement for a fixed 50 ms chunk size, but
also no measurement proving it causes onset delay. NVDA eSpeak, OneCore, and
SAPI5 use engine-native callback/marker boundaries rather than a universal
fixed chunk. `WavePlayer` is persistent and reusable; ordinary player
recreation was not found. Sample-rate conversion and physical device onset
were not measurable in this environment because no loopback capture adapter
was installed.

The evidence therefore supports **Conclusion D**: the playback path is not
shown to be the dominant source. No production playback change is implemented.
The 50 ms loop, `idle()`, player lifecycle, buffer admission, and resampling
remain bounded hypotheses rather than proven causes.

## Reproducible next measurement

Use the existing development-only cache-hit diagnostic with a synchronized
WASAPI loopback capture and fixed Piper/eSpeak PCM fixtures. Compare one full
feed, current 50 ms feeds, and engine-native boundaries on the same persistent
player, including stop, idle, and queued-audio conditions. Only a measured
first-captured-sample improvement that preserves cancellation would justify one
opt-in playback experiment.
