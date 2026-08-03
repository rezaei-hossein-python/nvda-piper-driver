# Phase 2L short-speech classification

Status: Experimental

The control backend continues to use the Phase 2K request path. When
`NVDA_PIPER_EXPERIMENTAL_SHORT_SPEECH=1` is set, the driver may enable the
bounded interactive path. The PCM cache additionally requires
`NVDA_PIPER_EXPERIMENTAL_CACHE=1`.

Classification is deliberately conservative and uses only the already
converted NVDA sequence: one non-empty segment, at most 64 code points, and
`characterMode=True` is a cache-eligible character unit. Words, navigation,
controls, ordinary speech, Read All, and long requests use the ordinary warm
worker. No language, script, or document inspection is performed.
