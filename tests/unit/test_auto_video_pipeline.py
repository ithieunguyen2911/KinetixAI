"""Unit tests for AutoVideoPipeline using Mock/Fake Domain Interfaces (DIP verification)."""

from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.application.pipelines.auto_video_pipeline import AutoVideoPipeline
from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.entities.video_project import VideoProject
from src.domain.interfaces import (
    IMediaDownloader,
    ITranscriber,
    IVideoProcessor,
    IVisualRenderer,
)


class FakeDownloader(IMediaDownloader):
    def download(self, url: str, output_dir: Path) -> Path:
        p = output_dir / "fake_raw.mp4"
        p.write_bytes(b"fake_video")
        return p


class FakeProcessor(IVideoProcessor):
    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        output_audio.write_bytes(b"fake_wav")
        return output_audio

    def merge_and_export(
        self,
        base_video: Path,
        overlay_video: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment] | None = None,
    ) -> Path:
        output_path.write_bytes(b"fake_final_mp4")
        return output_path


class FakeTranscriber(ITranscriber):
    def transcribe(self, audio_path: Path, script_hint: str | None = None) -> List[SubtitleSegment]:
        return [
            SubtitleSegment(start_time=0.0, end_time=2.0, text="Unit Test Subtitle 1"),
            SubtitleSegment(start_time=2.0, end_time=4.0, text="Unit Test Subtitle 2"),
        ]


class FakeRenderer(IVisualRenderer):
    def __init__(self) -> None:
        self.last_template: str | None = None
        self.last_props: Dict[str, Any] | None = None

    def render_composition(self, template_id: str, props: Dict[str, Any], output_path: Path) -> Path:
        self.last_template = template_id
        self.last_props = props
        output_path.write_bytes(b"fake_overlay_mp4")
        return output_path


def test_auto_video_pipeline_orchestration_and_progress(tmp_path: Path) -> None:
    steps_seen: List[JobStatus] = []
    renderer = FakeRenderer()
    pipeline = AutoVideoPipeline(
        downloader=FakeDownloader(),
        processor=FakeProcessor(),
        transcriber=FakeTranscriber(),
        renderer=renderer,
        on_progress=lambda proj: steps_seen.append(proj.status),
    )

    project = VideoProject(
        project_id="unit_pipe_01",
        source_url="https://example.com/sample.mp4",
        engine_type=RenderEngineType.HYPERFRAMES,
    )
    final_path = pipeline.execute(project, tmp_path)

    assert final_path.exists()
    assert project.status == JobStatus.COMPLETED
    assert project.progress_percent == 100
    assert len(project.subtitles) == 2
    assert renderer.last_template == "CaptionTemplate"
    assert steps_seen == [
        JobStatus.DOWNLOADING,
        JobStatus.EXTRACTING_AUDIO,
        JobStatus.TRANSCRIBING,
        JobStatus.RENDERING_VISUALS,
        JobStatus.MERGING,
        JobStatus.COMPLETED,
    ]
