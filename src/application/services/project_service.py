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

    def inspect_source(self, source_url: str) -> Dict[str, Any]:
        """Inspect remote URL or local media file metadata via IMediaDownloader.extract_metadata."""
        meta = self.downloader.extract_metadata(source_url)
        # Enrich local file metadata with ffprobe if it's an existing local video file
        local_candidate = Path(source_url.strip().removeprefix("file://"))
        if local_candidate.exists() and local_candidate.is_file():
            try:
                probe = self.processor.probe_media(local_candidate)
                meta["duration"] = probe.get("duration_seconds", 0.0)
                meta["resolution"] = probe.get("resolution", "local")
                meta["fps"] = probe.get("fps", 30.0)
                meta["video_codec"] = probe.get("video_codec", "h264")
                meta["audio_codec"] = probe.get("audio_codec", "aac")
            except Exception:
                pass
        return meta

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
        template_id: str | None = None,
    ) -> VideoProject:
        """Update subtitles for an existing project, sync word timestamps, and re-render steps 4 and 5."""
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
        if template_id:
            project.template_id = template_id

        for seg in subtitles:
            seg.ensure_word_timestamps()
        project.subtitles = subtitles

        if project.audio_path and project.audio_path.exists():
            WhisperAdapter.export_transcript_json(
                project.subtitles,
                project.audio_path.with_suffix(".transcript.json"),
            )

        project_dir = self.workspace_root / project.project_id
        renderer = RendererFactory.get_renderer(project.engine_type)

        project.status = JobStatus.RENDERING_VISUALS
        project.progress_percent = 80
        project.current_step = f"Re-rendering overlay ({project.engine_type.value})"
        self.repository.save(project)

        probe_info = self.processor.probe_media(project.raw_video_path)
        raw_duration = float(probe_info.get("duration_seconds") or 6.0)

        overlay_target = project_dir / f"{project.project_id}_overlay.mp4"
        props = {
            "project_id": project.project_id,
            "engine": project.engine_type.value,
            "duration_seconds": raw_duration,
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
        """Inspect technical stream specifications of a project's final MP4 using IVideoProcessor.probe_media."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        target = project.final_output_path or project.raw_video_path
        if not target or not target.exists():
            raise FileNotFoundError(f"Media file not found for project: {project_id}")
        return self.processor.probe_media(target)

    def trim_project_video(
        self,
        project_id: str,
        start_time: float,
        end_time: float,
    ) -> VideoProject:
        """Trim the final MP4 of a project between start_time and end_time using IVideoProcessor.trim_video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        project_dir = self.workspace_root / project.project_id
        trimmed_target = project_dir / f"{project.project_id}_trimmed.mp4"
        source_video = project.final_output_path
        actual_trimmed = self.processor.trim_video(source_video, trimmed_target, start_time, end_time)
        project.final_output_path = actual_trimmed
        project.current_step = f"Trimmed ({start_time:.1f}s - {end_time:.1f}s)"
        return self.repository.save(project)

    def mix_project_audio(
        self,
        project_id: str,
        background_audio_path: Path,
        bg_volume: float = 0.20,
    ) -> VideoProject:
        """Mix background audio/music into the project's final MP4 using IVideoProcessor.mix_audio_tracks."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        project_dir = self.workspace_root / project.project_id
        mixed_target = project_dir / f"{project.project_id}_mixed.mp4"
        actual_mixed = self.processor.mix_audio_tracks(
            project.final_output_path,
            background_audio_path,
            mixed_target,
            bg_volume=bg_volume,
        )
        project.final_output_path = actual_mixed
        project.current_step = f"Audio Mixed (bg volume {int(bg_volume * 100)}%)"
        return self.repository.save(project)

    def change_project_speed(self, project_id: str, speed_factor: float) -> VideoProject:
        """Change playback speed (0.25x to 4.0x) of a project's active video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        target = project_dir / f"{project.project_id}_speed.mp4"
        actual = self.processor.change_speed(project.final_output_path, target, speed_factor)
        project.final_output_path = actual
        project.current_step = f"Speed Adjusted ({speed_factor:.2f}x)"
        return self.repository.save(project)

    def apply_project_color_grade(
        self,
        project_id: str,
        preset: str = "natural",
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> VideoProject:
        """Apply LUT / Color Look preset and eq parameters to a project's active video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        target = project_dir / f"{project.project_id}_graded.mp4"
        actual = self.processor.apply_color_grade(
            project.final_output_path,
            target,
            preset=preset,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            gamma=gamma,
        )
        project.final_output_path = actual
        project.current_step = f"Color Graded ({preset})"
        return self.repository.save(project)

    def reframe_project_video(self, project_id: str, aspect_ratio: str = "16:9") -> VideoProject:
        """Reframe a project's active video into 16:9, 9:16 (vertical Shorts blur-pad), or 1:1."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        safe_tag = aspect_ratio.replace(":", "x")
        target = project_dir / f"{project.project_id}_{safe_tag}.mp4"
        actual = self.processor.reframe_aspect_ratio(project.final_output_path, target, aspect_ratio)
        project.final_output_path = actual
        project.current_step = f"Reframed ({aspect_ratio})"
        return self.repository.save(project)

    def master_project_audio(
        self,
        project_id: str,
        remove_silence: bool = False,
        normalize_loudness: bool = True,
        mix_bgm: bool = False,
        bgm_source: str = "demo://bgm",
        bg_volume: float = 0.18,
    ) -> VideoProject:
        """Execute NLE audio post-processing (Silence Cut, EBU R128 Loudness Normalization, BGM Ducking Mix)."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        current_video = project.final_output_path
        steps_applied: List[str] = []

        if remove_silence:
            silence_target = project_dir / f"{project.project_id}_desilenced.mp4"
            current_video = self.processor.remove_silences(current_video, silence_target)
            steps_applied.append("Silence Cut")

        if normalize_loudness:
            norm_target = project_dir / f"{project.project_id}_normalized.mp4"
            current_video = self.processor.normalize_audio(current_video, norm_target)
            steps_applied.append("EBU R128 Normalized")

        if mix_bgm:
            bgm_path = (
                self.downloader.download("demo://bgm", project_dir)
                if bgm_source.strip().lower() == "demo://bgm"
                else Path(bgm_source)
            )
            mix_target = project_dir / f"{project.project_id}_bgm_mixed.mp4"
            current_video = self.processor.mix_audio_tracks(
                current_video,
                bgm_path,
                mix_target,
                bg_volume=bg_volume,
            )
            steps_applied.append(f"BGM Mixed ({int(bg_volume * 100)}%)")

        project.final_output_path = current_video
        summary = " + ".join(steps_applied) if steps_applied else "Audio Inspected"
        project.current_step = f"Audio Mastered: {summary}"
        return self.repository.save(project)

    def capture_project_snapshot(self, project_id: str, timestamp_sec: float = 1.0) -> Dict[str, Any]:
        """Capture a PNG frame snapshot from the project's active video at timestamp_sec."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        snap_name = f"{project.project_id}_frame_{int(timestamp_sec * 100):05d}.png"
        snap_path = project_dir / snap_name
        out_img = self.processor.capture_snapshot(project.final_output_path, timestamp_sec, snap_path)
        return {
            "project_id": project.project_id,
            "timestamp_sec": round(float(timestamp_sec), 3),
            "snapshot_path": str(out_img),
        }

    def get_project(self, project_id: str) -> VideoProject | None:
        return self.repository.get(project_id)

    def list_projects(self) -> List[VideoProject]:
        return self.repository.list_all()
