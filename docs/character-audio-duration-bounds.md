# Character audio-duration bounds

The representative selected Piper character PCM is approximately 0.46 seconds
long. A count-only queue therefore permitted too much stale audio under an
operating-system held-key repeat. The experiment tracks estimated active plus
pending duration and keeps a separate hard entry bound. The estimate is
language- and voice-neutral as a conservative scheduling bound; actual PCM is
still validated by the existing playback path.

The tested provisional value is 1.5 seconds. Portable validation must confirm
that normal typing remains faithful, held input does not become silent, and
release does not leave a long backlog.
