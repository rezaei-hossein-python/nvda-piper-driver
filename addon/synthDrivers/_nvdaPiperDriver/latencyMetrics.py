"""Content-free monotonic latency traces for development validation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Final


MAX_TRACE_EVENTS: Final = 32
MAX_RETAINED_TRACES: Final = 128


@dataclass(slots=True)
class LatencyTrace:
	"""One request's timestamps; no speech content is retained."""
	requestId: int
	generationId: int
	_events: dict[str, int] = field(default_factory=dict, repr=False)

	def mark(self, event: str, nowNs: int | None = None) -> None:
		if type(event) is not str or not event or len(event) > 48:
			raise ValueError("invalid latency event")
		if len(self._events) >= MAX_TRACE_EVENTS and event not in self._events:
			raise RuntimeError("latency trace event limit exceeded")
		now = time.monotonic_ns() if nowNs is None else nowNs
		if type(now) is not int or now < 0:
			raise ValueError("invalid monotonic timestamp")
		previous = self._events.get(event)
		if previous is not None and now < previous:
			raise ValueError("latency timestamps must be monotonic")
		self._events[event] = now

	def snapshot(self) -> dict[str, int]:
		return dict(self._events)


class LatencyRecorder:
	"""Bounded in-memory recorder for local validation; never logs text."""

	def __init__(self) -> None:
		self._traces: deque[dict[str, object]] = deque(maxlen=MAX_RETAINED_TRACES)

	def record(self, trace: LatencyTrace) -> None:
		self._traces.append(
			{
				"requestId": trace.requestId,
				"generationId": trace.generationId,
				"timestamps": trace.snapshot(),
			}
		)

	def snapshot(self) -> tuple[dict[str, object], ...]:
		return tuple(self._traces)
