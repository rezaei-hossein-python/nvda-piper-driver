"""Reproducible standalone benchmark for the Phase 2H Piper adapter."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import sys
from typing import Final, Sequence

from runtimeAdapter import PiperRuntimeAdapter, RuntimeAdapterError, inspectWav


DEFAULT_RUNS: Final = 5
DEFAULT_WARMUPS: Final = 1


@dataclass(frozen=True)
class BenchmarkSummary:
	count: int
	minimum: float
	median: float
	maximum: float


def summarize(values: Sequence[float]) -> BenchmarkSummary:
	if not values:
		raise ValueError("At least one measurement is required")
	return BenchmarkSummary(len(values), min(values), statistics.median(values), max(values))


def environmentRecord() -> dict[str, object]:
	return {
		"dateUtc": datetime.now(timezone.utc).date().isoformat(),
		"operatingSystem": platform.platform(),
		"machine": platform.machine(),
		"processor": platform.processor() or "unreported",
		"pythonVersion": platform.python_version(),
		"logicalCpuCount": os.cpu_count(),
	}


def runBenchmark(model: Path, config: Path, outputDirectory: Path, texts: Sequence[str], runs: int = DEFAULT_RUNS, warmups: int = DEFAULT_WARMUPS, speakerId: int | None = None) -> dict[str, object]:
	if type(runs) is not int or runs < 1 or runs > 100:
		raise ValueError("runs must be between 1 and 100")
	if type(warmups) is not int or warmups < 0 or warmups > 10:
		raise ValueError("warmups must be between 0 and 10")
	if not texts or any(not isinstance(text, str) or not text for text in texts):
		raise ValueError("texts must contain non-empty Unicode strings")
	outputDirectory = outputDirectory.resolve()
	if not outputDirectory.is_dir():
		raise ValueError("output directory must already exist")
	adapter = PiperRuntimeAdapter(model, config)
	load = adapter.load()
	records: list[dict[str, object]] = []
	try:
		for caseIndex, text in enumerate(texts):
			for runIndex in range(warmups + runs):
				output = outputDirectory / f"case-{caseIndex}-run-{runIndex}.wav"
				result = adapter.synthesize(text, output, speakerId=speakerId, overwrite=True)
				wav = inspectWav(output)
				if runIndex >= warmups:
					records.append({"case": caseIndex, "run": runIndex - warmups, "textCodePoints": len(text), **result.toDict(), "wav": wav})
	finally:
		adapter.close()
	grouped: dict[str, object] = {}
	for caseIndex in range(len(texts)):
		caseRecords = [record for record in records if record["case"] == caseIndex]
		grouped[str(caseIndex)] = {
			"elapsedSeconds": asdict(summarize([float(record["elapsedSeconds"]) for record in caseRecords])),
			"firstChunkSeconds": asdict(summarize([float(record["firstChunkSeconds"]) for record in caseRecords])),
			"realTimeFactor": asdict(summarize([float(record["realTimeFactor"]) for record in caseRecords])),
		}
	return {"schemaVersion": 1, "environment": environmentRecord(), "runtimeVersion": load.runtimeVersion, "executionProviders": load.executionProviders, "modelLoadSeconds": load.loadSeconds, "voiceMetadata": asdict(load.metadata), "runs": runs, "warmupsDiscarded": warmups, "records": records, "summaries": grouped}


def main(argv: Sequence[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Benchmark a manually supplied Piper model outside NVDA")
	parser.add_argument("--model", type=Path, required=True)
	parser.add_argument("--config", type=Path, required=True)
	parser.add_argument("--output-directory", type=Path, required=True)
	parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
	parser.add_argument("--warmups", type=int, default=DEFAULT_WARMUPS)
	parser.add_argument("--speaker-id", type=int)
	args = parser.parse_args(argv)
	texts = (
		"Short standalone check.",
		"Numbers 1, 2, and 3; punctuation: commas, periods, and questions?",
		"This longer standalone paragraph exercises repeated model reuse without choosing a language in reusable runtime code. It contains several clauses, a second sentence, and enough input to produce multiple seconds of audio for a meaningful real-time-factor measurement.",
		"Unicode input remains Unicode: café, naïve, coöperate.\nThis is a second line with a combining mark: e\u0301.",
	)
	try:
		record = runBenchmark(args.model, args.config, args.output_directory, texts, args.runs, args.warmups, args.speaker_id)
	except (RuntimeAdapterError, ValueError) as error:
		code = error.code if isinstance(error, RuntimeAdapterError) else "invalidBenchmark"
		print(json.dumps({"error": code}, separators=(",", ":")), file=sys.stderr)
		return 2
	print(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
