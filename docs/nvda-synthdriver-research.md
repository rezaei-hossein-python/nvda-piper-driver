# Phase 1A: current NVDA `SynthDriver` interface

## Scope and evidence rules

This note describes only the pinned NVDA source in `references/nvda-source`. “Required” below means either enforced by Python (for example, an abstract method) or stated as a minimum/“must” in the pinned source. “Optional” means a base implementation exists or support is advertised conditionally. Built-in-driver behavior is an implementation example, not automatically a contract.

## 1. Base class

`references/nvda-source/source/synthDriverHandler.py`, symbol `SynthDriver`, is the abstract synthesizer base class. It inherits `references/nvda-source/source/driverHandler.py`, symbol `Driver`, which in turn inherits `AutoSettings`. A synthesizer module is expected to expose a class named `SynthDriver` derived from this base (`synthDriverHandler.SynthDriver` class documentation).

Related value objects are `synthDriverHandler.LanguageInfo` and `synthDriverHandler.VoiceInfo`. `VoiceInfo(id, displayName, language=None)` stores a stable ID, display name, and optional language ID.

## 2. Required methods and properties

### Enforced by the class definition

- `synthDriverHandler.SynthDriver.speak(speechSequence)` is decorated with `@abstractmethod`; it must accept a list containing strings and `SynthCommand` objects and must be implemented.

### Stated driver requirements

- Set class attributes `name` and `description`, and override class method `check`; this is stated by `synthDriverHandler.SynthDriver` and inherited `driverHandler.Driver`. `name` must be the original module filename.
- Support `speech.commands.IndexCommand` in `supportedCommands`; `synthDriverHandler.SynthDriver` says this is the minimum command support.
- Advertise and provide both `synthDriverHandler.synthIndexReached` and `synthDriverHandler.synthDoneSpeaking` in `supportedNotifications`; the base-class documentation says both must be supported.
- Override `cancel` and `pause` “as appropriate” (`synthDriverHandler.SynthDriver`). The base methods are no-ops, so a driver that produces audio needs real implementations to meet their documented semantics.
- Any advertised setting needs an attribute with the same ID, normally backed by `_get_<id>` / `_set_<id>` auto-properties (`synthDriverHandler.SynthDriver`; `driverHandler.Driver`). Thus an advertised `voice` setting requires usable `voice` access and voice enumeration; advertised numeric settings require usable getters/setters.
- Cleanup belongs in `terminate`; inherited `driverHandler.Driver.terminate` saves settings and unregisters its configuration-save action. A driver with runtime/audio resources must override it for cleanup and should retain the inherited bookkeeping, as illustrated by `synthDrivers.oneCore.OneCoreSynthDriver.terminate` calling `super().terminate()`.

## 3. Optional methods and properties

These are optional unless the corresponding feature is advertised:

- `voice`, `availableVoices`, `language`, and `availableLanguages`: `synthDriverHandler.SynthDriver._get_language` derives language from the current `VoiceInfo`; `_get_availableLanguages` derives a set from voices. `_get_voice` and `_getAvailableVoices` raise `NotImplementedError` in the base, while `_set_voice` is a no-op.
- `language`: `_set_language` raises `NotImplementedError`. `languageIsSupported(lang)` normalizes locale names and accepts either an exact locale or matching root language; `None` is accepted (`synthDriverHandler.SynthDriver.languageIsSupported`).
- `rate`, `pitch`, and `volume`: documented as integer percentages from 0 through 100. Base getters return `0`; base setters do nothing (`synthDriverHandler.SynthDriver._get_rate`, `_set_rate`, `_get_pitch`, `_set_pitch`, `_get_volume`, `_set_volume`).
- `variant` and `availableVariants`: enumeration/getter methods raise `NotImplementedError`; the setter is a no-op (`synthDriverHandler.SynthDriver._get_variant`, `_getAvailableVariants`, `_set_variant`).
- `inflection`: base getter returns `0`, setter is a no-op (`synthDriverHandler.SynthDriver._get_inflection`, `_set_inflection`).
- `rateBoost`, `useWasapi`, and `punctuationSilence` have setting factories but no base behavior in this class (`SynthDriver.RateBoostSetting`, `UseWasapiSetting`, `PunctuationSilenceSetting`).
- `pause(switch)` has a no-op base implementation; `True` means pause and `False` resume (`synthDriverHandler.SynthDriver.pause`).
- `languageIsSupported`, `initSettings`, and `loadSettings` have reusable base implementations.

