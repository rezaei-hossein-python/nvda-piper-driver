# eSpeak interaction baseline

This is a source-backed Phase 2J investigation, not a claim that Piper should have identical latency.

## What NVDA supplies

Pinned NVDA constructs speech sequences before the driver sees them. `speech.speakSpelling()` wraps character text in `CharacterModeCommand(True/False)` when spelling functionality is enabled (`references/nvda-source/source/speech/speech.py:355-391, 615-640`). Typed characters call `speakSpelling()` and typed words call ordinary `speakText()` (`speech.py:1442-1490`). Normalized text may also contain `LangChangeCommand`; `SpeechManager` appends a final `IndexCommand` to ordinary utterances (`speech.py:1176-1192`, `manager.py:318-326`).

Read All is callback-driven. `sayAll.py` inserts `CallbackCommand` objects for `lineReached`, `next`, and final stop (`sayAll.py:194, 318-330, 390-395`). `SpeechManager._processSpeechSequence()` converts each callback to an `IndexCommand` (`manager.py:332-340`), and `_handleIndex()` runs the callback and advances the queue (`manager.py:674-714`). `synthDoneSpeaking` only invokes `_handleDoneSpeaking()` (`manager.py:722-731`); it does not run the callback mapped to an index.

## What eSpeak implements

The pinned eSpeak driver advertises `IndexCommand`, `CharacterModeCommand`, language changes, breaks, rate/pitch/volume, phonemes, and both index and completion notifications (`synthDrivers/espeak.py:14-54`). Its `speak()` converts character mode to SSML `<say-as interpret-as="characters">`, breaks to SSML `<break>`, prosody to SSML tags, phonemes to eSpeak phoneme syntax, language changes to voice tags, and indexes to SSML marks (`espeak.py:318-375`). It calls the native `_espeak.speak()` engine and stops it through `_espeak.stop()` (`espeak.py:375-383`). Native callbacks report indexes and final completion (`espeak.py:466-477`).

The transferable techniques are bounded request replacement, immediate stop, exact command ordering, and completion only after output. The non-transferable advantage is the compact native formant engine and its native mark/callback timing. Piper's neural inference, phonemization, model load, and sentence-chunk API have different costs and cannot be made equivalent by copying SSML handling.

## Baseline evidence

The controlled portable run qualitatively confirmed that eSpeak responds more immediately than the current Piper path. No synchronized event-to-audio timer was captured, so no numeric eSpeak latency claim is made. Standalone Piper evidence records a warm first chunk around 0.061 seconds for the approved model, while the current NVDA one-shot path also pays approximately 1.9 seconds of model loading for each child. These values are not a portable-NVDA comparison.
