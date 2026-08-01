# Speech-job conversion

## Purpose and boundary

Phase 2E adds a pure conversion boundary between one NVDA driver-facing speech sequence and one immutable project-owned `SpeechJob`. Conversion does not queue, submit, execute, synthesize, cancel, pause, notify, perform I/O, or retain text in the driver. `SynthDriver.speak()` remains unavailable and raises before using its argument.

The private support package is `synthDrivers._nvdaPiperDriver`. Pinned `synthDriverHandler.getSynthList` skips names beginning with `_` (`references/nvda-source/source/synthDriverHandler.py`, `getSynthList`), so this package is not a separate synthesizer driver.

## Pinned NVDA input contract

Pinned `speech.types.SpeechSequence` is `list[SpeechCommand | str]`, and `SynthDriver.speak` documents a list of text strings and `SynthCommand` objects. The converter therefore accepts only an exact built-in `list`. Tuples, mappings, bytes, generators, arbitrary iterables, and `list` subclasses are rejected rather than consumed implicitly.

The exact accepted item types are:

- `str`;
- `IndexCommand`;
- `CharacterModeCommand`;
- `LangChangeCommand`;
- `BreakCommand`;
- `RateCommand`;
- `PitchCommand`;
- `VolumeCommand`;
- `PhonemeCommand`.

These are the driver-facing types defined in pinned `references/nvda-source/source/speech/commands.py`. Exact type checks deliberately reject arbitrary subclasses and pipeline-only commands such as `CallbackCommand`, `ConfigProfileTriggerCommand`, `EndUtteranceCommand`, and `SuppressUnicodeNormalizationCommand`.

## Immutable model

All records are frozen, slotted dataclasses. `SpeechJob.items` is a tuple and preserves input order.

| Record | Copied fields |
|---|---|
| `SpeechJob` | `jobId`, `generationId`, `requestNumber`, immutable items, `voiceId`, `rate` |
| `TextItem` | exact text, without normalization, trimming, merging, or escaping |
| `IndexItem` | integer index |
| `CharacterModeItem` | Boolean state |
| `LanguageChangeItem` | string language or `None` |
| `BreakItem` | integer duration in milliseconds |
| `ProsodyItem` | rate/pitch/volume tag, original offset, original multiplier, original reset/default meaning |
| `PhonemeItem` | IPA string and fallback string or `None` |

Prosody values are records only; they are not applied and do not advertise command support. Conversion copies pinned `_offset` and `_multiplier` storage because the derived `offset` and `multiplier` properties can read global synthesizer configuration. IPA and fallback text are copied without interpretation.

## Validation and atomic failure

The converter performs strict validation without coercion:

- index and break values must have exact type `int`, excluding `bool`;
- character mode and command default flags must have exact type `bool`;
- language must be exact `str` or `None`;
- IPA must be exact `str`; fallback must be exact `str` or `None`;
- prosody offset must be exact `int`, multiplier exact `int` or `float`, and stored values/default state must be internally consistent;
- active voice must be a non-empty exact `str` and active rate an exact integer in `0..100`.

Malformed supported commands raise `TypeError` or `ValueError` with field/type context but no field value. Unsupported types raise `UnsupportedSpeechItemError`, whose message identifies only the type. The converter never calls `repr()` or `str()` on an item. Conversion builds a local tuple first, returns no partial job, and advances no identifier after any failure.

## Identifier strategy

Each `SpeechJobConverter` owns separate job, generation, and request counters. All start at `1`, increment monotonically only after a job is constructed successfully, and are bounded at `2^63 - 1`. Exhaustion raises `OverflowError` without advancing a counter. IDs contain no time, randomness, text, hash, persistent state, or cross-process guarantee.

Phase 2E assigns a new generation ID to each converted job solely to validate immutable identity propagation. Phase 2G must define cancellation-era generation allocation before using this field for stale-result rejection.

## Settings and lifecycle

`SynthDriver._createSpeechJob` is a private future production boundary. It first requires the Phase 2D `ready` state, then passes the current mock voice and rate by value. Later setting changes or termination cannot mutate an existing job. The method returns the job directly and the driver retains only its converter counters, not the returned job or speech text.

Unavailable construction remains rejected. Conversion after termination raises the existing lifecycle error. The mock voice and rate still do not affect speech.

## Privacy and side effects

Neither module imports logging, filesystem, process, thread, queue, network, audio, model, Piper, ONNX Runtime, worker, or protocol facilities. Text appears only in the caller-owned source and returned immutable job. It is not logged, formatted for errors, hashed into IDs, written, sent, or stored globally.

Tests preserve whitespace, empty strings, Persian, English, mixed text, punctuation, newlines, combining marks, zero-width characters, and directional characters exactly. Those tests establish conversion fidelity, not future synthesis safety.

## Verification and limitations

Unit tests cover immutability, source-list mutation, item order, every supported command, malformed fields, unsupported and pipeline-only items, hostile objects, atomic failures, deterministic/bounded identifiers, setting snapshots, and lifecycle restrictions. Archive tests require only the driver, private support package, manifest, and generated help.

No safe portable NVDA validation is required for this pure layer; existing real-NVDA selection and inherited configuration questions remain pending. Phase 2F is limited to a fake-worker protocol prototype. It may consume immutable jobs but must not add Piper, ONNX Runtime, model handling, or real audio. Generation semantics must remain provisional until Phase 2G.
