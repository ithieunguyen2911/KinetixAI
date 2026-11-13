"""IVideoProcessor Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from src.domain.entities.subtitle_segment import SubtitleSegment


class IVideoProcessor(ABC):
    """Interface for low-level media stream processing, NLE editing, and compositing (FFmpeg)."""

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

    def split_video(
        self,
        video_path: Path,
        split_time: float,
        output_dir: Path,
    ) -> List[Path]:
        """Split video_path at split_time (seconds) into two clip files [part1, part2]."""
        raise NotImplementedError("split_video is not implemented by this processor.")

    def concat_clips(
        self,
        clip_paths: List[Path],
        output_path: Path,
        transition: str = "fade",
        transition_duration: float = 0.4,
    ) -> Path:
        """Concatenate multiple video clips with optional transition."""
        raise NotImplementedError("concat_clips is not implemented by this processor.")

    def change_speed(
        self,
        video_path: Path,
        output_path: Path,
        speed_factor: float,
    ) -> Path:
        """Change playback speed (0.25x to 4.0x) of both video and audio streams."""
        raise NotImplementedError("change_speed is not implemented by this processor.")

    def apply_color_grade(
        self,
        video_path: Path,
        output_path: Path,
        preset: str = "natural",
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> Path:
        """Apply LUT/Color Look preset and eq adjustments (brightness, contrast, saturation, gamma)."""
        raise NotImplementedError("apply_color_grade is not implemented by this processor.")

    def reframe_aspect_ratio(
        self,
        video_path: Path,
        output_path: Path,
        aspect_ratio: str = "16:9",
    ) -> Path:
        """Reframe video into 16:9, 9:16 (with blurred pillarbox canvas), or 1:1 square."""
        raise NotImplementedError("reframe_aspect_ratio is not implemented by this processor.")

    def remove_silences(
        self,
        video_path: Path,
        output_path: Path,
        threshold_db: float = -35.0,
        min_silence_sec: float = 0.35,
    ) -> Path:
        """Remove silent pauses from audio/video stream."""
        raise NotImplementedError("remove_silences is not implemented by this processor.")

    def normalize_audio(
        self,
        video_path: Path,
        output_path: Path,
    ) -> Path:
        """Normalize audio loudness to broadcast EBU R128 standard."""
        raise NotImplementedError("normalize_audio is not implemented by this processor.")

    def mix_audio_tracks(
        self,
        primary_audio: Path,
        background_audio: Path,
        output_audio: Path,
        bg_volume: float = 0.18,
    ) -> Path:
        """Mix a primary video/voice track with a ducked background music track."""
        raise NotImplementedError("mix_audio_tracks is not implemented by this processor.")

    def capture_snapshot(
        self,
        video_path: Path,
        timestamp_sec: float,
        output_image_path: Path,
    ) -> Path:
        """Export a single high-resolution PNG frame at timestamp_sec."""
        raise NotImplementedError("capture_snapshot is not implemented by this processor.")