## 4. Driver class attributes

- `name: str` and `description: str` identify and label the driver (`synthDriverHandler.SynthDriver.name`, `.description`).
- `supportedSettings` is inherited through the settings framework and contains `DriverSetting` objects. Common factories are `LanguageSetting`, `VoiceSetting`, `VariantSetting`, `RateSetting`, `RateBoostSetting`, `VolumeSetting`, `PitchSetting`, `InflectionSetting`, `UseWasapiSetting`, and `PunctuationSilenceSetting` (`synthDriverHandler.SynthDriver`).
- `supportedCommands` is a set/frozenset of `SynthCommand` classes; its base value is empty (`synthDriverHandler.SynthDriver.supportedCommands`).
- `supportedNotifications` is a set/frozenset of extension-point `Action` objects; its base value is empty (`synthDriverHandler.SynthDriver.supportedNotifications`).
- `_configSection = "speech"` selects the configuration section (`synthDriverHandler.SynthDriver._configSection`).
- `_availableVoices` and `_availableVariants` may be cached by the base auto-property getters (`SynthDriver._get_availableVoices`, `_get_availableVariants`).

## 5. Lifecycle

1. **Availability:** `synthDriverHandler.getSynthList` discovers modules under `synthDrivers`, ignores names beginning with `_`, imports `synthDrivers.<name>.SynthDriver`, and includes it only when `check()` returns true. Import/check failures are logged and excluded. Silence is placed last.
2. **Initialization:** `synthDriverHandler.getSynthInstance` instantiates the class, optionally validates OneCore’s default voice, then calls `initSettings`. `driverHandler.Driver.__init__` says construction may set defaults, may raise on error, and must leave the driver usable.
3. **Settings initialization:** `synthDriverHandler.SynthDriver.initSettings` creates/updates config metadata, ensures advertised setting attributes exist, performs `changeVoice`, and saves defaults or loads existing settings. `changeVoice` updates the settings ring and loads the voice dictionary.
4. **Selection:** `synthDriverHandler.setSynth` cancels and terminates the current driver before constructing the replacement. Success updates configuration (unless fallback) and emits `synthChanged`; construction failure is logged and triggers fallback logic. The default priority is OneCore, eSpeak, then silence (`defaultSynthPriorityList`, `findAndSetNextSynth`).
5. **Startup/shutdown:** `references/nvda-source/source/speech/__init__.py`, symbols `initialize` and `terminate`, call `synthDriverHandler.initialize`/`setSynth(configuredName)` at startup and `setSynth(None)` at shutdown. `setSynth(None)` calls current `cancel`, then `terminate`, then clears the current synth.
6. **Termination:** inherited `driverHandler.Driver.terminate` saves settings and unregisters configuration callbacks. Resource-owning drivers add cleanup; see `oneCore.OneCoreSynthDriver.terminate`, `sapi5.SynthDriver.terminate`, and `espeak.SynthDriver.terminate`.

## 6. `speak` contract and sequence items

The direct contract is `synthDriverHandler.SynthDriver.speak`: speak a list of strings and `speech.commands.SynthCommand` instances. `references/nvda-source/source/speech/types.py`, symbols `SequenceItemT` and `SpeechSequence`, type the wider speech pipeline as `list[str | SpeechCommand]`, but `speech.commands.SpeechCommand` explicitly says drivers receive only subclasses of `SynthCommand`.

Driver-facing command classes defined in `references/nvda-source/source/speech/commands.py` are:

- `IndexCommand(index: int)`: mark progress; its constructor rejects non-integer indexes.
- `CharacterModeCommand(state: bool)`: character/spelling mode; rejects non-boolean state.
- `LangChangeCommand(lang: str | None)`: change language, with `None` meaning the NVDA locale.
- `BreakCommand(time: int = 0)`: pause duration in milliseconds.
- `PitchCommand`, `VolumeCommand`, and `RateCommand`: `BaseProsodyCommand` subclasses using either an offset or multiplier; neither means return to the configured default. Supplying both a non-default offset and multiplier raises `ValueError`.
- `PhonemeCommand(ipa, text=None)`: Unicode IPA with optional fallback text.

