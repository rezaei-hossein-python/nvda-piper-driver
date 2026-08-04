# Phase 2P cache-hit audible-onset diagnostic

Phase 2P is diagnostic only. It does not change the accepted Phase 2L
production path, scheduler, cache, worker, or audio settings.

## Probe boundary

`experiments/piperRuntime/cacheHitOnsetDiagnostic.py` is outside the add-on
package and requires `NVDA_PIPER_AUDIO_ONSET_DIAGNOSTIC=1`. It accepts only
fixed signal categories and a bounded trial count. It records monotonic,
content-free stage timestamps and terminal states. It never records speech
text, characters, cache keys, model paths, or user content.

The deterministic synthetic impulse is available without Piper. Cached Piper
and eSpeak fixtures are accepted only from the two named files in the ignored
diagnostic output directory; arbitrary paths and text are rejected.

## Capture status

Physical onset must come from WASAPI loopback, an approved virtual loopback,
electrical capture, or synchronized microphone capture. `WavePlayer.feed()`
and completion callbacks are not audible-onset measurements. On the target
machine no supported capture adapter (`sounddevice`, `pyaudio`, `soundcard`, or
`pycaw`) is installed, so physical onset is currently **unmeasured**. Reports
must use `unknown` for captured-sample and phonetic-energy stages rather than
substituting feed timestamps.

NVDA was running during the initial diagnostic preflight (PID 16192) and was
not terminated. A real full-NVDA run requires the user to close that unrelated
instance first. No production package was modified, and no commit or push is
part of Phase 2P.

## Required comparison

The probe is intended to compare synthetic impulse, cached Piper character,
and eSpeak character signals across direct persistent-player, stop-before-feed,
idle, queued-audio, controller, and full-NVDA paths. The final report must
separate input-to-driver, classification, cache lookup, queue, dispatch,
stop/restart, feed admission, captured onset, phonetic energy, and waveform
duration. Any unavailable stage is explicitly `unknown`.

Until a synchronized capture run is completed, no claim about the dominant
physical audio stage is justified. The next engineering step is to install or
approve one local loopback capture method, close the unrelated NVDA process,
and run the prescribed matrix without changing production behavior.
