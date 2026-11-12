"""VideoProject Aggregate Root Domain Entity."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment


@dataclass
class VideoProject:
    """Aggregate root representing an automated video production project."""

    project_id: str
    source_url: str
    engine_type: RenderEngineType = RenderEngineType.REMOTION
    template_id: str = "CaptionTemplate"
    script_text: str | None = None
    raw_video_path: Path | None = None
    audio_path: Path | None = None
    overlay_video_path: Path | None = None
    subtitles: List[SubtitleSegment] = field(default_factory=list)
    final_output_path: Path | None = None
    status: JobStatus = JobStatus.PENDING
    progress_percent: int = 0
    current_step: str = "Ready"
    error_message: str | None = None

    def __post_init__(self) -> None:
        self.project_id = self.project_id.strip()
        self.source_url = self.source_url.strip()
        if not self.project_id:
            raise ValueError("VideoProject.project_id must not be empty.")
        if not self.source_url:
            raise ValueError("VideoProject.source_url must not be empty.")
        if isinstance(self.engine_type, str):
            self.engine_type = RenderEngineType(self.engine_type.lower())
        if isinstance(self.status, str):
            self.status = JobStatus(self.status.lower())
        if not (0 <= self.progress_percent <= 100):
            raise ValueError("VideoProject.progress_percent must be between 0 and 100.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_url": self.source_url,
            "engine_type": self.engine_type.value,
            "template_id": self.template_id,
            "script_text": self.script_text,
            "raw_video_path": str(self.raw_video_path) if self.raw_video_path else None,
            "audio_path": str(self.audio_path) if self.audio_path else None,
            "overlay_video_path": str(self.overlay_video_path) if self.overlay_video_path else None,
            "subtitles": [s.to_dict() for s in self.subtitles],
            "final_output_path": str(self.final_output_path) if self.final_output_path else None,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "error_message": self.error_message,
        }
