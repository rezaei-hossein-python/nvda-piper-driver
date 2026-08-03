"""Security and schema tests for the disposable NVDA adapter."""

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "tools" / "portableNvdaValidation" / "testAdapter" / "adapterProtocol.py"
spec = importlib.util.spec_from_file_location("adapterProtocol", source)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class AdapterProtocolTests(unittest.TestCase):
	def request(self, command: str, **fields: object) -> bytes:
		data = {"id": 1, "runId": "run", "token": "secret", "command": command, **fields}
		import json
		return json.dumps(data).encode()

	def test_valid_ping_and_duplicate_rejection(self) -> None:
		seen: set[int] = set()
		self.assertEqual("ping", module.parseRequest(self.request("ping"), "run", "secret", seen)["command"])
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(self.request("ping"), "run", "secret", seen)

	def test_wrong_token_unknown_fields_and_code_payload_rejected(self) -> None:
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(self.request("ping"), "run", "wrong", set())
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(self.request("ping", code="import os"), "run", "secret", set())

	def test_fixture_and_synth_allowlists(self) -> None:
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(self.request("typeFixture", fixture="arbitraryText"), "run", "secret", set())
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(self.request("selectSynth", name="python"), "run", "secret", set())

	def test_size_limit(self) -> None:
		with self.assertRaises(module.ProtocolError):
			module.parseRequest(b"x" * (module.MAX_MESSAGE_BYTES + 1), "run", "secret", set())


if __name__ == "__main__":
	unittest.main()
