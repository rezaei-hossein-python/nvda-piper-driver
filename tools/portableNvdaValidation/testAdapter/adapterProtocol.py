"""Restricted localhost protocol shared by the disposable NVDA adapter."""
from __future__ import annotations
import json
import secrets
from typing import Final

MAX_MESSAGE_BYTES: Final = 4096
MAX_COMMANDS: Final = 256
COMMAND_FIELDS: dict[str, frozenset[str]] = {
	"ping": frozenset({"id", "runId", "token", "command"}), "getStatus": frozenset({"id", "runId", "token", "command"}),
	"selectSynth": frozenset({"id", "runId", "token", "command", "name"}),
	"focusFixture": frozenset({"id", "runId", "token", "command", "fixture"}),
	"typeFixture": frozenset({"id", "runId", "token", "command", "fixture"}),
	"navigateFixture": frozenset({"id", "runId", "token", "command", "fixture"}),
	"startReadAll": frozenset({"id", "runId", "token", "command", "fixture"}),
	"cancelSpeech": frozenset({"id", "runId", "token", "command"}), "switchToEspeak": frozenset({"id", "runId", "token", "command"}),
	"switchToPiper": frozenset({"id", "runId", "token", "command"}), "getMetrics": frozenset({"id", "runId", "token", "command"}),
	"shutdownNvda": frozenset({"id", "runId", "token", "command"}),
}
FIXTURES: Final = frozenset({"lowercaseCharacter", "uppercaseCharacter", "digit", "punctuation", "repeatedCharacter", "shortWord", "rapidCharacters", "characterNavigation", "wordNavigation", "lineNavigation", "controlNavigation", "editBoxWorkflow", "multiParagraphDocument", "readAllDocument", "cancellationScenario"})

class ProtocolError(ValueError):
	pass

def newToken() -> str:
	return secrets.token_urlsafe(32)

def parseRequest(raw: bytes, expectedRunId: str, expectedToken: str, seenIds: set[int]) -> dict[str, object]:
	if len(raw) > MAX_MESSAGE_BYTES:
		raise ProtocolError("message-too-large")
	try:
		request = json.loads(raw.decode("utf-8"))
	except (UnicodeDecodeError, json.JSONDecodeError) as error:
		raise ProtocolError("malformed-json") from error
	if type(request) is not dict:
		raise ProtocolError("request-not-object")
	command = request.get("command")
	if command not in COMMAND_FIELDS or set(request) != COMMAND_FIELDS[command]:
		raise ProtocolError("invalid-command-schema")
	identifier = request.get("id")
	if type(identifier) is not int or not 1 <= identifier <= MAX_COMMANDS or identifier in seenIds:
		raise ProtocolError("invalid-or-duplicate-id")
	if request.get("token") != expectedToken:
		raise ProtocolError("authentication-failed")
	if request.get("runId") != expectedRunId:
		raise ProtocolError("run-id-failed")
	if command in {"focusFixture", "typeFixture", "navigateFixture", "startReadAll"} and request.get("fixture") not in FIXTURES:
		raise ProtocolError("invalid-fixture")
	if command == "selectSynth" and request.get("name") not in {"nvdaPiperDriver", "espeak"}:
		raise ProtocolError("invalid-synth")
	seenIds.add(identifier)
	return request
