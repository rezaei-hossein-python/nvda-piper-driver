# Phase 2R WASAPI loopback capture

## Capture method

The ignored `.phase2r-capture` environment contains PyAudioWPatch 0.2.12.8,
installed from its Windows AMD64 wheel. The project is
`https://github.com/s0d3s/PyAudioWPatch`, licensed Apache-2.0, and provides
PortAudio WASAPI loopback devices. It is not a production dependency and is
not included in the add-on.

The target enumerated:

- output: `Speakers (Realtek(R) Audio)`;
- loopback: `Speakers (Realtek(R) Audio) [Loopback]`;
- format: 48,000 Hz, stereo, signed 16-bit;
- capture uncertainty: one 480-frame block, approximately 10 ms.

## Standalone verification

A deterministic 20 ms marker tone was played through the default output while
the loopback stream captured in memory. Five smoke trials detected the marker.
The required 100-trial run completed with zero failures:

| Statistic | Marker delay |
| --- | ---: |
| Minimum | 94.06 ms |
| Median | 111.17 ms |
| Maximum | 123.17 ms |
| p95 | 115.17 ms |
| Standard deviation | 3.75 ms |

These are output-marker capture timings, not Piper or NVDA timings. The
detector uses a pre-marker baseline and requires sustained energy above it, so
ambient desktop audio does not count as the marker. No capture file is saved.

## Fixed fixtures and direct-output proxy

The approved local Piper runtime generated an ignored fixture at 16 kHz mono:
8,704 frames, 544 ms, SHA-256
`4178ebc9d204afb884f000b60cb06215c81353bc1061dccf2702824b2840a950`.
Its first threshold energy occurs at approximately 65 ms. The pinned NVDA
`espeak.dll` synchronous callback generated an ignored 22.05 kHz mono fixture:
5,358 frames, 243 ms, SHA-256
`d11f4b45bc293d0733811b970e18797e4ad64ce8fa20d8946c81aca50808b10b`.
Its first threshold energy occurs at approximately 1.6 ms.

Concurrent PyAudio output proxies, after conversion to 48 kHz stereo, measured
synthetic median 110.67 ms, Piper median 172.22 ms, and eSpeak median 107.60
ms. These are not NVDA `WavePlayer` measurements, but the approximately 61.55
ms Piper increment is consistent with the Piper waveform's delayed first
energy.

## Current limitation

The capture path and fixed fixtures are now verified, but the real NVDA
`WavePlayer`, accepted controller cache-hit path, and portable-NVDA matrix have
not yet been run. Therefore those stages remain `unknown`, and no production
bottleneck or optimization is claimed. The leading measurable hypothesis is
the Piper waveform envelope, pending confirmation through `WavePlayer`.
