# Phase 1B: NVDA neural-speech ecosystem review

## Method and limits

Reviewed 2026-08-01. “Current” means evidence visible on that date; repository activity is not proof of long-term maintenance. Official NVDA behavior is authoritative; third-party projects are implementation evidence only. No substantial source code is reproduced.

## Sonata NVDA (formerly Piper for NVDA)

- **Purpose/status/version evidence:** [mush42/sonata-nvda](https://github.com/mush42/sonata-nvda) describes a GPL-2.0 NVDA neural synthesizer supporting Piper through the author's cross-platform Rust Sonata engine. The repository and releases were accessible; the latest visible release was v3.1.0. Release dates shown without a year by GitHub were not interpreted beyond their ordering. The v3.0 beta notes explicitly added NVDA 2024.1 compatibility. Do not infer compatibility with current NVDA without manifest/store evidence.
- **Architecture/audio/cancellation:** v2.0 release notes say TTS moved to a separate process and responsiveness improved; v3.0 beta says the server became one statically linked executable. Repository paths `addon/synthDrivers/sonata_neural_voices.py` and the Sonata engine/server are relevant implementation evidence. Exact cancellation and audio semantics require a pinned code audit before reuse; release claims are not benchmarks.
- **Voices/settings:** the add-on ships no voices. Its keyboard-operable manager downloads/previews voices or installs local archives; model changes require restart. It exposes speaker/variant and synthesis parameters. The README recommends low/medium or “fast” variants for responsiveness, but this is project guidance rather than measured evidence applicable here.
- **Packaging/localization/licence:** AddonTemplate-style files (`buildVars.py`, `manifest*.ini.tpl`, `sconstruct`, locale/doc directories) and a bundled server executable. Add-on GPL-2.0. Each server dependency and voice remains independently auditable.
- **Strengths:** process isolation, persistent service, integrated voice management, local archives, multi-model direction, and real user releases.
- **Negative evidence:** v3.0 beta warned that installed voices would be lost; v3.0-beta.2/3 told users to kill `sonata-grpc` and remove `installTasks.py` to update. Issues #42/#46 are referenced by the release. These demonstrate migration, locked-file, orphan-process, and accessible recovery risks. Reported model pronunciation quality limitations appear in the README.
- **Lesson:** reuse the isolation concept and generation-based cancellation idea only after independent measurement. Keep models outside replaceable add-on program files, make migrations transactional, close every handle before update, and test upgrade/rollback/removal.

## Sonata compatibility forks

GitHub showed forks, but the searches conducted did not establish a currently maintained compatibility fork with releases, ownership, and supported-NVDA evidence strong enough to profile by name. Therefore no fork is labelled maintained or abandoned. Before implementation, query the upstream fork network and Add-on Store by add-on ID again, record commit/release dates, and distinguish a patch mirror from an independently supported distribution. This unresolved result is preferable to attributing maintenance without evidence.

## Hear2Read NG

- **Purpose/status/version evidence:** the official Add-on Store entry describes a Piper-based synthesizer for eleven Indic languages plus Indian English, Apache-2.0, minimum NVDA 2022.1, with Store publication metadata and SHA-256. The community directory showed Hear2Read NG 2.0.8 stable compatible through NVDA 2026.1 on 2026-08-01 ([directory](https://nvda-addons.org/); [Hear2Read site](https://hear2read.org/)). Those listings establish distribution status, not a security audit.
- **Architecture/voices/packaging:** the Store description and Hear2Read documentation say it includes a voice manager; the NG installer includes Nepali and can install additional languages. The original product used a separate Windows installer/desktop voice manager and required NVDA restart. Exact NG source paths, inference boundary, cancellation, audio, settings, localization catalogue, and binary provenance were not verifiable from an authoritative public repository found in this review.
- **Strengths:** current Store presence, multilingual focus, voice-manager experience, and a real compatibility range.
- **Weaknesses/risks:** incomplete public architectural evidence in the sources found; historical registration/download and separate-installer UX would conflict with this project's no-telemetry/no-silent-network expectations unless redesigned. Apache-2.0 metadata does not by itself establish licences of Piper, eSpeak, ORT, or every model.
- **Lesson:** treat its Store and Indic-language UX as field evidence, but request/locate exact public source and third-party notices before adopting technical patterns. Persian validation must not become language-specific design.

## Other Piper/ONNX NVDA projects

The former `mush42/piper-nvda` is the historical identity of Sonata, not an independent current design. Search results also surfaced experimental/general neural add-ons, but none had sufficiently authoritative evidence of current local Piper/ONNX architecture and maintenance to support a detailed profile. This is an explicit research gap, not proof that no others exist. Repeat the search through the live Store, add-on community directory, GitHub topics, and community list before release.

## Built-in NVDA architectural references

### OneCore

`references/nvda-source/source/synthDrivers/oneCore.py` uses `nvwave.WavePlayer`, queues work, receives synthesis callbacks on a background thread, and reports indexes/completion. `cancel`, `_processQueue`, `_callback`, and `terminate` show explicit queue/audio/resource management. Strength: current core integration and error fallback. Limitation: Windows OneCore APIs and its callback model differ from Piper; code is GPL and cannot simply be transplanted without design/licence review.

### SAPI5

`references/nvda-source/source/synthDrivers/sapi5.py` has a WASAPI speak thread, condition-protected request queue, `WavePlayer`, cancellation, pause, and thread joining. Comments around `_speakThread` explain avoiding audio/main-thread blocking. Strength: detailed lifecycle and synchronization precedent. Limitation: COM/SAPI events and bookmarks do not prove Piper behavior.

### eSpeak

`references/nvda-source/source/synthDrivers/espeak.py` advertises commands/notifications and implements `cancel`, `pause`, callbacks, and termination through the native wrapper. Strength: multilingual voice/settings mapping and tight streaming integration. Limitation: eSpeak is a mature lightweight synthesizer with different latency and model behavior.

### Silence and speech manager

`silence.py` is useful for the minimum driver surface only. `references/nvda-source/source/speech/manager.py` is more important: `_onSynthIndexReached` and `_onSynthDoneSpeaking` marshal work to the main event queue and tolerate unknown indexes after cancellation. A new driver must preserve those semantics rather than copying one driver's private details.

## Experienced-developer practices supported by evidence

- Use current AddonTemplate structure and automated lint/type/build checks ([NV Access AddonTemplate](https://github.com/nvaccess/AddonTemplate), accessed 2026-08-01).
- Package a pip dependency rather than relying on NVDA's copy (`docs/imported/nvda-developer-guide.html`, “Add-on API stability”), while accepting responsibility for its updates.
- Keep native work off the GUI/main thread and marshal GUI operations appropriately (same guide, “A note on threading”; pinned built-in drivers above).
- Implement real cancel, terminate, index, and done behavior (`docs/nvda-synthdriver-research.md`).
- Localize manifest/UI/help with gettext and locale directories (developer guide, “Localizing Add-ons” and “Add-on Documentation”).
- Treat release notes as failure evidence: process lifetime, voice migration, locked binaries, and NVDA/Python transitions need explicit tests.

## 32-bit to 64-bit and compatibility lessons

The target is current 64-bit NVDA. Native CPython extensions, executables, DLLs, and ORT packages must all be x64 and built for the selected runtime. The official AddonTemplate recommends Python 3.13 64-bit as of access; this is build-tool guidance, not permission to assume NVDA's future Python ABI. The pinned tree retaining `sapi*_32.py` compatibility helpers is historical/contextual evidence, not a design target. Do not ship dual architecture until a supported requirement exists.

## Applicable conclusions

Reusable: process isolation, persistent model loading, bounded queued audio, generation/stale-result rejection, separately managed voices, local archive installation, explicit lifecycle, and AddonTemplate localization/build layout.

Do not reuse without proof: claimed speed, thread safety, cancellation granularity, model compatibility, licensing conclusions, server binaries, download indexes, or private NVDA APIs. The ecosystem's clearest negative lesson is that voice storage and worker lifetime are release-engineering concerns, not secondary features.

## Unresolved evidence

- Identify and audit any active Sonata compatibility forks and their exact purpose.
- Locate an authoritative public Hear2Read NG source repository and third-party notices.
- Pin Sonata commits/releases and inspect exact cancellation/audio/protocol code before implementation.
- Recheck the Store for other local neural synthesizers immediately before prototype and release.
