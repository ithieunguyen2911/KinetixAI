"""IVideoProcessor Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from src.domain.entities.subtitle_segment import SubtitleSegment


class IVideoProcessor(ABC):
    """Interface for low-level media stream processing and compositing (FFmpeg)."""

    @abstractmethod
    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract WAV audio track from video_path into output_audio."""
        pass

    @abstractmethod
    def merge_and_export(
        self,
        base_video: Path,
        overlay_video: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment] | None = None,
    ) -> Path:
        """Merge base_video with overlay_video (and optional subtitle stream) into output_path."""
        pass
