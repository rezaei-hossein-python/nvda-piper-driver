"""Development-only, character-cache waveform onset analysis.

This module never runs from the production add-on. It only transforms validated
16-bit PCM supplied by a development harness and is gated by an explicit
environment variable. Words, navigation, and ordinary speech are out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os

ACTIVATION_ENV = "NVDA_PIPER_EXPERIMENTAL_CHARACTER_ONSET"
POLICIES = {"current", "preserve40ms", "preserve25ms", "preserve15ms", "adaptive"}


@dataclass(frozen=True, slots=True)
class OnsetAnalysis:
	frames: int
	durationMs: float
	peak: int
	rms: float
	threshold: float
	firstSustainedFrame: int | None
	firstVoicedFrame: int | None
	leadingFrames: int
	clipping: bool


@dataclass(frozen=True, slots=True)
class OnsetResult:
	pcm: bytes
	policy: str
	originalFrames: int
	outputFrames: int
	cutFrame: int
	prerollFrames: int
	onsetShiftMs: float
	fallback: bool
	sha256: str


def enabled(environ: dict[str, str] | None = None) -> bool:
	return (environ or os.environ).get(ACTIVATION_ENV) == "1"


def _samples(pcm: bytes, channels: int) -> list[int]:
	if type(pcm) is not bytes or not pcm or channels <= 0 or len(pcm) % (2 * channels):
		raise ValueError("PCM must be non-empty aligned signed 16-bit bytes")
	return [int.from_bytes(pcm[index : index + 2], "little", signed=True) for index in range(0, len(pcm), 2)]


def _frameEnergy(samples: list[int], channels: int) -> list[float]:
	return [math.sqrt(sum(samples[index + channel] ** 2 for channel in range(channels)) / channels) for index in range(0, len(samples), channels)]


def analyze(pcm: bytes, sampleRate: int, channels: int = 1, *, sustainedFrames: int = 12) -> OnsetAnalysis:
	if type(sampleRate) is not int or sampleRate <= 0 or type(sustainedFrames) is not int or sustainedFrames <= 0:
		raise ValueError("invalid PCM analysis settings")
	samples = _samples(pcm, channels)
	energy = _frameEnergy(samples, channels)
	peak = max(abs(value) for value in samples)
	rms = math.sqrt(sum(value * value for value in samples) / len(samples))
	baselineCount = max(1, len(energy) // 10)
	baseline = sum(energy[:baselineCount]) / baselineCount
	threshold = max(256.0, baseline * 4.0, peak * 0.02)
	firstVoiced = next((index for index, value in enumerate(energy) if value >= threshold), None)
	firstSustained = None
	for index in range(0, max(0, len(energy) - sustainedFrames + 1)):
		if all(value >= threshold for value in energy[index : index + sustainedFrames]):
			firstSustained = index
			break
	return OnsetAnalysis(
		frames=len(energy),
		durationMs=len(energy) * 1000 / sampleRate,
		peak=peak,
		rms=rms,
		threshold=threshold,
		firstSustainedFrame=firstSustained,
		firstVoicedFrame=firstVoiced,
		leadingFrames=firstSustained or 0,
		clipping=peak >= 32767,
	)


def _nearestZero(energySamples: list[int], frame: int, channels: int, searchFrames: int = 80) -> int:
	start = max(0, frame - searchFrames)
	end = min(len(energySamples) // channels, frame + searchFrames + 1)
	return min(
		range(start, end),
		key=lambda candidate: (
			abs(candidate - frame),
			max(abs(energySamples[candidate * channels + channel]) for channel in range(channels)),
		),
	)


def _fadeIn(pcm: bytes, startFrame: int, frames: int, channels: int) -> bytes:
	if frames <= 1 or startFrame >= len(pcm) // (2 * channels):
		return pcm
	data = bytearray(pcm)
	for frame in range(min(frames, len(pcm) // (2 * channels) - startFrame)):
		gain = frame / max(1, frames - 1)
		for channel in range(channels):
			index = ((startFrame + frame) * channels + channel) * 2
			value = int.from_bytes(data[index : index + 2], "little", signed=True)
			value = max(-32768, min(32767, round(value * gain)))
			data[index : index + 2] = value.to_bytes(2, "little", signed=True)
	return bytes(data)


def optimize(pcm: bytes, sampleRate: int, *, policy: str = "adaptive", channels: int = 1, fadeMs: float = 1.0) -> OnsetResult:
	if policy not in POLICIES or type(fadeMs) not in (int, float) or not 0 <= fadeMs <= 5:
		raise ValueError("invalid onset policy")
	analysis = analyze(pcm, sampleRate, channels)
	originalFrames = analysis.frames
	if policy == "current" or analysis.firstSustainedFrame is None:
		return OnsetResult(pcm, policy, originalFrames, originalFrames, 0, 0, 0.0, True, hashlib.sha256(pcm).hexdigest())
	if policy == "preserve40ms":
		prerollMs = 40.0
	elif policy == "preserve25ms":
		prerollMs = 25.0
	elif policy == "preserve15ms":
		prerollMs = 15.0
	else:
		# Adaptive keeps a bounded pre-roll proportional to the detected energy
		# onset, without inspecting language, text, or character identity.
		prerollMs = min(40.0, max(10.0, analysis.durationMs * 0.04))
	prerollFrames = max(1, round(sampleRate * prerollMs / 1000))
	samples = _samples(pcm, channels)
	cutFrame = max(0, analysis.firstSustainedFrame - prerollFrames)
	cutFrame = _nearestZero(samples, cutFrame, channels)
	if cutFrame <= 0 or cutFrame >= originalFrames or originalFrames - cutFrame < max(1, originalFrames // 4):
		return OnsetResult(pcm, policy, originalFrames, originalFrames, 0, 0, 0.0, True, hashlib.sha256(pcm).hexdigest())
	frameBytes = channels * 2
	output = pcm[cutFrame * frameBytes :]
	output = _fadeIn(output, 0, min(round(sampleRate * fadeMs / 1000), len(output) // frameBytes), channels)
	outputFrames = len(output) // frameBytes
	return OnsetResult(output, policy, originalFrames, outputFrames, cutFrame, prerollFrames, cutFrame * 1000 / sampleRate, False, hashlib.sha256(output).hexdigest())


def cacheIdentity(baseIdentity: str, policy: str) -> str:
	if not isinstance(baseIdentity, str) or not baseIdentity or policy not in POLICIES:
		raise ValueError("invalid cache identity")
	return f"{baseIdentity}:character-onset:{policy}"
