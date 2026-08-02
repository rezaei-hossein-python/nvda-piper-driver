# NVDA Piper Driver

## Development status

This development-validation package contains a minimal synthesizer-driver module with a controlled test-only availability gate. It is unavailable by default and normal users cannot enable it through add-on settings. Its private pure converter and bounded in-process fake protocol are disconnected from `speak()`. Phase 2G cancellation is only synchronous state modelling with metadata-only fake results; `SynthDriver.cancel()` and NVDA notifications are not implemented. The fake worker is not a process or IPC transport and does not queue or execute jobs. The package includes no Piper runtime, model, synthesis, PCM, audio output, or model installation functionality.

There is no public release. This package is not intended for everyday use and does not indicate acceptance by the NVDA Add-on Store.

## Project purpose

The project intends to provide offline NVDA speech using separately verified Piper-compatible neural voices. Implementation has not progressed beyond packaging and controlled mock discovery, lifecycle, settings, immutable conversion, and in-process protocol validation.

## Installation status

Only install this development package in a controlled NVDA development or portable environment. Installation in a primary NVDA profile has not been validated. Restart NVDA if its add-on manager requests it.

## Privacy

This package has no speech runtime, network access, telemetry, or text logging. Future speech functionality is designed to operate offline and must not collect synthesized text.

## Known limitations

- The driver is excluded from the selectable synthesizer list unless an unsupported, explicit development-test condition is supplied to the NVDA process.
- No speech is produced.
- Converted jobs are not queued, retained, submitted, or executed.
- The mock voice and rate setting do not affect speech.
- No Piper runtime or voice is included.
- There is no model installer or downloader.
- NVDA installation, help-opening, and uninstall behavior still require controlled manual validation.

## Removal

Use NVDA's installed add-on management interface to remove the add-on, then restart NVDA if requested. Because this package contains only metadata, help, and the test-gated driver, it creates no model files or runtime data outside NVDA's add-on directory.

## Licence and source

NVDA Piper Driver is licensed under GPL-2.0-or-later. Source, the full licence text, and issue reporting are available at <https://github.com/rezaei-hossein-python/nvda-piper-driver>.

When reporting an issue, include the package version, NVDA version, Windows version, installation type, exact steps, and any relevant NVDA log excerpt after removing private text and paths.
