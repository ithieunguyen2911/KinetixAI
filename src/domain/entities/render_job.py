"""RenderJob Domain Entity."""

from dataclasses import dataclass
from typing import Any, Dict

from src.domain.entities.enums import JobStatus, RenderEngineType


@dataclass
class RenderJob:
    """Tracks the execution state of an automated video production run."""

    job_id: str
    project_id: str
    engine_type: RenderEngineType = RenderEngineType.REMOTION
    status: JobStatus = JobStatus.PENDING
    progress_percent: int = 0
    current_step: str = "Initialized"
    error_message: str | None = None

    def __post_init__(self) -> None:
        self.job_id = self.job_id.strip()
        self.project_id = self.project_id.strip()
        if not self.job_id:
            raise ValueError("RenderJob.job_id must not be empty.")
        if not self.project_id:
            raise ValueError("RenderJob.project_id must not be empty.")
        if not (0 <= self.progress_percent <= 100):
            raise ValueError("RenderJob.progress_percent must be between 0 and 100.")

    def update_progress(self, status: JobStatus, progress_percent: int, current_step: str) -> None:
        """Update job lifecycle state and progress percentage."""
        if not (0 <= progress_percent <= 100):
            raise ValueError("progress_percent must be between 0 and 100.")
        self.status = status
        self.progress_percent = progress_percent
        self.current_step = current_step

    def mark_failed(self, error_message: str) -> None:
        """Transition job into FAILED status with error context."""
        self.status = JobStatus.FAILED
        self.current_step = "Failed"
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "engine_type": self.engine_type.value,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "error_message": self.error_message,
        }
