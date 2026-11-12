"""Unit tests for Domain Layer Entities and Abstract Interfaces."""

from pathlib import Path
import pytest

from src.domain.entities import (
    JobStatus,
    MediaAsset,
    RenderEngineType,
    RenderJob,
    SubtitleSegment,
    VideoProject,
    WordTimestamp,
)
from src.domain.interfaces import (
    IMediaDownloader,
    ITranscriber,
    IVideoProcessor,
    IVisualRenderer,
)


def test_subtitle_segment_and_word_timestamp_validation() -> None:
    word = WordTimestamp(word=" KinetixAI ", start_time=0.0, end_time=0.8)
    assert word.word == "KinetixAI"
    seg = SubtitleSegment(start_time=0.0, end_time=2.5, text="  Hello Clean Architecture  ", words=[word])
    assert seg.text == "Hello Clean Architecture"
    assert seg.duration == 2.5
    data = seg.to_dict()
    assert data["text"] == "Hello Clean Architecture"
    assert len(data["words"]) == 1

    with pytest.raises(ValueError, match="must not be empty"):
        SubtitleSegment(start_time=0.0, end_time=1.0, text="   ")

    with pytest.raises(ValueError, match="must be >= 0.0"):
        SubtitleSegment(start_time=-0.1, end_time=1.0, text="Invalid")

    with pytest.raises(ValueError, match="must be > start_time"):
        SubtitleSegment(start_time=2.0, end_time=2.0, text="Invalid")


def test_media_asset_and_render_job_validation() -> None:
    asset = MediaAsset(asset_id="raw_01", file_path=Path("sample.mp4"), media_type="video", duration_seconds=5.0)
    assert asset.to_dict()["asset_id"] == "raw_01"

    with pytest.raises(ValueError, match="media_type"):
        MediaAsset(asset_id="bad", file_path=Path("x.mp4"), media_type="invalid")

    job = RenderJob(job_id="job_1", project_id="proj_1", engine_type=RenderEngineType.HYPERFRAMES)
    job.update_progress(JobStatus.TRANSCRIBING, 50, "Transcribing with Whisper")
    assert job.status == JobStatus.TRANSCRIBING
    assert job.progress_percent == 50

    job.mark_failed("Network timeout")
    assert job.status == JobStatus.FAILED
    assert job.error_message == "Network timeout"


def test_video_project_entity() -> None:
    project = VideoProject(
        project_id="proj_demo",
        source_url="demo://sample",
        engine_type=RenderEngineType.REMOTION,
    )
    assert project.project_id == "proj_demo"
    assert project.engine_type == RenderEngineType.REMOTION
    assert project.status == JobStatus.PENDING
    assert project.to_dict()["engine_type"] == "remotion"


def test_domain_interfaces_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        IMediaDownloader()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        ITranscriber()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IVisualRenderer()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IVideoProcessor()  # type: ignore[abstract]
