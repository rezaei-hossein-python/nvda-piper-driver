# NVDA Piper Driver

## Development status

This development-validation package contains a minimal unavailable synthesizer-driver module. Its availability check intentionally returns false, so `NVDA Piper Driver` is not selectable. It does not include a Piper runtime, voice model, speech output, settings, or model installation functionality.

There is no public release. This package is not intended for everyday use and does not indicate acceptance by the NVDA Add-on Store.

## Project purpose

The project intends to provide offline NVDA speech using separately verified Piper-compatible neural voices. Implementation has not progressed beyond packaging and the deliberately unavailable driver boundary.

## Installation status

Only install this development package in a controlled NVDA development or portable environment. Installation in a primary NVDA profile has not been validated. Restart NVDA if its add-on manager requests it.

## Privacy

This package has no runtime code, network access, telemetry, or text logging. Future speech functionality is designed to operate offline and must not collect synthesized text.

## Known limitations

- The driver module can be discovered by NVDA's loader but is excluded from the selectable synthesizer list.
- No speech is produced.
- No Piper runtime or voice is included.
- There is no model installer or downloader.
- NVDA installation, help-opening, and uninstall behavior still require controlled manual validation.

## Removal

Use NVDA's installed add-on management interface to remove the add-on, then restart NVDA if requested. Because this package contains only metadata, help, and the unavailable driver, it creates no model files or runtime data outside NVDA's add-on directory.

## Licence and source

NVDA Piper Driver is licensed under GPL-2.0-or-later. Source, the full licence text, and issue reporting are available at <https://github.com/rezaei-hossein-python/nvda-piper-driver>.

When reporting an issue, include the package version, NVDA version, Windows version, installation type, exact steps, and any relevant NVDA log excerpt after removing private text and paths.
