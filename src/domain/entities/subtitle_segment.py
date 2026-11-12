"""Subtitle and Word Timestamp Domain Entities."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class WordTimestamp:
    """Represents a single spoken word with millisecond-accurate timestamps."""

    word: str
    start_time: float
    end_time: float

    def __post_init__(self) -> None:
        self.word = self.word.strip()
        if not self.word:
            raise ValueError("WordTimestamp.word must not be empty.")
        if self.start_time < 0.0:
            raise ValueError("WordTimestamp.start_time must be >= 0.0.")
        if self.end_time < self.start_time:
            raise ValueError("WordTimestamp.end_time must be >= start_time.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start_time": round(float(self.start_time), 3),
            "end_time": round(float(self.end_time), 3),
        }


@dataclass
class SubtitleSegment:
    """Represents a timed subtitle caption segment."""

    start_time: float
    end_time: float
    text: str
    words: List[WordTimestamp] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.text = self.text.strip()
        if not self.text:
            raise ValueError("SubtitleSegment.text must not be empty.")
        if self.start_time < 0.0:
            raise ValueError("SubtitleSegment.start_time must be >= 0.0.")
        if self.end_time <= self.start_time:
            raise ValueError("SubtitleSegment.end_time must be > start_time.")

    @property
    def duration(self) -> float:
        """Duration of the subtitle segment in seconds."""
        return round(self.end_time - self.start_time, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": round(float(self.start_time), 3),
            "end_time": round(float(self.end_time), 3),
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
        }
