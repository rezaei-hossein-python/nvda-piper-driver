"""Development-only cache-hit onset probe.

This module is deliberately independent of the add-on package.  It measures
the timestamped stages that can be exercised without Piper inference and never
accepts speech text, cache keys, or arbitrary audio paths.  Physical onset is
reported as unavailable unless an explicitly supplied capture adapter is used
by a development harness; ``feed`` is never treated as audible onset.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
from typing import Any, Protocol

ACTIVATION_ENV = "NVDA_PIPER_AUDIO_ONSET_DIAGNOSTIC"
MAX_TRIALS = 1000
VALID_SIGNALS = {"syntheticImpulse", "cachedPiper", "espeak"}
VALID_PATHS = {"direct", "stop", "idle", "behindAudio", "controller", "fullNvda"}


class Player(Protocol):
	def feed(self, pcm: bytes) -> None: ...

	def stop(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Signal:
	category: str
	pcm: bytes
	sampleRate: int
	channels: int = 1
	sampleWidth: int = 2

	@property
	def frames(self) -> int:
		return len(self.pcm) // (self.channels * self.sampleWidth)

	@property
	def durationMs(self) -> float:
		return self.frames * 1000.0 / self.sampleRate

	@property
	def sha256(self) -> str:
		return hashlib.sha256(self.pcm).hexdigest()


@dataclass(slots=True)
class ProbeEvent:
	eventId: int
	ordinal: int
	signal: str
	path: str
	inputNs: int
	driverEntryNs: int | None = None
	classificationStartNs: int | None = None
	classificationEndNs: int | None = None
	lookupStartNs: int | None = None
	lookupEndNs: int | None = None
	queueInsertNs: int | None = None
	queueDepth: int = 0
	controllerDispatchNs: int | None = None
	stopEntryNs: int | None = None
	stopReturnNs: int | None = None
	feedEntryNs: int | None = None
	feedReturnNs: int | None = None
	firstCapturedSampleNs: int | None = None
	firstPhoneticEnergyNs: int | None = None
	completionNs: int | None = None
	terminalState: str = "failed"


class RecordingPlayer:
	"""Small player double used for deterministic unit tests and proxy timing."""

	def __init__(self) -> None:
		self.feedCount = 0
		self.stopCount = 0

	def feed(self, pcm: bytes) -> None:
		if not pcm:
			raise ValueError("empty PCM")
		self.feedCount += 1

	def stop(self) -> None:
		self.stopCount += 1


def diagnosticEnabled(environ: dict[str, str] | None = None) -> bool:
	return (environ or os.environ).get(ACTIVATION_ENV) == "1"


def validatePcm(pcm: bytes, *, sampleRate: int, channels: int = 1, sampleWidth: int = 2) -> None:
	if type(pcm) is not bytes or not pcm:
		raise ValueError("PCM must be non-empty bytes")
	if sampleRate <= 0 or channels <= 0 or sampleWidth not in (1, 2, 3, 4):
		raise ValueError("invalid PCM format")
	if len(pcm) % (channels * sampleWidth):
		raise ValueError("PCM is not frame aligned")


def makeImpulse(sampleRate: int = 22050) -> Signal:
	# A deterministic 2 ms, mono, signed-16-bit impulse with no leading silence.
	pcm = (32767).to_bytes(2, "little", signed=True) + b"\0\0" * max(1, sampleRate // 500 - 1)
	return Signal("syntheticImpulse", pcm, sampleRate)


def makeTone(sampleRate: int = 22050, durationMs: int = 20) -> Signal:
	# Fixed low-amplitude tone, useful when an impulse is too brief for a device.
	frames = max(1, sampleRate * durationMs // 1000)
	pcm = bytearray()
	for i in range(frames):
		value = 12000 if (i // max(1, sampleRate // 440 // 2)) % 2 else -12000
		pcm.extend(int(value).to_bytes(2, "little", signed=True))
	return Signal("syntheticImpulse", bytes(pcm), sampleRate)


def loadFixedPcm(category: str, root: Path, *, sampleRate: int) -> Signal:
	"""Load only the two named ignored diagnostic fixtures, never arbitrary paths."""
	if category not in {"cachedPiper", "espeak"}:
		raise ValueError("unsupported fixture category")
	root = root.resolve()
	allowed = (root / ("cached-piper-character.pcm" if category == "cachedPiper" else "espeak-character.pcm")).resolve()
	if allowed.parent != root or not allowed.is_file():
		raise FileNotFoundError("fixed diagnostic fixture is unavailable")
	pcm = allowed.read_bytes()
	validatePcm(pcm, sampleRate=sampleRate)
	return Signal(category, pcm, sampleRate)


def runTrials(signal: Signal, player: Player, *, path: str, count: int = 100, intervalSeconds: float = 0.0) -> tuple[ProbeEvent, ...]:
	if signal.category not in VALID_SIGNALS or path not in VALID_PATHS:
		raise ValueError("unsupported diagnostic selection")
	if type(count) is not int or not 1 <= count <= MAX_TRIALS:
		raise ValueError("trial count is out of bounds")
	events: list[ProbeEvent] = []
	for ordinal in range(1, count + 1):
		start = time.monotonic_ns()
		event = ProbeEvent(ordinal, ordinal, signal.category, path, start)
		event.driverEntryNs = time.monotonic_ns()
		event.classificationStartNs = event.driverEntryNs
		event.classificationEndNs = time.monotonic_ns()
		event.lookupStartNs = event.classificationEndNs
		event.lookupEndNs = time.monotonic_ns()
		event.queueInsertNs = event.lookupEndNs
		event.queueDepth = 0
		event.controllerDispatchNs = time.monotonic_ns()
		if path == "stop":
			event.stopEntryNs = time.monotonic_ns()
			player.stop()
			event.stopReturnNs = time.monotonic_ns()
		event.feedEntryNs = time.monotonic_ns()
		player.feed(signal.pcm)
		event.feedReturnNs = time.monotonic_ns()
		event.terminalState = "fed"
		event.completionNs = time.monotonic_ns()
		events.append(event)
		if intervalSeconds > 0:
			time.sleep(min(intervalSeconds, 1.0))
	return tuple(events)


def _deltaMs(events: list[ProbeEvent], start: str, end: str) -> list[float]:
	values: list[float] = []
	for event in events:
		a, b = getattr(event, start), getattr(event, end)
		if a is not None and b is not None and b >= a:
			values.append((b - a) / 1_000_000)
	return values


def summarize(events: tuple[ProbeEvent, ...]) -> dict[str, Any]:
	feed = _deltaMs(list(events), "inputNs", "feedReturnNs")
	return {
		"samples": len(events),
		"failures": sum(e.terminalState == "failed" for e in events),
		"terminalStates": {state: sum(e.terminalState == state for e in events) for state in {e.terminalState for e in events}},
		"inputToFeedMs": _stats(feed),
		"physicalOnset": "unavailable",
		"firstCapturedSampleMs": "unknown",
		"firstPhoneticEnergyMs": "unknown",
	}


def _stats(values: list[float]) -> dict[str, float | int | None]:
	if not values:
		return {"count": 0, "minimum": None, "median": None, "maximum": None, "p95": None, "stdev": None}
	ordered = sorted(values)
	return {"count": len(values), "minimum": min(values), "median": statistics.median(values), "maximum": max(values), "p95": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0}


def report(events: tuple[ProbeEvent, ...], *, signal: Signal, output: Path) -> None:
	output.parent.mkdir(parents=True, exist_ok=True)
	payload = {"schema": 1, "signal": {"category": signal.category, "frames": signal.frames, "durationMs": signal.durationMs, "sampleRate": signal.sampleRate, "channels": signal.channels, "sampleWidth": signal.sampleWidth, "sha256": signal.sha256}, "capture": {"available": False, "method": None, "uncertainty": "No supported loopback/capture adapter is installed; feed timestamps are not audible onset."}, "summary": summarize(events), "events": [asdict(e) for e in events]}
	output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
	if not diagnosticEnabled():
		print(f"disabled: set {ACTIVATION_ENV}=1")
		return 2
	player = RecordingPlayer()
	signal = makeImpulse()
	events = runTrials(signal, player, path="direct", count=100)
	print(json.dumps({"signal": signal.category, "summary": summarize(events), "capture": "unavailable"}, separators=(",", ":")))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
