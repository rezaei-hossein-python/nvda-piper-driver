"""Content-free portable NVDA log analysis."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


FORBIDDEN_CONTENT_PATTERNS = ("speech text", "phoneme", "private fixture")
CRITICAL_PATTERNS = ("traceback", "watchdog", "critical", "restart limit", "worker failure")


def analyze(path: Path) -> dict[str, object]:
	if not path.is_file():
		return {"exists": False, "critical": [], "speechContentFound": False}
	text = path.read_text(encoding="utf-8", errors="replace")
	lower = text.lower()
	return {
		"exists": True,
		"lineCount": len(text.splitlines()),
		"critical": [pattern for pattern in CRITICAL_PATTERNS if pattern in lower],
		"speechContentFound": any(pattern in lower for pattern in FORBIDDEN_CONTENT_PATTERNS),
	}


if __name__ == "__main__":
	print(json.dumps(analyze(Path(sys.argv[1])), sort_keys=True))
