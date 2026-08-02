# NVDA Piper Driver

## Development status

This development-validation package contains a synthesizer driver behind the exact Phase 2C marker plus explicit runtime, model, and configuration paths. It is unavailable by default and normal users cannot enable it through add-on settings. Phase 2J uses one bounded background controller and one persistent child process so model loading, synthesis, PCM feeding, and playback drain do not run on NVDA's main thread. It has one active request and one replaceable pending slot, framed segment/index delivery, isolated character-mode segments, no general queue, frame-level streaming, model discovery, or language-selection logic. The package includes no Piper runtime, ONNX Runtime, model, WAV, or model installer.

There is no public release. This package is not intended for everyday use and does not indicate acceptance by the NVDA Add-on Store.

## Project purpose

The project intends to provide offline NVDA speech using separately verified Piper-compatible neural voices. Implementation has not progressed beyond packaging and controlled mock discovery, lifecycle, settings, immutable conversion, and in-process protocol validation.

## Installation status

Only install this development package in a controlled NVDA development or portable environment. Installation in a primary NVDA profile has not been validated. Restart NVDA if its add-on manager requests it.

## Privacy

This package performs no network access, telemetry, WAV retention, or text logging. Speech text and PCM exist only while the current bounded background request needs them and are released afterward.

## Known limitations

- The driver is excluded from the selectable synthesizer list unless an unsupported, explicit development-test condition is supplied to the NVDA process.
- The persistent child normally loads the configured model once per driver session; segment synthesis remains bounded and sentence/segment-granular rather than frame-streaming.
- At most one active and one replaceable pending job exist; jobs are not persistently retained.
- The rate setting is not yet mapped to Piper synthesis.
- No Piper runtime or voice is included.
- There is no model installer or downloader.
- Controlled Phase 2J sequences preserve NVDA's mandatory index metadata as audio boundaries and queue real `synthIndexReached` callbacks after segment playback. Character-mode text is isolated and sent to the explicitly selected Piper model; language metadata remains tolerated without model switching. Portable typed-echo, Read All, replacement, and cancellation measurements remain required. Other unsupported commands are rejected locally with bounded content-free warnings and no event traceback.
- Pinned NVDA source shows that Read All advances through callback-backed index notifications. The bounded controller now implements those callbacks without fabricated timing; see the project documentation for the eSpeak baseline, index design, persistent worker, and interactive-performance evidence.

## Removal

Use NVDA's installed add-on management interface to remove the add-on, then restart NVDA if requested. Because this package contains only metadata, help, and the test-gated driver, it creates no model files or runtime data outside NVDA's add-on directory.

## Licence and source

NVDA Piper Driver is licensed under GPL-2.0-or-later. Source, the full licence text, and issue reporting are available at <https://github.com/rezaei-hossein-python/nvda-piper-driver>.

When reporting an issue, include the package version, NVDA version, Windows version, installation type, exact steps, and any relevant NVDA log excerpt after removing private text and paths.
