"""Development-only audio-path diagnostic; never imported by the add-on package."""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class AudioEvent:
	eventId: int
	ordinal: int
	state: str
	queueDepth: int
	feedNs: int | None
	stopNs: int | None


def runMode(pcm: bytes, player, *, mode: str, count: int = 10, intervalSeconds: float = 0.0) -> tuple[AudioEvent, ...]:
	"""Run one bounded mode against an already validated WavePlayer-like object.

	The caller supplies PCM generated separately from an approved voice. No text,
	model, worker, IPC, or arbitrary file access is accepted here.
	"""
	if type(pcm) is not bytes or not pcm or len(pcm) % 2 or mode not in {"direct", "stop", "fifo", "continuous", "idle"}:
		raise ValueError("invalid diagnostic input")
	if type(count) is not int or not 1 <= count <= 100:
		raise ValueError("count is out of bounds")
	events: list[AudioEvent] = []
	for ordinal in range(1, count + 1):
		stopNs = None
		if mode == "stop":
			start = time.monotonic_ns()
			player.stop()
			stopNs = time.monotonic_ns() - start
		start = time.monotonic_ns()
		player.feed(pcm)
		feedNs = time.monotonic_ns() - start
		events.append(AudioEvent(ordinal, ordinal, "fed", max(0, count - ordinal), feedNs, stopNs))
		if intervalSeconds:
			time.sleep(min(intervalSeconds, 1.0))
	return tuple(events)
