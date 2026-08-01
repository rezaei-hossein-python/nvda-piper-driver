# Accessibility acceptance criteria

## Objective criteria

- Every operation is reachable with keyboard alone; tab/shift-tab order follows task order, Escape cancels safely, Enter activates the documented default.
- Native controls are used where adequate. Every control exposes an accurate name, role, value/state, required/invalid state, and associated help; group labels are programmatic.
- Focus is visible in high contrast where applicable, but color, icon, position, animation, or sound is never the sole information channel.
- Validation identifies the field and correction, moves/focuses predictably without destroying input, and does not open a modal loop.
- Progress has a named status, coarse rate-limited announcements, determinate value when known, and a keyboard-reachable cancel action. No rapid announcement flooding.
- Voice selection is fully nonvisual. Each item communicates display name, locale, speaker, validation state, quality/size if known, provenance/licence status, and whether restart/load is needed without requiring a tooltip.
- First run explains that no voice is bundled, operation is offline, and how to import a local verified model. Missing-model/runtime/device errors are concise and actionable.
- Update/restart/uninstall prompts state consequence and preserve focus. Restart is requested only when required. Model retention/removal is an explicit choice.
- Help uses semantic headings, lists, tables with headers, descriptive links, keyboard navigation, language declaration, and accessible plain text/HTML. Localized UI never exposes untranslated placeholder keys.
- Diagnostic dialogs do not display synthesized user text unless a future separate explicitly requested feature is designed. Logs/status avoid text by default.

## Screen-reader behavior

Normal navigation produces no add-on status chatter beyond spoken content. Cancellation does not announce internal state. Repeated identical errors are coalesced. Status messages are short, unique, and actionable; technical detail belongs in redacted logs. Closing or correcting a dialog returns focus to the invoking control or failed field. Worker failures cannot generate cascading modal dialogs.

## Workflow-specific acceptance

| Workflow | Pass condition |
|---|---|
| Model import | File picker, metadata review, validation, progress, cancel, success/failure, and focus restoration work without mouse. |
| Settings | Voice/rate/volume and advanced controls have labels, values, logical order, defaults, and validation; unavailable capabilities are absent or clearly unavailable. |
| First run | User can reach help/import or dismiss safely; no network starts; driver does not trap speech selection. |
| Missing model | Driver remains repairable, names the problem once, and offers direct next action. |
| Update/restart | Consequence and model preservation are announced before confirmation; default action is safe. |
| Documentation/localization | English source and each shipped locale build open from Add-on Help and retain structure. |

## Manual test script

1. Start a clean supported installed NVDA using only keyboard; install/select the test package when that milestone exists.
2. With no model, verify one concise message, focus, dismissal, help, and no network traffic.
3. Open every settings page; traverse forward/backward; record spoken name/role/state/value and focus order.
4. Enter invalid folder/selection values; verify field-specific message, preserved input, and focus restoration.
5. Import valid, invalid, corrupt, duplicate, and low-disk models; exercise progress cancellation at each stage.
6. Select voices/speakers/languages nonvisually, including Persian metadata and long/bidirectional names.
7. Start speech, pause/resume/cancel rapidly, change voice/settings, and trigger worker/audio failure; check announcement volume and absence of loops.
8. Exercise update/restart/uninstall retention choices and return focus.
9. Open help and navigate headings, links, lists, and tables; repeat with each available locale and high contrast.
10. Inspect diagnostic UI/log using sentinel private text; fail if text appears. Repeat essential flows in portable NVDA.

Record NVDA/Windows/add-on versions, keyboard sequence, expected/actual speech and focus, and severity. Do not record private synthesized content.
