"""Pure metric and record tests for the standalone benchmark."""

from __future__ import annotations

import importlib.util
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "piperRuntime"
sys.path.insert(0, str(EXPERIMENT))
try:
	spec = importlib.util.spec_from_file_location("phase2hBenchmark", EXPERIMENT / "benchmark.py")
	assert spec is not None and spec.loader is not None
	benchmark = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = benchmark
	spec.loader.exec_module(benchmark)
finally:
	sys.path.remove(str(EXPERIMENT))


class BenchmarkTests(unittest.TestCase):
	def test_summary_is_deterministic(self) -> None:
		summary = benchmark.summarize([4.0, 1.0, 3.0, 2.0, 5.0])
		self.assertEqual(5, summary.count)
		self.assertEqual(1.0, summary.minimum)
		self.assertEqual(3.0, summary.median)
		self.assertEqual(5.0, summary.maximum)
		with self.assertRaises(FrozenInstanceError):
			summary.count = 6

	def test_summary_rejects_empty_input(self) -> None:
		with self.assertRaises(ValueError):
			benchmark.summarize([])

	def test_environment_record_is_structured(self) -> None:
		record = benchmark.environmentRecord()
		self.assertEqual({"dateUtc", "operatingSystem", "machine", "processor", "pythonVersion", "logicalCpuCount"}, set(record))
		self.assertNotIn(str(Path.home()), str(record))

	def test_benchmark_source_has_no_network_or_timing_claims(self) -> None:
		source = (EXPERIMENT / "benchmark.py").read_text(encoding="utf-8").lower()
		for forbidden in ("requests", "urllib", "socket", "sleep(", "shell=true"):
			self.assertNotIn(forbidden, source)


if __name__ == "__main__":
	unittest.main()
