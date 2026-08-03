"""Disposable authenticated NVDA global-plugin adapter.

Copied only into a harness-owned portable configuration. It accepts fixed
commands and fixture categories and never evaluates code or speech text.
"""
from __future__ import annotations
import json
import os
import socket
import threading
from pathlib import Path
try:
	import globalPluginHandler
except ImportError:
	globalPluginHandler = None
from adapterProtocol import parseRequest

class _PluginBase:
	def __init__(self) -> None:
		self._stop = threading.Event(); self._server = None; self._thread = None
		self._token = os.environ.get("NVDA_PIPER_VALIDATION_TOKEN", "")
		self._runId = os.environ.get("NVDA_PIPER_VALIDATION_RUN_ID", "")
		self._state = {"ready": False, "selectedSynth": None, "events": []}
		marker = Path(os.environ.get("NVDA_PIPER_VALIDATION_CONFIG_MARKER", ""))
		owned = False
		try:
			owned = marker.read_text(encoding="utf-8") == '{"owner": "nvda-piper-phase2l-harness-v1"}'
		except (OSError, UnicodeError):
			owned = False
		if os.environ.get("NVDA_PIPER_VALIDATION_ADAPTER") != "1" or not os.environ.get("NVDA_PIPER_VALIDATION_RUN_ID") or not self._token or not owned:
			return
		portFile = os.environ.get("NVDA_PIPER_VALIDATION_PORT_FILE")
		if not portFile:
			return
		self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._server.bind(("127.0.0.1", 0)); self._server.listen(1); self._server.settimeout(0.25)
		with open(portFile, "w", encoding="ascii") as stream: stream.write(str(self._server.getsockname()[1]))
		self._state["ready"] = True
		self._thread = threading.Thread(target=self._serve, name="nvdaValidationAdapter", daemon=True); self._thread.start()

	def _serve(self) -> None:
		seen: set[int] = set()
		while not self._stop.is_set() and self._server is not None:
			try: client, _ = self._server.accept()
			except socket.timeout: continue
			with client:
				try:
					size = int.from_bytes(client.recv(4), "little")
					if size <= 0 or size > 4096: raise ValueError("invalid-frame")
					request = parseRequest(client.recv(size), self._runId, self._token, seen); response = self._dispatch(request)
				except Exception as error: response = {"ok": False, "error": type(error).__name__}
				encoded = json.dumps(response, separators=(",", ":"), sort_keys=True).encode("utf-8")
				client.sendall(len(encoded).to_bytes(4, "little") + encoded)

	def _dispatch(self, request: dict[str, object]) -> dict[str, object]:
		command = request["command"]
		if command == "ping": return {"ok": True, "ready": self._state["ready"]}
		if command == "getStatus": return {"ok": True, **self._state}
		if command == "getMetrics": return {"ok": True, "events": tuple(self._state["events"])}
		if command in {"selectSynth", "switchToEspeak", "switchToPiper"}:
			self._state["selectedSynth"] = "espeak" if command == "switchToEspeak" else ("nvdaPiperDriver" if command == "switchToPiper" else request["name"])
			return {"ok": True, "selectedSynth": self._state["selectedSynth"]}
		if command == "cancelSpeech": self._state["events"].append({"event": "cancel"}); return {"ok": True}
		if command == "shutdownNvda": self._stop.set(); return {"ok": True}
		return {"ok": False, "error": "fixture-adapter-not-verified"}

	def terminate(self) -> None:
		self._stop.set()
		if self._server is not None: self._server.close(); self._server = None

if globalPluginHandler is not None:
	class GlobalPlugin(globalPluginHandler.GlobalPlugin, _PluginBase):
		def __init__(self): _PluginBase.__init__(self)
		def terminate(self): _PluginBase.terminate(self); globalPluginHandler.GlobalPlugin.terminate(self)
else:
	GlobalPlugin = _PluginBase
