# Held-key character repetition

Status: Experimental; portable validation pending.

The Phase 2L character path used a bounded FIFO, but each new character also
advanced the single current generation. That made an active character stale
while it was still queued, and the eight-entry limit then discarded later
events. The observed result was a few repetitions, silence while the key was
held, and a final character after release.

The held-key experiment keeps accepted character generations valid together,
uses a separate duration bound, and records explicit aggregation or overflow.
Navigation, focus, mouse-over, ordered speech, and cancellation clear the
character epoch and remain newest-wins or ordered as before.

The selected provisional bound is 1.5 seconds of estimated active plus pending
character audio and eight pending entries. Identical rapid tail events beyond
the bound are explicitly aggregated; different units are never aggregated.
The aggregate receives at most one additional playback, avoiding an
unbounded obsolete backlog. This is an experiment, not yet an accepted
production behavior.
