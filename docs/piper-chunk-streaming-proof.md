# Piper chunk streaming proof

Status: Proposed

## Current Python Piper generator

The current Piper generator yields one chunk for a character, word, short navigation phrase, and single sentence. For multi-sentence and long inputs it yields multiple chunks before the generator finishes. Repeated warm observations included:

- two-sentence input: first yield about 62–94 ms, completion about 125–157 ms, two chunks;
- twelve repeated long phrases: first yield about 94–109 ms, completion about 1,125–1,156 ms, twelve chunks.

Thus current Piper already has genuine sentence-level output for sufficiently long input, but the production worker concatenates all yields before sending PCM to NVDA.

## RT model

The RT prototype runs the encoder once, then decoder windows of 55 mel frames with three-frame padding. For the same Lessac text, navigation produced three decoder chunks; first usable PCM arrived around 183–242 ms and completion around 341–456 ms in the direct Python/ORT experiment. The first chunk was delivered while later decoder calls were still pending. This is decoder/model-chunk streaming, not frame streaming.

The timing is a runtime prototype, not an NVDA audible-onset measurement. The direct Python implementation is not selected as the production backend.

## Rejected production integration

The production integration emitted the same generator yields without concatenation, but portable NVDA validation rejected it: perceived response became slower, typed characters stopped speaking, document reading stopped, and navigation was no longer immediate. The preceding persistent full-request backend was materially better. These are first-IPC/worker timings, not physical audio onset, and do not establish production acceptance.
