# Character echo and Read All compatibility

## Sequence shapes

The following shapes are source-derived and content-free. They describe item types only; no user text, language value, index value, or document content is captured.

| Workflow | Ordered shape observed or required by pinned NVDA |
|---|---|
| Ordinary focus/navigation | `LangChangeCommand?`, `Text`, final `IndexCommand` |
| Typed character | `CharacterModeCommand(True)`, `Text`, `CharacterModeCommand(False)`, final `IndexCommand` |
| Typed word | `Text`, final `IndexCommand` |
| Character description | `BreakCommand`, optional prosody, `Text`, final `IndexCommand` |
| Read All segment | `IndexCommand` for a `CallbackCommand`, text/control speech, `IndexCommand`, `EndUtteranceCommand` |
| Read All cancellation | queued sequences are cancelled and the synthesizer is stopped |

The exact text is intentionally absent from this table. A removable live sequence logger was not left in the add-on.

## Compatibility policy

| Phase 2E item | Phase 2J status | Reason |
|---|---|---|
| `TextItem` | Fully supported | Exact text is submitted in order. |
| `IndexItem` | Fully supported at segment boundaries | Each preceding segment is played before the real `synthIndexReached` callback is queued. |
| `LanguageChangeItem` | Metadata-tolerated | The explicitly selected single model is unchanged; no locale is inspected or retained. |
| `CharacterModeItem` | Fully supported as an isolated segment | NVDA-provided character text is synthesized by the selected Piper model without language-specific tables. |
| `BreakItem` | Explicitly unsupported | Silence timing is not represented by the current one-shot text request. |
| `ProsodyItem` | Explicitly unsupported | Piper settings mapping has not been verified for all rate/pitch/volume commands. |
| `PhonemeItem` | Explicitly unsupported | IPA must not be silently discarded or sent through an unverified phoneme path. |

Unsupported items now produce one bounded content-free warning per consecutive rejection episode, without an NVDA traceback or retained content. This prevents warning floods but does not claim support.

## Read All implementation

Read All cannot proceed correctly with completion alone. Pinned `sayAll.py` inserts callbacks that advance the reader; `SpeechManager` maps them to indexes and runs them only from `_handleIndex()` after `synthIndexReached`. The Phase 2J controller now splits requests at immutable index boundaries, plays each segment, and queues the corresponding callback only after that segment's `WavePlayer.idle()` returns. Stale, cancelled, failed, or superseded boundaries are suppressed. Final completion follows the last callback and audio boundary.

This is bounded segment timing rather than a frame-level stream. It may add latency at boundaries and must be validated in portable NVDA. No approximate timestamp, callback interception, or model-specific language behavior is used.
