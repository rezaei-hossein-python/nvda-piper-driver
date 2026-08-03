"""Scenario driver boundary.

The production-safe default does not inject keys or execute arbitrary NVDA
code. A future disposable global-plugin adapter may implement the predefined
scenario names below; until then this command records an explicit blocked
result rather than claiming that speech was tested.
"""

from __future__ import annotations

import argparse
import json
import time


SCENARIOS = ("startup", "character", "editBox", "navigation", "document", "cancellation", "switching", "shutdown")


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--scenario", choices=SCENARIOS, required=True)
	parser.add_argument("--allow-plugin", action="store_true")
	args = parser.parse_args()
	if not args.allow_plugin:
		print(json.dumps({"scenario": args.scenario, "status": "blocked", "reason": "no approved NVDA test plugin is installed"}))
		return 3
	print(json.dumps({"scenario": args.scenario, "status": "not-implemented", "startedNs": time.monotonic_ns()}))
	return 4


if __name__ == "__main__":
	raise SystemExit(main())
