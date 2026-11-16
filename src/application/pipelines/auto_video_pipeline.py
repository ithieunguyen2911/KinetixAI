"""AutoVideoPipeline - 5-Step Clean Architecture Orchestrator."""

from pathlib import Path
from typing import Callable

from src.domain.entities.enums import JobStatus
from src.domain.entities.studio_entities import StoryScene
from src.domain.entities.video_project import VideoProject
from src.domain.interfaces.media_downloader import IMediaDownloader
from src.domain.interfaces.transcriber import ITranscriber
from src.domain.interfaces.video_processor import IVideoProcessor
from src.domain.interfaces.visual_renderer import IVisualRenderer


ProgressCallback = Callable[[VideoProject], None]


class AutoVideoPipeline:
    """Orchestrator connecting all 5 media tools exclusively through Domain Interfaces (DIP)."""

    def __init__(
        self,
        downloader: IMediaDownloader,
        processor: IVideoProcessor,
        transcriber: ITranscriber,
        renderer: IVisualRenderer,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self.downloader = downloader
        self.processor = processor
        self.transcriber = transcriber
        self.renderer = renderer
        self.on_progress = on_progress

    def _notify(self, project: VideoProject, status: JobStatus, progress: int, step: str) -> None:
        project.status = status
        project.progress_percent = progress
        project.current_step = step
        if self.on_progress:
            self.on_progress(project)

    def execute(self, project: VideoProject, work_dir: Path) -> Path:
        """Execute the 5-step automated video production workflow."""
        work_dir.mkdir(parents=True, exist_ok=True)
        project.append_log("PIPELINE", "Start Pipeline", f"Source='{project.source_url}', Engine='{project.engine_type.value}', Template='{project.template_id}'")
        try:
            # Step 1: yt-dlp downloads or ingests source video
            self._notify(project, JobStatus.DOWNLOADING, 15, "Step 1/5: Downloading source video (yt-dlp)")
            project.raw_video_path = self.downloader.download(project.source_url, work_dir)
            project.append_log("INGEST", "Media Downloaded", f"Raw video saved at {project.raw_video_path.name}")

            # Step 2: FFmpeg extracts 16kHz mono WAV audio
            self._notify(project, JobStatus.EXTRACTING_AUDIO, 35, "Step 2/5: Extracting WAV audio (FFmpeg)")
            audio_target = work_dir / f"{project.project_id}_audio.wav"
            project.audio_path = self.processor.extract_audio(project.raw_video_path, audio_target)

            # Step 3: Whisper transcribes speech -> timestamped SubtitleSegments
            self._notify(project, JobStatus.TRANSCRIBING, 60, "Step 3/5: Transcribing subtitles (Whisper)")
            project.subtitles = self.transcriber.transcribe(
                project.audio_path,
                script_hint=project.script_text,
            )
            for seg in project.subtitles:
                seg.ensure_word_timestamps()

            # Auto-populate Storyboard Scenes from Subtitles if empty
            if not project.scenes and project.subtitles:
                default_char = project.characters[0].character_id if project.characters else "char_host"
                project.scenes = [
                    StoryScene(
                        scene_id=f"scene_{idx:02d}",
                        title=f"Scene {idx:02d}",
                        setting_context=project.scene_context.world_setting,
                        character_id=default_char,
                        narration_text=seg.text,
                        start_time=seg.start_time,
                        duration_sec=max(0.4, round(seg.end_time - seg.start_time, 3)),
                        transition_in=project.transition_preset,
                        animation_preset=project.animation_preset,
                        sfx_id="sfx_whoosh_fast" if idx == 1 else "sfx_pop_bubble",
                    )
                    for idx, seg in enumerate(project.subtitles, start=1)
                ]
            project.append_log("TRANSCRIBE", "Subtitles & Scenes Seeded", f"Generated {len(project.subtitles)} subtitle cues & {len(project.scenes)} scenes.")

            # Step 4: Remotion or HyperFrames renders visual overlay composition
            engine_label = project.engine_type.value.capitalize()
            self._notify(
                project,
                JobStatus.RENDERING_VISUALS,
                80,
                f"Step 4/5: Rendering motion graphics overlay ({engine_label})",
            )
            overlay_target = work_dir / f"{project.project_id}_overlay.mp4"
            probe_info = self.processor.probe_media(project.raw_video_path)
            raw_duration = float(probe_info.get("duration_seconds") or 6.0)
            project.ensure_timeline_clips(raw_duration)
            props = {
                "project_id": project.project_id,
                "engine": project.engine_type.value,
                "animation_preset": project.animation_preset,
                "scene_context": project.scene_context.to_dict(),
                "characters": [c.to_dict() for c in project.characters],
                "duration_seconds": raw_duration,
                "subtitles": [s.to_dict() for s in project.subtitles],
            }
            project.overlay_video_path = self.renderer.render_composition(
                project.template_id,
                props,
                overlay_target,
            )

            # Step 5: FFmpeg composites overlay + subtitles onto base video and exports MP4
            self._notify(project, JobStatus.MERGING, 92, "Step 5/5: Merging & exporting final MP4 (FFmpeg)")
            final_target = work_dir / f"{project.project_id}_final.mp4"
            project.final_output_path = self.processor.merge_and_export(
                project.raw_video_path,
                project.overlay_video_path,
                final_target,
                subtitles=project.subtitles,
            )

            project.append_log("PIPELINE", "Export Complete", f"Final MP4: {project.final_output_path.name}")
            self._notify(project, JobStatus.COMPLETED, 100, "Completed: Final MP4 exported")
            return project.final_output_path
        except Exception as exc:
            project.status = JobStatus.FAILED
            project.current_step = "Failed"
            project.error_message = str(exc)
            project.append_log("PIPELINE", "Pipeline Error", str(exc), status="ERROR")
            if self.on_progress:
                self.on_progress(project)
            raise
