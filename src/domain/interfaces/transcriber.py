"""ITranscriber Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from src.domain.entities.subtitle_segment import SubtitleSegment


class ITranscriber(ABC):
    """Interface for speech-to-text audio transcription."""

    @abstractmethod
    def transcribe(self, audio_path: Path, script_hint: str | None = None) -> List[SubtitleSegment]:
        """Transcribe an audio file into timestamped SubtitleSegment items."""
        pass
