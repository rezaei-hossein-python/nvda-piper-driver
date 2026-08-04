"""Development-only WASAPI loopback probe using PyAudioWPatch.

The module is outside the add-on and accepts no text or arbitrary files. It
plays one deterministic short tone through the default output and records the
matching default loopback device in memory. Captured audio is intentionally not
written by this probe; callers may retain only redacted timing summaries.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import json
from pathlib import Path
import threading
import time

ACTIVATION_ENV = "NVDA_PIPER_LOOPBACK_CAPTURE"
SAMPLE_RATE = 48_000
CHANNELS = 2
SAMPLE_WIDTH = 2
FRAMES_PER_BUFFER = 480


@dataclass(frozen=True, slots=True)
class CaptureResult:
	outputDevice: str
	loopbackDevice: str
	sampleRate: int
	channels: int
	startedNs: int
	playedNs: int
	firstNonSilentNs: int | None
	framesCaptured: int
	uncertaintyMs: float


def enabled(environ: dict[str, str] | None = None) -> bool:
	return (environ or os.environ).get(ACTIVATION_ENV) == "1"


def _tone(frameCount: int = SAMPLE_RATE // 50) -> bytes:
	"""Create a deterministic 20 ms, stereo, low-level square-wave marker."""
	period = max(2, SAMPLE_RATE // 440)
	data = bytearray()
	for frame in range(frameCount):
		value = 8192 if (frame // (period // 2)) % 2 else -8192
		encoded = int(value).to_bytes(SAMPLE_WIDTH, "little", signed=True)
		data.extend(encoded * CHANNELS)
	return bytes(data)


def _resampleMono16ToStereo48(pcm: bytes, sourceRate: int) -> bytes:
	if type(pcm) is not bytes or not pcm or sourceRate <= 0 or len(pcm) % 2:
		raise ValueError("invalid fixed PCM")
	sourceFrames = len(pcm) // 2
	outputFrames = max(1, round(sourceFrames * SAMPLE_RATE / sourceRate))
	output = bytearray()
	for frame in range(outputFrames):
		sourceIndex = min(sourceFrames - 1, round(frame * sourceRate / SAMPLE_RATE))
		sample = pcm[sourceIndex * 2 : sourceIndex * 2 + 2]
		output.extend(sample * CHANNELS)
	return bytes(output)


def loadFixedPiperFixture() -> bytes:
	path = (Path(".phase2r-fixtures") / "piper-character.wav").resolve()
	if path.parent.name != ".phase2r-fixtures" or not path.is_file():
		raise FileNotFoundError("fixed Piper fixture is unavailable")
	import wave
	with wave.open(str(path), "rb") as wavFile:
		if wavFile.getnchannels() != 1 or wavFile.getsampwidth() != 2:
			raise ValueError("fixed Piper fixture format is unsupported")
		return _resampleMono16ToStereo48(wavFile.readframes(wavFile.getnframes()), wavFile.getframerate())


def _firstNonSilent(samples: bytes, threshold: int = 512) -> int | None:
	frameSize = CHANNELS * SAMPLE_WIDTH
	for frame in range(0, len(samples) // frameSize):
		for channel in range(CHANNELS):
			start = frame * frameSize + channel * SAMPLE_WIDTH
			if abs(int.from_bytes(samples[start : start + SAMPLE_WIDTH], "little", signed=True)) >= threshold:
				return frame
	return None


def _firstMarkerFrame(samples: bytes, baseline: bytes) -> int | None:
	"""Find a sustained marker above the pre-playback loopback baseline."""
	frameSize = CHANNELS * SAMPLE_WIDTH
	baselineValues = [abs(int.from_bytes(baseline[index : index + SAMPLE_WIDTH], "little", signed=True)) for index in range(0, len(baseline), SAMPLE_WIDTH)]
	base = (sum(baselineValues) // len(baselineValues)) if baselineValues else 0
	# Shared-mode loopback may attenuate speech substantially; keep a conservative
	# floor while still requiring energy above the measured baseline.
	threshold = max(32, base * 3 + 16)
	consecutive = 0
	for frame in range(0, len(samples) // frameSize):
		start = frame * frameSize
		energy = sum(abs(int.from_bytes(samples[start + channel * SAMPLE_WIDTH : start + (channel + 1) * SAMPLE_WIDTH], "little", signed=True)) for channel in range(CHANNELS)) // CHANNELS
		if energy >= threshold:
			consecutive += 1
			if consecutive >= 3:
				return frame - 2
		else:
			consecutive = 0
	return None


def captureOnce() -> CaptureResult:
	if not enabled():
		raise RuntimeError(f"set {ACTIVATION_ENV}=1")
	try:
		import pyaudiowpatch as pyaudio
	except ImportError as error:  # pragma: no cover - exercised only in dev env.
		raise RuntimeError("PyAudioWPatch is not installed in the capture environment") from error
	audio = pyaudio.PyAudio()
	try:
		output = audio.get_default_output_device_info()
		loopback = audio.get_default_wasapi_loopback()
		marker = _tone()
		inputStream = audio.open(
			format=pyaudio.paInt16,
			channels=CHANNELS,
			rate=SAMPLE_RATE,
			input=True,
			input_device_index=loopback["index"],
			frames_per_buffer=FRAMES_PER_BUFFER,
		)
		outputStream = audio.open(
			format=pyaudio.paInt16,
			channels=CHANNELS,
			rate=SAMPLE_RATE,
			output=True,
			output_device_index=output["index"],
			frames_per_buffer=FRAMES_PER_BUFFER,
		)
		try:
			inputStream.start_stream()
			baseline = bytearray()
			for _ in range(10):
				baseline.extend(inputStream.read(FRAMES_PER_BUFFER, exception_on_overflow=False))
			started = time.monotonic_ns()
			writer = threading.Thread(target=outputStream.write, args=(marker,), daemon=True)
			writer.start()
			captured = bytearray()
			for _ in range(100):
				captured.extend(inputStream.read(FRAMES_PER_BUFFER, exception_on_overflow=False))
			writer.join(timeout=2.0)
			played = time.monotonic_ns()
			firstFrame = _firstMarkerFrame(bytes(captured), bytes(baseline))
			firstNs = None if firstFrame is None else started + int(firstFrame * 1_000_000_000 / SAMPLE_RATE)
			return CaptureResult(
				outputDevice="default-output",
				loopbackDevice="default-output-loopback",
				sampleRate=SAMPLE_RATE,
				channels=CHANNELS,
				startedNs=started,
				playedNs=played,
				firstNonSilentNs=firstNs,
				framesCaptured=len(captured) // (CHANNELS * SAMPLE_WIDTH),
				uncertaintyMs=FRAMES_PER_BUFFER * 1000 / SAMPLE_RATE,
			)
		finally:
			outputStream.stop_stream()
			outputStream.close()
			inputStream.stop_stream()
			inputStream.close()
	finally:
		audio.terminate()


if __name__ == "__main__":
	result = captureOnce()
	delayMs = None if result.firstNonSilentNs is None else (result.firstNonSilentNs - result.startedNs) / 1_000_000
	print(json.dumps({"sampleRate": result.sampleRate, "channels": result.channels, "framesCaptured": result.framesCaptured, "firstMarker": result.firstNonSilentNs is not None, "markerDelayMs": delayMs, "uncertaintyMs": result.uncertaintyMs}, separators=(",", ":")))
