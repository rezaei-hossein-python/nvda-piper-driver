# Character throughput

The Phase 2L bounded FIFO remains the throughput boundary: eight pending
character events, explicit overflow accounting, and cancellation clearing the
queue. Phase 2M changes only the duration of newly synthesized character-cache
entries; it does not introduce aggregation or silently drop accepted events.
