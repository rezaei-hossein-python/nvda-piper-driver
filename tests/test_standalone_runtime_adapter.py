"""Pure tests for the standalone Phase 2H Piper adapter."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import wave


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "piperRuntime" / "runtimeAdapter.py"
spec = importlib.util.spec_from_file_location("phase2hRuntimeAdapter", MODULE_PATH)
assert spec is not None and spec.loader is not None
runtimeAdapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtimeAdapter
spec.loader.exec_module(runtimeAdapter)


def _writeVoice(directory: Path, **updates: object) -> tuple[Path, Path]:
	model = directory / "voice.onnx"
	model.write_bytes(b"model")
	configData: dict[str, object] = {
		"audio": {"sample_rate": 16_000},
		"num_speakers": 1,
		"speaker_id_map": {},
		"phoneme_type": "espeak",
		"piper_version": "1.0.0",
	}
	configData.update(updates)
	config = directory / "voice.onnx.json"
	config.write_text(json.dumps(configData), encoding="utf-8")
	return model, config


class ValidationTests(unittest.TestCase):
	def test_structured_results_are_immutable(self) -> None:
		metadata = runtimeAdapter.VoiceMetadata(16_000, 1, (), "espeak", "1.0.0")
		load = runtimeAdapter.LoadResult("1.5.0", 1.0, metadata, ("CPUExecutionProvider",))
		result = runtimeAdapter.SynthesisResult(0.1, 0.05, 16_000, 1, 2, 160, 320, 0.01, 10.0, 1)
		for value in (metadata, load, result):
			with self.assertRaises(FrozenInstanceError):
				value.sampleRate = 1  # type: ignore[attr-defined]

	def test_paths_config_and_language_neutral_metadata(self) -> None:
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			model, config = _writeVoice(Path(temporary), num_speakers=3, speaker_id_map={"arbitrary label": 2})
			validatedModel, validatedConfig, metadata = runtimeAdapter.validateVoiceFiles(model, config)
			self.assertEqual(model, validatedModel)
			self.assertEqual(config, validatedConfig)
			self.assertEqual((2,), metadata.speakerIds)
			self.assertEqual(3, metadata.numSpeakers)

	def test_invalid_paths_and_malformed_config_are_content_free(self) -> None:
		secret = "PRIVATE-SPEECH-CONTENT"
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			directory = Path(temporary)
			model, config = _writeVoice(directory)
			config.write_text(secret, encoding="utf-8")
			with self.assertRaises(runtimeAdapter.RuntimeAdapterError) as caught:
				runtimeAdapter.validateVoiceFiles(model, config)
			self.assertNotIn(secret, str(caught.exception))
			with self.assertRaises(runtimeAdapter.RuntimeAdapterError):
				runtimeAdapter.validateVoiceFiles(b"bad", config)

	def test_text_bounds_unicode_and_empty_input(self) -> None:
		text = "فارسی English e\u0301 \u200f"
		self.assertIs(text, runtimeAdapter.validateText(text))
		with self.assertRaisesRegex(runtimeAdapter.RuntimeAdapterError, "must not be empty"):
			runtimeAdapter.validateText("")
		with self.assertRaises(runtimeAdapter.RuntimeAdapterError):
			runtimeAdapter.validateText("x" * (runtimeAdapter.MAX_TEXT_CODE_POINTS + 1))

	def test_output_overwrite_is_explicit(self) -> None:
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			output = Path(temporary) / "out.wav"
			output.write_bytes(b"existing")
			with self.assertRaises(runtimeAdapter.RuntimeAdapterError) as caught:
				runtimeAdapter.validateOutputPath(output)
			self.assertEqual("outputExists", caught.exception.code)
			self.assertEqual(output, runtimeAdapter.validateOutputPath(output, overwrite=True))

	def test_wav_metadata_parser(self) -> None:
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			output = Path(temporary) / "valid.wav"
			with wave.open(str(output), "wb") as wavFile:
				wavFile.setparams((1, 2, 16_000, 4, "NONE", "not compressed"))
				wavFile.writeframes(b"\x00\x00" * 4)
			metadata = runtimeAdapter.inspectWav(output)
			self.assertEqual(4, metadata["frameCount"])
			self.assertEqual(16_000, metadata["sampleRate"])


class FakeChunk:
	audio_int16_bytes = b"\x00\x00" * 160


class FakeSession:
	def get_providers(self) -> list[str]:
		return ["CPUExecutionProvider"]


class FakeVoice:
	session = FakeSession()
	seenText: str | None = None

	@staticmethod
	def load(model: str, config_path: str, use_cuda: bool) -> "FakeVoice":
		return FakeVoice()

	def synthesize(self, text: str, syn_config: object) -> list[FakeChunk]:
		self.seenText = text
		return [FakeChunk()]


class AdapterTests(unittest.TestCase):
	def test_mocked_runtime_preserves_unicode_and_writes_wav(self) -> None:
		fakeModule = types.ModuleType("piper")
		fakeModule.PiperVoice = FakeVoice
		fakeModule.SynthesisConfig = lambda **kwargs: kwargs
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			directory = Path(temporary)
			model, config = _writeVoice(directory)
			output = directory / "output.wav"
			with patch.dict(sys.modules, {"piper": fakeModule}), patch.object(runtimeAdapter.importlib.metadata, "version", return_value="1.5.0"):
				adapter = runtimeAdapter.PiperRuntimeAdapter(model, config)
				result = adapter.synthesize("café فارسی e\u0301", output)
				self.assertEqual("café فارسی e\u0301", adapter._voice.seenText)
				self.assertEqual(160, result.frameCount)
				self.assertEqual(1, result.chunkCount)
				adapter.close()
				self.assertIsNone(adapter._voice)

	def test_runtime_version_is_exact(self) -> None:
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			model, config = _writeVoice(Path(temporary))
			adapter = runtimeAdapter.PiperRuntimeAdapter(model, config)
			with patch.object(runtimeAdapter.importlib.metadata, "version", return_value="1.4.2"):
				with self.assertRaises(runtimeAdapter.RuntimeAdapterError) as caught:
					adapter.load()
			self.assertEqual("runtimeVersionMismatch", caught.exception.code)

	@unittest.skipUnless(__import__("os").environ.get("PIPER_TEST_MODEL") and __import__("os").environ.get("PIPER_TEST_CONFIG"), "Set PIPER_TEST_MODEL and PIPER_TEST_CONFIG for local runtime validation")
	def test_supplied_runtime_and_model(self) -> None:
		import os
		with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
			adapter = runtimeAdapter.PiperRuntimeAdapter(os.environ["PIPER_TEST_MODEL"], os.environ["PIPER_TEST_CONFIG"])
			result = adapter.synthesize("Standalone runtime validation.", Path(temporary) / "runtime.wav")
			self.assertGreater(result.frameCount, 0)
			adapter.close()


class ScopeTests(unittest.TestCase):
	def test_adapter_has_no_network_or_locale_specific_control(self) -> None:
		source = MODULE_PATH.read_text(encoding="utf-8").lower()
		for forbidden in ("requests", "urllib", "socket", "http.client", "shell=true", "subprocess"):
			self.assertNotIn(forbidden, source)
		for localeToken in ("fa_ir", "en_us", "persian", "english"):
			self.assertNotIn(localeToken, source)


if __name__ == "__main__":
	unittest.main()
