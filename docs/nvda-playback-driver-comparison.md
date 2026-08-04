# NVDA 2026.1.1 playback-driver comparison

This comparison is source-based; `feed()` and completion are not audible-onset
measurements.

| Driver | PCM delivery | Chunk size | Persistent player | `stop()` policy | `idle()` policy | Completion policy |
| --- | --- | ---: | --- | --- | --- | --- |
| Piper | controller feeds validated PCM | project currently 50 ms | reused while format/device match | cancellation and replacement | after complete result | controller drain, then NVDA done notification |
| eSpeak | engine callback supplies PCM and event offsets | engine callback boundaries | module-level player | cancellation aborts synthesis | terminal callback calls `idle()` | event callbacks and terminal event |
| OneCore | native stream markers and PCM | native marker boundaries | driver player | cancellation stops native stream | after queue processing | native stream completion |
| SAPI5 | audio callback / stream data | engine callback boundaries | driver player | stop before purge | speech thread calls `idle()` when queue empty | bookmarks then done notification |

The NVDA source does not establish a universal fixed chunk size. Engine-native
drivers feed the boundaries supplied by their engines and use `WavePlayer` as
the output sink.
