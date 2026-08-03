"""Bounded, process-memory cache for explicitly enabled character speech."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import threading
from typing import Final


MAX_ENTRIES: Final = 32
MAX_TOTAL_BYTES: Final = 256 * 1024
MAX_ENTRY_BYTES: Final = 32 * 1024
TRIM_ENV: Final = "NVDA_PIPER_EXPERIMENTAL_CHARACTER_TRIM"


def analyzePcm(pcm: bytes, sampleWidth: int = 2) -> dict[str, int]:
	"""Return content-free amplitude/length facts for aligned PCM."""
	if type(pcm) is not bytes or sampleWidth != 2 or not pcm or len(pcm) % 2:
		raise ValueError("PCM must be nonempty aligned 16-bit bytes")
	samples = [int.from_bytes(pcm[index : index + 2], "little", signed=True) for index in range(0, len(pcm), 2)]
	amplitudes = [abs(value) for value in samples]
	return {
		"frames": len(samples),
		"durationMs": len(samples) * 1000 // 16_000,
		"peak": max(amplitudes),
		"rmsHundredths": int((sum(value * value for value in samples) / len(samples)) ** 0.5 * 100),
		"leadingExactZero": next((index for index, value in enumerate(samples) if value), len(samples)),
		"trailingExactZero": next((index for index, value in enumerate(reversed(samples)) if value), len(samples)),
		"leadingNearZero256": next((index for index, value in enumerate(samples) if abs(value) >= 256), len(samples)),
		"trailingNearZero256": next((index for index, value in enumerate(reversed(samples)) if abs(value) >= 256), len(samples)),
	}


def trimConservative(pcm: bytes, *, threshold: int = 256, sustainedFrames: int = 160, preRoll: int = 80, postRoll: int = 160) -> bytes:
	"""Trim only sustained low-amplitude margins, retaining conservative padding."""
	if type(pcm) is not bytes or not pcm or len(pcm) % 2:
		return pcm
	samples = [int.from_bytes(pcm[index : index + 2], "little", signed=True) for index in range(0, len(pcm), 2)]
	if any(abs(value) >= threshold for value in samples[: min(len(samples), preRoll)]):
		return pcm
	def sustained(start: int) -> bool:
		return start + sustainedFrames <= len(samples) and all(abs(value) >= threshold for value in samples[start : start + sustainedFrames])
	start = next((index for index in range(len(samples)) if sustained(index)), 0)
	reverse = list(reversed(samples))
	endFromReverse = next((index for index in range(len(reverse)) if sustained(len(samples) - index - sustainedFrames)), 0)
	end = len(samples) - endFromReverse
	start = max(0, start - preRoll)
	end = min(len(samples), end + postRoll)
	if end <= start or end - start < len(samples) // 2:
		return pcm
	return b"".join(int(value).to_bytes(2, "little", signed=True) for value in samples[start:end])


@dataclass(frozen=True, slots=True)
class CacheKey:
	spoken: str
	characterMode: bool
	modelIdentity: str
	configurationIdentity: str
	speaker: str
	rate: int
	pitch: int
	volume: int
	noiseScale: float
	lengthScale: float
	sampleRate: int
	channels: int
	sampleWidth: int
	runtimeIdentity: str


@dataclass(frozen=True, slots=True)
class CachedPcm:
	pcm: bytes
	frameCount: int
	sampleRate: int
	channels: int
	sampleWidth: int
	creationGeneration: int
	byteSize: int


class ShortSpeechCache:
	"""Thread-safe deterministic LRU with no persistence or key logging."""

	def __init__(self, maxEntries: int = MAX_ENTRIES, maxBytes: int = MAX_TOTAL_BYTES, maxEntryBytes: int = MAX_ENTRY_BYTES) -> None:
		if not all(type(value) is int and value > 0 for value in (maxEntries, maxBytes, maxEntryBytes)):
			raise ValueError("cache limits must be positive integers")
		self._maxEntries = maxEntries
		self._maxBytes = maxBytes
		self._maxEntryBytes = maxEntryBytes
		self._entries: OrderedDict[CacheKey, CachedPcm] = OrderedDict()
		self._totalBytes = 0
		self._evictions = 0
		self._lock = threading.RLock()

	def get(self, key: CacheKey) -> CachedPcm | None:
		with self._lock:
			value = self._entries.get(key)
			if value is None:
				return None
			self._entries.move_to_end(key)
			return value

	def put(self, key: CacheKey, value: CachedPcm) -> bool:
		if type(value.pcm) is not bytes or value.byteSize != len(value.pcm) or value.byteSize <= 0:
			return False
		if value.byteSize > self._maxEntryBytes or value.byteSize > self._maxBytes:
			return False
		if value.channels <= 0 or value.sampleWidth <= 0 or value.frameCount != value.byteSize // (value.channels * value.sampleWidth):
			return False
		with self._lock:
			old = self._entries.pop(key, None)
			if old is not None:
				self._totalBytes -= old.byteSize
			self._entries[key] = value
			self._totalBytes += value.byteSize
			while len(self._entries) > self._maxEntries or self._totalBytes > self._maxBytes:
				_, evicted = self._entries.popitem(last=False)
				self._totalBytes -= evicted.byteSize
				self._evictions += 1
			return key in self._entries

	def invalidate(self, _reason: str) -> None:
		with self._lock:
			self._entries.clear()
			self._totalBytes = 0

	def snapshot(self) -> dict[str, int]:
		with self._lock:
			return {"entries": len(self._entries), "bytes": self._totalBytes, "evictions": self._evictions}
