# NVDA Piper Driver
# Copyright (C) 2026 Hosein Rezaei
# This file is covered by the GNU General Public License v2 or later.
# See LICENSE for details.

import synthDriverHandler


class SynthDriver(synthDriverHandler.SynthDriver):
	"""Unavailable Phase 2B synthesizer driver."""

	name = "nvdaPiperDriver"
	description = "NVDA Piper Driver"

	@classmethod
	def check(cls) -> bool:
		"""Remain unavailable until controlled mock discovery is implemented in Phase 2C."""
		return False

	def speak(self, speechSequence) -> None:
		"""Reject an unexpected call because this driver cannot be selected."""
		raise RuntimeError("The unavailable NVDA Piper Driver cannot speak")