`EndUtteranceCommand`, `SuppressUnicodeNormalizationCommand`, callback commands, and configuration-profile commands derive from `SpeechCommand`, not `SynthCommand`, and are therefore documented as pipeline-managed rather than driver-facing (`speech.commands.SpeechCommand`, `BaseCallbackCommand`). The speech manager converts callbacks to indexes and sends the built utterance through `speech.manager.SpeechManager._pushNextSpeech`, after firing `synthDriverHandler.pre_synthSpeak`.

A driver should only claim command classes it actually interprets. Built-ins log unknown/unsupported items rather than defining a universal error contract (`synthDrivers.espeak.SynthDriver.speak`; `synthDrivers.sapi5.SynthDriver.speak`).

## 7. Cancellation and pause

- `synthDriverHandler.SynthDriver.cancel` means “Silence speech immediately.” `speech.manager.SpeechManager` calls it on priority interruption and on explicit cancellation, then resets/updates its own index state (`SpeechManager.speak`, `SpeechManager.cancel`).
- The manager deliberately avoids quick index reuse because stale indexes can arrive after cancellation (`speech.manager.SpeechManager._generateIndexes`). It rejects notifications from a non-current synth and treats unknown indexes as probably belonging to cancelled speech (`_onSynthIndexReached`, `_removeCompletedFromQueue`). This is evidence that drivers may have asynchronous, stale results; drivers should suppress them when possible.
- `synthDriverHandler.SynthDriver.pause(True)` pauses and `pause(False)` resumes. `speech.speech.pauseSpeech` calls the driver then emits `speech.extensions.post_speechPaused`; pause does not reset the manager queue.
- Examples: eSpeak delegates to `_espeak.stop`/`_espeak.pause`; OneCore sets a cancellation flag, drops queued text, stops its player, and pauses the player; SAPI5 stops playback, clears queued requests, purges SAPI speech, and pauses its audio interfaces (`synthDrivers.espeak.SynthDriver.cancel/pause`; `oneCore.OneCoreSynthDriver.cancel/pause`; `sapi5.SynthDriver.cancel/pause`).

## 8. Settings interfaces

Settings are declared with `supportedSettings`; each setting ID maps to an attribute of the same name (`synthDriverHandler.SynthDriver`). `initSettings` supplies `defaultVal` only when an advertised attribute is absent. `loadSettings` treats voice specially via `synthDriverHandler.changeVoice`, repairs invalid configured voices by restoring the current voice, then applies other configured attributes.

- **Voice:** advertise `VoiceSetting`; return an `OrderedDict[str, VoiceInfo]` from `_getAvailableVoices`, expose current `voice`, and validate changes. `VoiceInfo.language` may be `None`.
- **Rate, pitch, volume, inflection:** public values are documented as 0–100 percentages. Factories return numeric settings and accept optional minimum steps; volume uses a normal step of 5.
- **Variant/language:** factories provide settings-ring labels. Available variants use `VoiceInfo`; available languages are derived from voices unless overridden.
- **Other toggles:** `RateBoostSetting` is settings-ring enabled. `UseWasapiSetting` and `PunctuationSilenceSetting` default to true and are not in the settings ring.
- Supporting `PitchSetting` does not imply support for in-sequence `PitchCommand`; the latter must be listed separately for capital-pitch behavior (`synthDriverHandler.SynthDriver` class documentation).

## 9. Index and completion notifications

The global actions are `synthDriverHandler.synthIndexReached` and `synthDriverHandler.synthDoneSpeaking`. Drivers emit:

- `synthIndexReached.notify(synth=self, index=<int>)` when audio reaches an `IndexCommand` marker.
- `synthDoneSpeaking.notify(synth=self)` when speech output finishes.

