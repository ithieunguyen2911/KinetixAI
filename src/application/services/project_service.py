"""ProjectService - Application Service coordinating projects, repositories, and AutoVideoPipeline."""

from pathlib import Path
from typing import Any, Dict, List

from src.application.factories.renderer_factory import RendererFactory
from src.application.pipelines.auto_video_pipeline import AutoVideoPipeline
from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.entities.video_project import VideoProject
from src.domain.interfaces.media_downloader import IMediaDownloader
from src.domain.interfaces.transcriber import ITranscriber
from src.domain.interfaces.video_processor import IVideoProcessor
from src.infrastructure.downloaders.ytdlp_adapter import YtDlpAdapter
from src.infrastructure.processors.ffmpeg_adapter import FfmpegAdapter
from src.infrastructure.repositories.json_project_repository import JsonProjectRepository
from src.infrastructure.transcribers.whisper_adapter import WhisperAdapter


class ProjectService:
    """Application use-case service for managing and running VideoProjects."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        downloader: IMediaDownloader | None = None,
        processor: IVideoProcessor | None = None,
        transcriber: ITranscriber | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.workspace_root = workspace_root or (repo_root / "workspace")
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.repository = JsonProjectRepository(self.workspace_root / "projects.json")
        self.downloader = downloader or YtDlpAdapter()
        self.processor = processor or FfmpegAdapter()
        self.transcriber = transcriber or WhisperAdapter()

    def create_and_run_project(
        self,
        project_id: str,
        source_url: str,
        engine_type: RenderEngineType | str = RenderEngineType.REMOTION,
        template_id: str = "CaptionTemplate",
        script_text: str | None = None,
    ) -> VideoProject:
        """Create a VideoProject, run the 5-step pipeline, and persist every state update."""
        resolved_engine = (
            RenderEngineType(engine_type.lower())
            if isinstance(engine_type, str)
            else engine_type
        )
        project = VideoProject(
            project_id=project_id,
            source_url=source_url,
            engine_type=resolved_engine,
            template_id=template_id,
            script_text=script_text,
        )
        self.repository.save(project)

        renderer = RendererFactory.get_renderer(project.engine_type)
        pipeline = AutoVideoPipeline(
            downloader=self.downloader,
            processor=self.processor,
            transcriber=self.transcriber,
            renderer=renderer,
            on_progress=lambda p: self.repository.save(p),
        )
        project_dir = self.workspace_root / project.project_id
        pipeline.execute(project, project_dir)
        return self.repository.save(project)

    def update_subtitles_and_rerender(
        self,
        project_id: str,
        subtitles: List[SubtitleSegment],
        engine_type: RenderEngineType | str | None = None,
    ) -> VideoProject:
        """Update subtitles for an existing project and re-render steps 4 and 5."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        if not project.raw_video_path or not project.raw_video_path.exists():
            raise FileNotFoundError(f"Raw video missing for project: {project_id}")

        if engine_type is not None:
            project.engine_type = (
                RenderEngineType(engine_type.lower())
                if isinstance(engine_type, str)
                else engine_type
            )
        project.subtitles = subtitles
        project_dir = self.workspace_root / project.project_id
        renderer = RendererFactory.get_renderer(project.engine_type)

        project.status = JobStatus.RENDERING_VISUALS
        project.progress_percent = 80
        project.current_step = f"Re-rendering overlay ({project.engine_type.value})"
        self.repository.save(project)

        overlay_target = project_dir / f"{project.project_id}_overlay.mp4"
        props = {
            "project_id": project.project_id,
            "engine": project.engine_type.value,
            "subtitles": [s.to_dict() for s in project.subtitles],
        }
        project.overlay_video_path = renderer.render_composition(
            project.template_id,
            props,
            overlay_target,
        )

        project.status = JobStatus.MERGING
        project.progress_percent = 92
        project.current_step = "Merging updated overlay (FFmpeg)"
        self.repository.save(project)

        final_target = project_dir / f"{project.project_id}_final.mp4"
        project.final_output_path = self.processor.merge_and_export(
            project.raw_video_path,
            project.overlay_video_path,
            final_target,
            subtitles=project.subtitles,
        )

        project.status = JobStatus.COMPLETED
        project.progress_percent = 100
        project.current_step = "Completed: Updated MP4 exported"
        return self.repository.save(project)

    def probe_project_media(self, project_id: str) -> Dict[str, Any]:
        """Inspect technical stream specifications of a project's final MP4 using FfmpegAdapter.probe_media."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        target = project.final_output_path or project.raw_video_path
        if not target or not target.exists():
            raise FileNotFoundError(f"Media file not found for project: {project_id}")
        if isinstance(self.processor, FfmpegAdapter):
            return self.processor.probe_media(target)
        return {"file_path": str(target), "duration_seconds": 6.0}

    def trim_project_video(
        self,
        project_id: str,
        start_time: float,
        end_time: float,
    ) -> VideoProject:
        """Trim the final MP4 of a project between start_time and end_time using FFmpeg."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        if not isinstance(self.processor, FfmpegAdapter):
            raise RuntimeError("Processor does not support trimming.")

        trimmed_path = project.final_output_path.with_name(f"{project.project_id}_trimmed.mp4")
        self.processor.trim_video(project.final_output_path, trimmed_path, start_time, end_time)
        project.final_output_path = trimmed_path
        project.current_step = f"Trimmed ({start_time:.1f}s - {end_time:.1f}s)"
        return self.repository.save(project)

    def get_project(self, project_id: str) -> VideoProject | None:
        return self.repository.get(project_id)

    def list_projects(self) -> List[VideoProject]:
        return self.repository.list_all()
