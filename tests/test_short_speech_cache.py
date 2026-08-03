import unittest

from addon.synthDrivers._nvdaPiperDriver.shortSpeechCache import CacheKey, CachedPcm, ShortSpeechCache, analyzePcm, trimConservative


def key(value: str) -> CacheKey:
	return CacheKey(value, True, "model", "config", "voice", 50, 0, 100, 0.667, 1.0, 16000, 1, 2, "runtime")


class ShortSpeechCacheTests(unittest.TestCase):
	def value(self, generation: int, payload: bytes = b"\x00\x00") -> CachedPcm:
		return CachedPcm(payload, len(payload) // 2, 16000, 1, 2, generation, len(payload))

	def test_hit_and_unicode_key_isolated(self) -> None:
		cache = ShortSpeechCache()
		cache.put(key("é"), self.value(1))
		self.assertEqual(1, cache.get(key("é")).creationGeneration)
		self.assertIsNone(cache.get(key("e")))

	def test_entry_and_byte_bounds_evict_oldest(self) -> None:
		cache = ShortSpeechCache(maxEntries=2, maxBytes=4, maxEntryBytes=4)
		cache.put(key("a"), self.value(1, b"aa"))
		cache.put(key("b"), self.value(2, b"bb"))
		cache.put(key("c"), self.value(3, b"cc"))
		self.assertIsNone(cache.get(key("a")))
		self.assertEqual({"entries": 2, "bytes": 4, "evictions": 1}, cache.snapshot())

	def test_oversized_entries_are_rejected(self) -> None:
		cache = ShortSpeechCache(maxEntryBytes=2)
		self.assertFalse(cache.put(key("a"), self.value(1, b"1234")))
		self.assertEqual({"entries": 0, "bytes": 0, "evictions": 0}, cache.snapshot())

	def test_invalidation_is_atomic(self) -> None:
		cache = ShortSpeechCache()
		cache.put(key("a"), self.value(1))
		cache.invalidate("settings")
		self.assertIsNone(cache.get(key("a")))

	def test_pcm_analysis_is_content_free_and_aligned(self) -> None:
		pcm = (b"\x00\x00" * 100) + (b"\x00\x10" * 200) + (b"\x00\x00" * 100)
		facts = analyzePcm(pcm)
		self.assertEqual(400, facts["frames"])
		self.assertEqual(100, facts["leadingExactZero"])
		self.assertEqual(100, facts["trailingExactZero"])

	def test_conservative_trim_retains_padding_and_alignment(self) -> None:
		pcm = (b"\x00\x00" * 100) + (b"\x00\x10" * 300) + (b"\x00\x00" * 100)
		trimmed = trimConservative(pcm)
		self.assertGreater(len(trimmed), 0)
		self.assertEqual(0, len(trimmed) % 2)
		self.assertLess(len(trimmed), len(pcm))

	def test_short_or_quiet_pcm_falls_back_unchanged(self) -> None:
		pcm = b"\x00\x00" * 20
		self.assertEqual(pcm, trimConservative(pcm))


if __name__ == "__main__":
	unittest.main()
