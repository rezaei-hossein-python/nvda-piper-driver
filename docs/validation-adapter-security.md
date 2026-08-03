# Validation adapter security

The adapter is copied only into a config marked with `.phase2l-harness-owned.json`. It requires `NVDA_PIPER_VALIDATION_ADAPTER=1`, a fresh run ID, a fresh random token, and a port-file path. Every request contains the run ID, token, unique integer ID, and an exact command-specific field set. Frames are limited to 4 KiB; one client and bounded command IDs are intended by the protocol; fixture names and synth names are allowlisted.

The adapter never accepts Python, shell, module, path, speech-text, or arbitrary method payloads. It binds only to `127.0.0.1`; tokens are not logged or reported; secure/non-owned configurations fail initialization. The harness refuses unrelated running NVDA processes and only cleans PIDs it launched.

The official NVDA SystemTestSpy source was inspected. Its production test lifecycle uses `speechSpyGlobalPlugin.py`, `speechSpySynthDriver.py`, `NvdaLib.py`, `KeyboardInputGesture.fromName`, `inputCore.manager.emulateGesture`, `queueHandler`, and Robot Remote Server. These mappings are documented in the source map. The project adapter is not a replacement for the full Robot/SystemTestSpy stack and must not claim UI scenario success until a verified fixture bridge is installed.
