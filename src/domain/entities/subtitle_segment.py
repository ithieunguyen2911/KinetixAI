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

    def ensure_word_timestamps(self) -> None:
        """Ensure per-word timestamps match self.text and [self.start_time, self.end_time]."""
        tokens = [t.strip() for t in self.text.split() if t.strip()]
        if not tokens:
            return
        existing_tokens = [w.word for w in self.words]
        bounds_valid = (
            bool(self.words)
            and abs(self.words[0].start_time - self.start_time) <= 0.5
            and abs(self.words[-1].end_time - self.end_time) <= 0.5
        )
        if existing_tokens == tokens and bounds_valid:
            return

        w_dur = (self.end_time - self.start_time) / len(tokens)
        self.words = [
            WordTimestamp(
                word=tok,
                start_time=round(self.start_time + idx * w_dur, 3),
                end_time=round(self.start_time + (idx + 1) * w_dur, 3),
            )
            for idx, tok in enumerate(tokens)
        ]

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
