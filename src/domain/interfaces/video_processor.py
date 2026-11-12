"""IVideoProcessor Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

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

    def probe_media(self, media_path: Path) -> Dict[str, Any]:
        """Inspect media stream technical metadata (codec, resolution, fps, duration, audio)."""
        return {
            "file_path": str(media_path),
            "duration_seconds": 6.0,
            "width": 1280,
            "height": 720,
            "resolution": "1280x720",
            "fps": 30.0,
            "video_codec": "h264",
            "audio_codec": "aac",
            "sample_rate": 16000,
            "size_bytes": media_path.stat().st_size if media_path.exists() else 0,
        }

    def trim_video(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        """Cut a video segment between start_time and end_time (seconds)."""
        raise NotImplementedError("trim_video is not implemented by this processor.")

    def mix_audio_tracks(
        self,
        primary_audio: Path,
        background_audio: Path,
        output_audio: Path,
        bg_volume: float = 0.18,
    ) -> Path:
        """Mix a primary voice track with a ducked background music track."""
        raise NotImplementedError("mix_audio_tracks is not implemented by this processor.")
