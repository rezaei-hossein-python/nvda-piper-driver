# Character queue overload policy

Character requests retain unique generation IDs and terminal accounting. The
queue has both an eight-entry safety limit and a 1.5-second estimated-audio
limit. Before either limit, events are preserved in FIFO order. When a limit
is reached, an identical rapid tail may be aggregated; a different character
is explicitly counted as dropped rather than merged.

Aggregation is bounded to one extra playback of the tail PCM. Cancellation,
navigation, focus changes, mouse-over, synthesizer switching, and shutdown
clear pending and aggregate state. No arbitrary text or document speech enters
this policy.
