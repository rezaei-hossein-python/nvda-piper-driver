# Piper and eSpeak performance comparison

Status: Proposed

Pinned eSpeak speaks through a native asynchronous engine and reports indexes/completion from native callbacks. Piper uses a persistent isolated Python worker and complete Piper generator chunks, so the technologies are not equivalent.

The reproducible Piper bridge baseline is 24–30 ms for warm character/word/control requests, approximately 39 ms for a short navigation phrase, and approximately 79 ms for a short sentence. No synchronized eSpeak event-to-audible timer was available, so a numeric Piper/eSpeak ratio is not claimed. Manual portable observations identify eSpeak as more immediate.

NVDA-owned queue, cancellation, notification, and audio ownership patterns remain unchanged.