`speech.manager.SpeechManager.__init__` registers handlers for both. `_onSynthIndexReached` and `_onSynthDoneSpeaking` ignore non-current drivers and queue actual handling on `queueHandler.eventQueue`, explicitly to run on the main thread. Indexes drive callback execution and queue advancement; completion can push waiting speech (`SpeechManager._handleIndex`, `_handleDoneSpeaking`). The manager’s generated index range is 1–9999 (`SpeechManager.MAX_INDEX`, `_generateIndexes`).

eSpeak maps a native non-`None` marker callback to index notification and `None` to completion (`synthDrivers.espeak.SynthDriver._onIndexReached`). OneCore attaches index notifications to audio-player `onDone` callbacks and announces completion after the player drains (`oneCore.OneCoreSynthDriver._callback`, `_processQueue`). SAPI5 maps bookmarks and end-stream handling to the two actions (`sapi5.SapiSink.Bookmark`, `SynthDriver._onEndStream`).

## 10. Explicit threading/main-thread expectations

- `speech.commands.BaseCallbackCommand.run` and `CallbackCommand` state callbacks execute on NVDA’s main thread and must return quickly.
- `speech.manager.SpeechManager._onSynthIndexReached` and `_onSynthDoneSpeaking` explicitly marshal notification handling onto `queueHandler.eventQueue` for the main thread. Therefore the built-ins demonstrate that a driver may emit the notification from another thread.
- OneCore says its native completion callback, `oneCore.OneCoreSynthDriver._callback`, is invoked on a background thread; it feeds audio and continues its speech queue there.
- SAPI5’s WASAPI mode creates `Sapi5SpeakThread`; `_speakThread` owns queued synthesis and draining specifically to avoid blocking the audio thread or main thread. `_stopThread` stops the player, signals the condition, and joins the worker.
- No inspected base-interface symbol explicitly states that `SynthDriver.speak`, `cancel`, `pause`, constructor, setting accessors, or `terminate` are always called on the main thread. That must not be assumed from this source alone.

## 11. Exceptions and failure behavior

- `driverHandler.Driver.__init__` may raise any `Exception`; `synthDriverHandler.setSynth` catches construction/settings failures, logs them, and attempts previous/default-driver fallback.
- `synthDriverHandler.getSynthList` catches module import and `check` errors, logs them, and excludes the driver.
- Base unimplemented feature methods raise `NotImplementedError` as listed above. Invalid speech-command arguments can raise `ValueError` (`IndexCommand`, `CharacterModeCommand`, `BaseProsodyCommand`).
- `SynthDriver.loadSettings` catches failure while applying a configured voice, logs “Invalid voice,” rewrites configuration to the current voice, and retries `changeVoice`.
- Built-in voice setters use `LookupError` for an unknown voice (`oneCore.OneCoreSynthDriver._set_voice`; SAPI5 conversion helpers also use `LookupError`). OneCore defines `oneCore.VoiceUnsupportedError(RuntimeError)` for absence of suitable voices.
- OneCore logs synthesis failure, continues queue processing, and after five consecutive failures queues `findAndSetNextSynth` (`OneCoreSynthDriver._handleSpeechFailure`, `MAX_CONSECUTIVE_SPEECH_FAILURES`). SAPI5’s worker logs synthesis exceptions; its legacy path re-raises (`sapi5.SynthDriver._speakThread`, `speak`). No single driver-specific exception type is mandated by the base source.

## 12. Built-in differences

