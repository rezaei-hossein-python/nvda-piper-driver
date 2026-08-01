"""Immutable Phase 2E speech-job value objects."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias


class ProsodyCommandType(Enum):
	RATE = "rate"
	PITCH = "pitch"
	VOLUME = "volume"


@dataclass(frozen=True, slots=True)
class TextItem:
	text: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class IndexItem:
	index: int


@dataclass(frozen=True, slots=True)
class CharacterModeItem:
	state: bool


@dataclass(frozen=True, slots=True)
class LanguageChangeItem:
	language: str | None


@dataclass(frozen=True, slots=True)
class BreakItem:
	durationMs: int


@dataclass(frozen=True, slots=True)
class ProsodyItem:
	commandType: ProsodyCommandType
	offset: int
	multiplier: int | float
	isDefault: bool


@dataclass(frozen=True, slots=True)
class PhonemeItem:
	ipa: str = field(repr=False)
	fallbackText: str | None = field(repr=False)


SpeechJobItem: TypeAlias = (
	TextItem | IndexItem | CharacterModeItem | LanguageChangeItem | BreakItem | ProsodyItem | PhonemeItem
)


@dataclass(frozen=True, slots=True)
class SpeechJob:
	jobId: int
	generationId: int
	requestNumber: int
	items: tuple[SpeechJobItem, ...]
	voiceId: str
	rate: int
