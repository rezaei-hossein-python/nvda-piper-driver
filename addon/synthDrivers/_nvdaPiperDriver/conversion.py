"""Pure conversion from pinned NVDA speech sequences to immutable jobs."""

from speech import commands

from .jobs import (
	BreakItem,
	CharacterModeItem,
	IndexItem,
	LanguageChangeItem,
	PhonemeItem,
	ProsodyCommandType,
	ProsodyItem,
	SpeechJob,
	SpeechJobItem,
	TextItem,
)


_MAX_IDENTIFIER = (1 << 63) - 1


class UnsupportedSpeechItemError(Exception):
	"""Raised when an item is not part of the Phase 2E driver-facing contract."""


def _unsupportedItem(item: object) -> UnsupportedSpeechItemError:
	itemType = type(item)
	return UnsupportedSpeechItemError(
		f"Unsupported speech item type: {itemType.__module__}.{itemType.__qualname__}",
	)


def _requireExactAttribute(item: object, name: str, expectedTypes: tuple[type, ...]):
	try:
		value = object.__getattribute__(item, name)
	except AttributeError:
		raise ValueError(f"Malformed {type(item).__name__}: missing {name}") from None
	if type(value) not in expectedTypes:
		raise TypeError(f"Malformed {type(item).__name__}: invalid {name} type")
	return value


def _convertProsody(item: object, commandType: ProsodyCommandType) -> ProsodyItem:
	offset = _requireExactAttribute(item, "_offset", (int,))
	multiplier = _requireExactAttribute(item, "_multiplier", (int, float))
	isDefault = _requireExactAttribute(item, "isDefault", (bool,))
	if offset != 0 and multiplier != 1:
		raise ValueError(f"Malformed {type(item).__name__}: conflicting prosody values")
	if isDefault is not (offset == 0 and multiplier == 1):
		raise ValueError(f"Malformed {type(item).__name__}: inconsistent default state")
	return ProsodyItem(commandType, offset, multiplier, isDefault)


def _convertItem(item: object) -> SpeechJobItem:
	itemType = type(item)
	if itemType is str:
		return TextItem(item)
	if itemType is commands.IndexCommand:
		return IndexItem(_requireExactAttribute(item, "index", (int,)))
	if itemType is commands.CharacterModeCommand:
		state = _requireExactAttribute(item, "state", (bool,))
		isDefault = _requireExactAttribute(item, "isDefault", (bool,))
		if isDefault is not (not state):
			raise ValueError("Malformed CharacterModeCommand: inconsistent default state")
		return CharacterModeItem(state)
	if itemType is commands.LangChangeCommand:
		language = _requireExactAttribute(item, "lang", (str, type(None)))
		isDefault = _requireExactAttribute(item, "isDefault", (bool,))
		if isDefault is not (not language):
			raise ValueError("Malformed LangChangeCommand: inconsistent default state")
		return LanguageChangeItem(language)
	if itemType is commands.BreakCommand:
		return BreakItem(_requireExactAttribute(item, "time", (int,)))
	if itemType is commands.RateCommand:
		return _convertProsody(item, ProsodyCommandType.RATE)
	if itemType is commands.PitchCommand:
		return _convertProsody(item, ProsodyCommandType.PITCH)
	if itemType is commands.VolumeCommand:
		return _convertProsody(item, ProsodyCommandType.VOLUME)
	if itemType is commands.PhonemeCommand:
		ipa = _requireExactAttribute(item, "ipa", (str,))
		fallbackText = _requireExactAttribute(item, "text", (str, type(None)))
		return PhonemeItem(ipa, fallbackText)
	raise _unsupportedItem(item)


class SpeechJobConverter:
	"""Own deterministic, instance-local identifiers and no speech content."""

	def __init__(self) -> None:
		self._nextJobId = 1
		self._nextGenerationId = 1
		self._nextRequestNumber = 1

	def convert(self, speechSequence: list[object], *, voiceId: str, rate: int) -> SpeechJob:
		if type(speechSequence) is not list:
			raise TypeError("speechSequence must be a list")
		if type(voiceId) is not str or not voiceId:
			raise ValueError("active voice ID is invalid")
		if type(rate) is not int:
			raise TypeError("active rate must be an integer")
		if not 0 <= rate <= 100:
			raise ValueError("active rate must be between 0 and 100")

		items = tuple(_convertItem(item) for item in speechSequence)
		if max(self._nextJobId, self._nextGenerationId, self._nextRequestNumber) > _MAX_IDENTIFIER:
			raise OverflowError("speech job identifier space exhausted")

		job = SpeechJob(
			jobId=self._nextJobId,
			generationId=self._nextGenerationId,
			requestNumber=self._nextRequestNumber,
			items=items,
			voiceId=voiceId,
			rate=rate,
		)
		self._nextJobId += 1
		self._nextGenerationId += 1
		self._nextRequestNumber += 1
		return job
