# Portable NVDA validation for Phase 2I

## Isolation evidence

The authorized executable is `D:\NVDA\nvda.exe`, version 2026.1.1 AMD64. Startup used an explicit configuration path under `D:\NVDA` and an explicit log path under that same portable configuration. The log reported the local configuration directory, loaded bundled eSpeak NG 1.52.0, initialized NVDA, and recorded a clean exit. The portable distribution also contains the current OneCore driver in `library.zip`.

No command was sent to a running NVDA instance until the previously running primary instance had been closed by the user. No primary NVDA file or configuration was modified.

## Development installation procedure

The development add-on is installed only below the portable configuration's `addons` directory. Runtime activation variables point explicitly to the ignored Phase 2H virtual environment and hash-verified local model/configuration. Neither asset is copied into the portable add-on or `.nvda-addon` archive.

The validation log is written inside the portable configuration and inspected for driver, worker, playback, and shutdown errors. Automatic update checking is disabled in the isolated Phase 2I portable configuration so the offline runtime test does not initiate an update request.

## Manual validation checklist

- Launch the `D:\NVDA` executable with the isolated local configuration.
- Confirm the development-gated NVDA Piper Driver is selectable.
- Send one short fixture appropriate for the configured validation voice.
- Confirm audible mono Piper speech without a retained WAV.
- Switch the portable configuration back to eSpeak.
- Confirm eSpeak remains audible.
- Exit portable NVDA.
- Confirm no NVDA or Phase 2I worker process survives.
- Inspect the portable log for errors and verify it contains no synthesized fixture text.

Results are recorded after the controlled run. Audible confirmation is subjective and limited to the selected model and output device; it does not establish latency, quality, cancellation, or screen-reader suitability.

## Recorded run

Portable NVDA 2026.1.1 loaded `nvdaPiperDriver` from `D:\NVDA\phase2iConfig` with the exact marker and verified explicit Phase 2H paths. A temporary portable-only harness submitted one short fixture and was removed afterward. The one-shot worker was absent after completion. The info-level log contained no error, traceback, watchdog recovery, or fixture text and recorded a clean exit.

The isolated profile was then changed to `espeak`; the next run logged eSpeak NG 1.52.0 as the selected driver, remained responsive, and exited cleanly. No NVDA or Phase 2I Python worker remained. The user confirmed hearing both the Piper fixture and the eSpeak fixture and confirmed that the synthesizer switch worked correctly.

An earlier diagnostic run with NVDA's welcome dialog and debug logging was discarded: the long automatic welcome utterance demonstrated that the synchronous prototype can trigger watchdog freeze recovery, and NVDA's own debug logger recorded its speech sequence. That log was deleted, the welcome dialog was disabled, and final validation used info logging. This is direct evidence that complete synchronous synthesis is not a production architecture.

## Safety boundary

This procedure does not install anything into the primary NVDA, download assets, or modify global runtime configuration. It does not test secure screens. Phase 2J is not started.