| Driver | Settings | Commands/notifications | Execution, cancellation, cleanup |
|---|---|---|---|
| eSpeak | Voice, variant, rate, rate boost, pitch, inflection, volume (`synthDrivers.espeak.SynthDriver.supportedSettings`) | All eight listed driver-facing command types; both notifications (`supportedCommands`, `supportedNotifications`) | Builds eSpeak markup synchronously and submits it; native callbacks notify progress/completion. Cancel/pause delegate to eSpeak; terminate calls `_espeak.terminate` (`speak`, `_onIndexReached`, `cancel`, `pause`, `terminate`). |
| OneCore | Dynamic: voice/rate; optionally rate boost; pitch/volume; optionally punctuation silence (`oneCore.OneCoreSynthDriver._get_supportedSettings`) | Same eight commands and both notifications (`supportedCommands`, `supportedNotifications`) | Converts to SSML, uses async native synthesis callback and `WavePlayer`; cancellation prevents further audio, retains parameter changes in one mode, and drops queued text. Termination blocks future callbacks and terminates native state (`speak`, `_callback`, `cancel`, `terminate`). |
| SAPI5 | Voice, rate, rate boost, pitch, volume, WASAPI (`synthDrivers.sapi5.SynthDriver.supportedSettings`) | Same eight commands and both notifications (`supportedCommands`, `supportedNotifications`) | Builds SAPI XML. WASAPI mode queues work on a dedicated thread; legacy mode uses SAPI callbacks. Cancellation stops audio and purges queues; termination joins the worker and closes the player (`speak`, `_speakThread`, `cancel`, `terminate`). |
| Silence | No settings (`synthDrivers.silence.SynthDriver.supportedSettings`) | It does not declare `supportedCommands` or `supportedNotifications`; it merely records the last `IndexCommand` and emits no notifications (`speak`) | Always available, produces no audio, cancel clears `lastIndex`, and inherits no-op pause plus base termination. This special dummy driver visibly does not satisfy the normal notification requirements and should not be copied as a functional synth design. |

## 13. Open questions

The inspected source does not confidently answer:

- Which exact NVDA release/commit this snapshot represents, or which add-on compatibility declarations are required; that metadata is outside the requested source scope.
- Whether third-party synth add-ons may emit notifications from arbitrary worker threads in all supported NVDA versions. Current manager handlers marshal processing, and built-ins emit from callbacks, but the base contract does not explicitly promise thread safety of `extensionPoints.Action.notify`.
- Whether `speak`, `cancel`, settings access, and `terminate` are guaranteed to be invoked only on NVDA’s main thread; no explicit guarantee was found.
- Whether `synthDoneSpeaking` must be emitted after cancellation, after an empty sequence, or after a synthesis error. The base requires notification support but does not specify these edge cases; built-in paths differ.
- Required ordering when the final index and completion happen nearly together, and whether every submitted index must be emitted after cancellation. The manager tolerates skipped/stale indexes, but that tolerance is not a driver contract.
- Whether a functional one-voice driver may omit `VoiceSetting` while still exposing a fixed `_get_voice`; silence is the only inspected example and is a special dummy.
- Whether `BreakCommand.time` has enforced bounds, and how percentage setting values outside 0–100 should be handled; documentation states ranges but these inspected constructors/base setters do not enforce them.
- Which audio API and worker architecture are preferred for a new driver. The examples show multiple approaches, not a mandated design.

## Future driver implementation checklist

- [ ] Export `SynthDriver`, derived from `synthDriverHandler.SynthDriver`, with module-matching `name` and accessible `description`.
- [ ] Make `check()` verify every required local runtime component without network access.
- [ ] Keep construction fallible and leave a successful instance fully usable; give missing dependency/model/audio failures concise user-facing handling at the integration layer.
- [ ] Advertise only implemented settings and commands; include `IndexCommand` and both required notifications.
- [ ] Accept strings plus advertised `SynthCommand` types; escape/translate text and markup safely without logging user text.
- [ ] Keep synthesis/audio work off the main thread; define ownership and synchronization for queues, model state, and audio.
- [ ] Make `cancel()` immediate: invalidate queued/in-flight work, stop audio, and prevent stale results from reaching playback or corrupting notification state.
- [ ] Implement `pause(True/False)` against audio output without losing queue/index state.
- [ ] Emit each valid index when its audio is reached and emit completion at the defined end of output; marshal only where supported by verified APIs.
- [ ] Implement voice enumeration with stable IDs and language metadata; validate Persian as a primary language without hardcoding it.
- [ ] Implement 0–100 settings accessors only for supported controls, including correct in-sequence prosody behavior where advertised.
- [ ] In `terminate()`, stop callbacks/workers, drain or stop audio safely, release model/native resources, and preserve base settings cleanup.
- [ ] Test rapid replacement, repeated short utterances, cancellation races, skipped/stale indexes, missing resources, initialization fallback, pause/resume, and shutdown.
