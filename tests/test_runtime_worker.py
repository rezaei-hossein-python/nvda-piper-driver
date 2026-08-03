"""Tests for the persistent worker's warm-up and configuration reuse."""

import unittest

from addon.synthDrivers._nvdaPiperDriver.runtimeWorker import _synthesize, _warmVoice


class _Chunk:
	def __init__(self, audio: bytes) -> None:
		self.audio_int16_bytes = audio


class _Voice:
	class _Config:
		sample_rate = 16_000

	config = _Config()

	def __init__(self) -> None:
		self.calls: list[tuple[str, object]] = []

	def synthesize(self, text: str, *, syn_config: object):
		self.calls.append((text, syn_config))
		if text:
			yield _Chunk(b"\x01\x00")


class RuntimeWorkerTests(unittest.TestCase):
	def test_warmup_is_silent_and_language_neutral(self) -> None:
		voice = _Voice()
		config = object()
		_warmVoice(voice, config)
		self.assertEqual([("", config)], voice.calls)

	def test_synthesis_reuses_supplied_configuration(self) -> None:
		voice = _Voice()
		config = object()
		result = _synthesize(voice, "short", config)
		self.assertEqual((b"\x01\x00", 16_000), result)
		self.assertEqual([("short", config)], voice.calls)


if __name__ == "__main__":
	unittest.main()
