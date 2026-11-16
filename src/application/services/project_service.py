"""ProjectService - Application Service coordinating projects, repositories, and AutoVideoPipeline."""

from copy import deepcopy
from pathlib import Path
import shutil
from typing import Any, Dict, List
import uuid

from src.application.factories.renderer_factory import RendererFactory
from src.application.pipelines.auto_video_pipeline import AutoVideoPipeline
from src.domain.entities.enums import (
    AnimationPreset,
    JobStatus,
    RenderEngineType,
    StorytellingGenre,
    TransitionPreset,
)
from src.domain.entities.studio_entities import (
    CharacterProfile,
    PodcastTurn,
    SceneContext,
    StoryScene,
    TimelineClip,
)
from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.entities.video_project import VideoProject
from src.domain.interfaces.audio_library import IAudioAssetLibrary
from src.domain.interfaces.media_downloader import IMediaDownloader
from src.domain.interfaces.transcriber import ITranscriber
from src.domain.interfaces.video_processor import IVideoProcessor
from src.domain.interfaces.voice_synthesizer import IVoiceSynthesizer
from src.infrastructure.audio.audio_library_adapter import StudioAudioLibraryAdapter
from src.infrastructure.downloaders.ytdlp_adapter import YtDlpAdapter
from src.infrastructure.processors.ffmpeg_adapter import FfmpegAdapter
from src.infrastructure.repositories.json_project_repository import JsonProjectRepository
from src.infrastructure.transcribers.whisper_adapter import WhisperAdapter
from src.infrastructure.tts.tts_voice_adapter import TtsVoiceAdapter


class ProjectService:
    """Application use-case service for managing and running VideoProjects."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        downloader: IMediaDownloader | None = None,
        processor: IVideoProcessor | None = None,
        transcriber: ITranscriber | None = None,
        voice_synthesizer: IVoiceSynthesizer | None = None,
        audio_library: IAudioAssetLibrary | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.workspace_root = workspace_root or (repo_root / "workspace")
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.repository = JsonProjectRepository(self.workspace_root / "projects.json")
        self.downloader = downloader or YtDlpAdapter()
        self.processor = processor or FfmpegAdapter()
        self.transcriber = transcriber or WhisperAdapter()
        self.voice_synthesizer = voice_synthesizer or TtsVoiceAdapter()
        self.audio_library = audio_library or StudioAudioLibraryAdapter()

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
            "animation_preset": project.animation_preset,
            "scene_context": project.scene_context.to_dict(),
            "characters": [c.to_dict() for c in project.characters],
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
        project.append_log(
            "SUBTITLE",
            "Re-Render Subtitles",
            f"Updated {len(project.subtitles)} cues ({project.engine_type.value} / {project.template_id}).",
        )
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
        project.append_log("NLE", "Speed Ramp", f"Adjusted playback speed to {speed_factor:.2f}x.")
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
        project.append_log(
            "COLOR",
            f"Color Grade ({preset})",
            f"B={brightness:.2f}, C={contrast:.2f}, S={saturation:.2f}",
        )
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
        project.append_log("NLE", "Aspect Reframe", f"Converted frame geometry to {aspect_ratio}.")
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
        project.append_log("AUDIO", "Audio Master", summary)
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
        project.append_log("NLE", "Snapshot PNG", f"Captured frame at {timestamp_sec:.2f}s -> {out_img.name}")
        self.repository.save(project)
        return {
            "project_id": project.project_id,
            "timestamp_sec": round(float(timestamp_sec), 3),
            "snapshot_path": str(out_img),
        }

    def split_project_video(self, project_id: str, split_time: float) -> Dict[str, Any]:
        """Split a project's active video into two clips (partA, partB) at split_time."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")
        project_dir = self.workspace_root / project.project_id
        splits_dir = project_dir / "splits"
        part_a, part_b = self.processor.split_video(project.final_output_path, split_time, splits_dir)
        project.current_step = f"Video Split at {split_time:.2f}s"
        self.repository.save(project)
        return {
            "project_id": project.project_id,
            "split_time": round(float(split_time), 3),
            "part_a_path": str(part_a),
            "part_b_path": str(part_b),
        }

    def concat_project_clips(
        self,
        project_id: str,
        clip_paths: List[str],
        transition: str = "none",
    ) -> VideoProject:
        """Concatenate multiple video clips into the project's active video."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        project_dir = self.workspace_root / project.project_id
        target = project_dir / f"{project.project_id}_concat.mp4"
        paths = [Path(p) for p in clip_paths]
        actual = self.processor.concat_clips(paths, target, transition=transition)
        project.final_output_path = actual
        project.current_step = f"Clips Concatenated ({len(paths)} clips)"
        return self.repository.save(project)

    def split_subtitle_cue(self, project_id: str, split_time: float) -> VideoProject:
        """Razor-split the subtitle cue spanning split_time into two consecutive cues."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        new_subs: List[SubtitleSegment] = []
        split_done = False
        for seg in project.subtitles:
            if not split_done and (seg.start_time + 0.15) < split_time < (seg.end_time - 0.15):
                words = [w for w in seg.text.split(" ") if w.strip()]
                if len(words) >= 2:
                    mid = len(words) // 2
                    text_a = " ".join(words[:mid])
                    text_b = " ".join(words[mid:])
                else:
                    text_a = seg.text + " (1)"
                    text_b = seg.text + " (2)"
                seg_a = SubtitleSegment(start_time=seg.start_time, end_time=round(split_time, 3), text=text_a)
                seg_b = SubtitleSegment(start_time=round(split_time, 3), end_time=seg.end_time, text=text_b)
                seg_a.ensure_word_timestamps()
                seg_b.ensure_word_timestamps()
                new_subs.extend([seg_a, seg_b])
                split_done = True
            else:
                new_subs.append(seg)
        project.subtitles = new_subs
        project.current_step = f"Subtitle Cue Split at {split_time:.2f}s"
        return self.repository.save(project)

    def export_project_subtitles(self, project_id: str, fmt: str = "srt") -> Dict[str, Any]:
        """Export project subtitles into .srt, .vtt, or .transcript.json format."""
        import json

        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        project_dir = self.workspace_root / project.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        norm_fmt = fmt.strip().lower().lstrip(".")

        def _fmt_time(seconds: float, sep: str = ",") -> str:
            ms = int(round((seconds % 1) * 1000))
            total_s = int(seconds)
            s = total_s % 60
            m = (total_s // 60) % 60
            h = total_s // 3600
            return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

        if norm_fmt == "vtt":
            out_path = project_dir / f"{project.project_id}.vtt"
            lines = ["WEBVTT", ""]
            for idx, seg in enumerate(project.subtitles, start=1):
                lines.append(str(idx))
                lines.append(f"{_fmt_time(seg.start_time, '.')} --> {_fmt_time(seg.end_time, '.')}")
                lines.append(seg.text)
                lines.append("")
            out_path.write_text("\n".join(lines), encoding="utf-8")
        elif norm_fmt in ("json", "transcript.json"):
            out_path = project_dir / f"{project.project_id}.transcript.json"
            payload = {
                "project_id": project.project_id,
                "segments": [s.to_dict() for s in project.subtitles],
            }
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            out_path = project_dir / f"{project.project_id}.srt"
            lines = []
            for idx, seg in enumerate(project.subtitles, start=1):
                lines.append(str(idx))
                lines.append(f"{_fmt_time(seg.start_time, ',')} --> {_fmt_time(seg.end_time, ',')}")
                lines.append(seg.text)
                lines.append("")
            out_path.write_text("\n".join(lines), encoding="utf-8")

        return {
            "project_id": project.project_id,
            "format": norm_fmt,
            "export_path": str(out_path),
            "cue_count": len(project.subtitles),
        }

    def get_project(self, project_id: str) -> VideoProject | None:
        proj = self.repository.get(project_id)
        if proj and not proj.timeline_clips:
            proj.ensure_timeline_clips(max(6.0, proj.subtitles[-1].end_time if proj.subtitles else 6.0))
        return proj

    def list_projects(self) -> List[VideoProject]:
        items = self.repository.list_all()
        for proj in items:
            if not proj.timeline_clips:
                proj.ensure_timeline_clips(max(6.0, proj.subtitles[-1].end_time if proj.subtitles else 6.0))
        return items

    # ==========================================================
    # v3.0 STUDIO CRUD, CLONE, CONTEXT, CHARACTER, AUDIO & BEAT
    # ==========================================================

    def get_studio_catalog(self) -> Dict[str, Any]:
        """Return all curated voices, custom cloned/designed voices, BGM, SFX, genres, transitions & animations."""
        return {
            "voices": self.voice_synthesizer.list_voices(),
            "custom_profiles": self.voice_synthesizer.list_custom_profiles(),
            "bgm_presets": self.audio_library.list_bgm_presets(),
            "sfx_presets": self.audio_library.list_sfx_presets(),
            "transitions": [t.value for t in TransitionPreset],
            "animations": [a.value for a in AnimationPreset],
            "storytelling_genres": [g.value for g in StorytellingGenre],
        }

    def clone_project(self, project_id: str, new_project_id: str | None = None) -> VideoProject:
        """Deep-clone a project (media files, subtitles, context, characters, scenes)."""
        source = self.repository.get(project_id)
        if not source:
            raise KeyError(f"Project not found: {project_id}")

        target_id = (new_project_id or f"{project_id}_copy_{uuid.uuid4().hex[:4]}").strip()
        while self.repository.get(target_id):
            target_id = f"{project_id}_copy_{uuid.uuid4().hex[:4]}"

        src_dir = self.workspace_root / source.project_id
        dst_dir = self.workspace_root / target_id
        if src_dir.exists():
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)

        def _remap_path(orig: Path | None) -> Path | None:
            if not orig:
                return None
            if orig.exists() and src_dir in orig.parents:
                rel = orig.relative_to(src_dir)
                candidate = dst_dir / rel
                return candidate if candidate.exists() else orig
            return orig

        cloned = VideoProject(
            project_id=target_id,
            source_url=source.source_url,
            engine_type=source.engine_type,
            template_id=source.template_id,
            script_text=source.script_text,
            raw_video_path=_remap_path(source.raw_video_path),
            audio_path=_remap_path(source.audio_path),
            overlay_video_path=_remap_path(source.overlay_video_path),
            subtitles=deepcopy(source.subtitles),
            final_output_path=_remap_path(source.final_output_path),
            status=source.status,
            progress_percent=source.progress_percent,
            current_step=f"Cloned from {source.project_id}",
            animation_preset=source.animation_preset,
            transition_preset=source.transition_preset,
            voice_id=source.voice_id,
            bgm_preset=source.bgm_preset,
            beat_timestamps=list(source.beat_timestamps),
            scene_context=deepcopy(source.scene_context),
            characters=deepcopy(source.characters),
            scenes=deepcopy(source.scenes),
            audit_logs=deepcopy(source.audit_logs),
        )
        cloned.append_log("PROJECT", "Clone Project", f"Cloned from '{source.project_id}' -> '{target_id}'.")
        source.append_log("PROJECT", "Cloned Out", f"Created copy '{target_id}'.")
        self.repository.save(source)
        return self.repository.save(cloned)

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project record and clean up its workspace folder."""
        existed = self.repository.delete(project_id)
        if not existed:
            raise KeyError(f"Project not found: {project_id}")
        proj_dir = self.workspace_root / project_id
        if proj_dir.exists():
            shutil.rmtree(proj_dir, ignore_errors=True)
        return {"deleted": True, "project_id": project_id}

    def update_scene_context(self, project_id: str, context_data: Dict[str, Any]) -> VideoProject:
        """Update global SceneContext continuity bible."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")
        project.scene_context = SceneContext.from_dict(context_data)
        project.current_step = "Context Bible Updated"
        project.append_log(
            "CONTEXT",
            "Update Context",
            f"World='{project.scene_context.world_setting[:45]}', Lens='{project.scene_context.camera_lens}'",
        )
        return self.repository.save(project)

    def manage_scene(
        self,
        project_id: str,
        action: str,
        scene_data: Dict[str, Any] | None = None,
        scene_id: str | None = None,
        scenes_list: List[Dict[str, Any]] | None = None,
    ) -> VideoProject:
        """Add, update, clone, delete, or batch-replace Storyboard Scenes."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")

        act = action.strip().lower()
        if act == "replace_all" and scenes_list is not None:
            project.scenes = [StoryScene.from_dict(item) for item in scenes_list]
            project.append_log("SCENE", "Batch Update Scenes", f"Saved {len(project.scenes)} storyboard scenes.")
        elif act == "delete" and scene_id:
            project.scenes = [s for s in project.scenes if s.scene_id != scene_id]
            project.append_log("SCENE", "Delete Scene", f"Removed scene '{scene_id}'.")
        elif act == "clone" and scene_id:
            target = next((s for s in project.scenes if s.scene_id == scene_id), None)
            if not target:
                raise KeyError(f"Scene '{scene_id}' not found.")
            copy_scene = StoryScene.from_dict(target.to_dict())
            copy_scene.scene_id = f"{target.scene_id}_copy_{uuid.uuid4().hex[:3]}"
            copy_scene.title = f"{target.title} (Copy)"
            copy_scene.start_time = round(target.start_time + target.duration_sec, 3)
            project.scenes.append(copy_scene)
            project.append_log("SCENE", "Clone Scene", f"Cloned '{scene_id}' -> '{copy_scene.scene_id}'.")
        elif scene_data:
            new_scene = StoryScene.from_dict(scene_data)
            idx = next((i for i, s in enumerate(project.scenes) if s.scene_id == new_scene.scene_id), None)
            if idx is not None:
                project.scenes[idx] = new_scene
                project.append_log("SCENE", "Edit Scene", f"Updated '{new_scene.scene_id}' ({new_scene.title}).")
            else:
                project.scenes.append(new_scene)
                project.append_log("SCENE", "Add Scene", f"Added '{new_scene.scene_id}' ({new_scene.title}).")

        project.current_step = f"Storyboard Updated ({len(project.scenes)} scenes)"
        return self.repository.save(project)

    def manage_character(
        self,
        project_id: str,
        action: str,
        char_data: Dict[str, Any] | None = None,
        character_id: str | None = None,
        characters_list: List[Dict[str, Any]] | None = None,
    ) -> VideoProject:
        """Add, update, clone, delete, or batch-replace Consistent Character profiles."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")

        act = action.strip().lower()
        if act == "replace_all" and characters_list is not None:
            project.characters = [CharacterProfile.from_dict(c) for c in characters_list]
            project.append_log("CHARACTER", "Batch Update Characters", f"Saved {len(project.characters)} character profiles.")
        elif act == "delete" and character_id:
            project.characters = [c for c in project.characters if c.character_id != character_id]
            project.append_log("CHARACTER", "Delete Character", f"Removed character '{character_id}'.")
        elif act == "clone" and character_id:
            target = next((c for c in project.characters if c.character_id == character_id), None)
            if not target:
                raise KeyError(f"Character '{character_id}' not found.")
            copy_char = CharacterProfile.from_dict(target.to_dict())
            copy_char.character_id = f"{target.character_id}_copy_{uuid.uuid4().hex[:3]}"
            copy_char.name = f"{target.name} (Clone)"
            project.characters.append(copy_char)
            project.append_log("CHARACTER", "Clone Character", f"Cloned '{character_id}' -> '{copy_char.character_id}'.")
        elif char_data:
            new_char = CharacterProfile.from_dict(char_data)
            idx = next((i for i, c in enumerate(project.characters) if c.character_id == new_char.character_id), None)
            if idx is not None:
                project.characters[idx] = new_char
                project.append_log("CHARACTER", "Edit Character", f"Updated '{new_char.name}' ({new_char.voice_id}).")
            else:
                project.characters.append(new_char)
                project.append_log("CHARACTER", "Add Character", f"Added '{new_char.name}' ({new_char.voice_id}).")

        project.current_step = f"Character Roster Updated ({len(project.characters)} profiles)"
        return self.repository.save(project)

    def synthesize_project_voiceover(
        self,
        project_id: str,
        text: str | None = None,
        voice_id: str = "vi-VN-HoaiMyNeural",
        rate: float = 1.0,
        pitch_hz: int = 0,
    ) -> VideoProject:
        """Generate TTS voiceover from script/subtitles and mux it onto the project's video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        spoken_text = (
            (text or "").strip()
            or " . ".join(s.text for s in project.subtitles).strip()
            or (project.script_text or "").replace("|", ". ").strip()
            or "Kinetix Studio AI Voiceover Ready."
        )
        project_dir = self.workspace_root / project.project_id
        voice_wav = project_dir / "assets" / "audio" / f"voice_{voice_id}.wav"
        generated_wav = self.voice_synthesizer.synthesize(
            text=spoken_text,
            output_path=voice_wav,
            voice_id=voice_id,
            rate=rate,
            pitch_hz=pitch_hz,
        )
        project.audio_path = generated_wav
        project.voice_id = voice_id

        voiced_video = project_dir / f"{project.project_id}_voiced.mp4"
        project.final_output_path = self.processor.replace_audio_track(
            project.final_output_path,
            generated_wav,
            voiced_video,
        )
        project.current_step = f"Voiceover Applied ({voice_id})"
        project.append_log("AUDIO", "TTS Voiceover", f"Synthesized voice '{voice_id}' (rate={rate:.2f}x) -> video audio replaced.")
        return self.repository.save(project)

    def apply_project_sound_library(
        self,
        project_id: str,
        bgm_preset: str | None = None,
        bgm_volume: float = 0.18,
        sfx_id: str | None = None,
        sfx_timestamp: float = 0.5,
        sfx_volume: float = 0.65,
    ) -> VideoProject:
        """Mix a curated BGM preset and/or insert a timestamped SFX effect onto the active video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        project_dir = self.workspace_root / project.project_id
        audio_dir = project_dir / "assets" / "audio"
        current_video = project.final_output_path
        probe = self.processor.probe_media(current_video)
        dur = float(probe.get("duration_seconds") or 6.0)
        actions: List[str] = []

        if bgm_preset and bgm_preset.strip().lower() != "none":
            bgm_path = self.audio_library.resolve_bgm(bgm_preset, audio_dir, duration_sec=dur)
            mixed_out = project_dir / f"{project.project_id}_bgm.mp4"
            current_video = self.processor.mix_audio_tracks(current_video, bgm_path, mixed_out, bg_volume=bgm_volume)
            project.bgm_preset = bgm_preset
            actions.append(f"BGM={bgm_preset} ({int(bgm_volume * 100)}%)")

        if sfx_id and sfx_id.strip().lower() != "none":
            sfx_path = self.audio_library.resolve_sfx(sfx_id, audio_dir)
            sfx_out = project_dir / f"{project.project_id}_sfx.mp4"
            current_video = self.processor.insert_sfx_track(
                current_video,
                sfx_path,
                sfx_out,
                timestamp_sec=sfx_timestamp,
                volume=sfx_volume,
            )
            actions.append(f"SFX={sfx_id}@{sfx_timestamp:.2f}s")

        project.final_output_path = current_video
        summary = " + ".join(actions) if actions else "Sound Library Checked"
        project.current_step = f"Audio Studio: {summary}"
        project.append_log("AUDIO", "Sound Library", summary)
        return self.repository.save(project)

    def apply_project_fx_motion(
        self,
        project_id: str,
        transition_preset: str = "fade_black",
        animation_preset: str = "spring_pop",
    ) -> VideoProject:
        """Apply transition & camera/overlay animation presets onto the project's video."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        project_dir = self.workspace_root / project.project_id
        project.transition_preset = transition_preset
        project.animation_preset = animation_preset

        fx_out = project_dir / f"{project.project_id}_fx.mp4"
        project.final_output_path = self.processor.apply_transition_and_animation(
            project.final_output_path,
            fx_out,
            transition_preset=transition_preset,
            animation_preset=animation_preset,
        )
        project.current_step = f"FX Motion ({transition_preset} + {animation_preset})"
        project.append_log("FX", "Transition & Animation", f"Applied transition='{transition_preset}', animation='{animation_preset}'.")
        return self.repository.save(project)

    def apply_project_beat_cut(
        self,
        project_id: str,
        bpm: int = 120,
        align_subtitles: bool = True,
        pulse_flash: bool = True,
    ) -> VideoProject:
        """Detect BPM beat grid, align subtitle cut points to beats, and apply rhythmic beat accents."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        project_dir = self.workspace_root / project.project_id
        beat_out = project_dir / f"{project.project_id}_beatcut.mp4"
        actual_video, beats = self.processor.detect_beats_and_cut(
            project.final_output_path,
            beat_out,
            bpm=bpm,
            pulse_flash=pulse_flash,
        )
        project.final_output_path = actual_video
        project.beat_timestamps = beats

        if align_subtitles and project.subtitles and len(beats) >= 2:
            def _nearest_beat(val: float) -> float:
                return min(beats, key=lambda b: abs(b - val))

            for idx, seg in enumerate(project.subtitles):
                snapped_start = _nearest_beat(seg.start_time) if idx > 0 else 0.0
                snapped_end = _nearest_beat(seg.end_time)
                if snapped_end <= snapped_start + 0.25:
                    later = [b for b in beats if b > snapped_start + 0.35]
                    snapped_end = later[0] if later else round(snapped_start + 1.0, 3)
                seg.start_time = round(snapped_start, 3)
                seg.end_time = round(snapped_end, 3)
                seg.words = []
                seg.ensure_word_timestamps()

        project.current_step = f"Beat-Cut Synced ({bpm} BPM • {len(beats)} beats)"
        project.append_log(
            "BEAT",
            "Auto Beat-Cut",
            f"Generated {len(beats)} beat markers at {bpm} BPM (align_subtitles={align_subtitles}).",
        )
        return self.repository.save(project)

    # ==========================================================
    # v4.0 INTERACTIVE TIMELINE CLIP CRUD, PODCAST & VOICESTUDIO
    # ==========================================================

    def manage_timeline_clip(
        self,
        project_id: str,
        action: str,
        clip_data: Dict[str, Any] | None = None,
        clip_id: str | None = None,
        split_time: float | None = None,
        render_timeline: bool = False,
    ) -> VideoProject:
        """Full Add / Edit / Split / Clone / Delete CRUD on interactive Multi-Track Timeline clips + Video Render."""
        project = self.repository.get(project_id)
        if not project:
            raise KeyError(f"Project not found: {project_id}")

        raw_dur = 6.0
        target_probe = project.final_output_path or project.raw_video_path
        if target_probe and target_probe.exists():
            raw_dur = float(self.processor.probe_media(target_probe).get("duration_seconds") or 6.0)
        project.ensure_timeline_clips(raw_dur)

        act = action.strip().lower()
        touched_track = "S1"

        if act == "add" and clip_data:
            new_clip = TimelineClip.from_dict(clip_data)
            project.timeline_clips.append(new_clip)
            touched_track = new_clip.track_id
            project.append_log("TIMELINE", "Add Clip", f"Added [{new_clip.track_id}] '{new_clip.label}' ({new_clip.start_time:.2f}s..{new_clip.end_time:.2f}s).")
        elif act == "update" and clip_data:
            cid = clip_id or str(clip_data.get("clip_id") or "")
            existing = next((c for c in project.timeline_clips if c.clip_id == cid), None)
            if not existing:
                raise KeyError(f"Timeline clip '{cid}' not found.")
            existing.track_id = str(clip_data.get("track_id") or existing.track_id).upper()
            existing.label = str(clip_data.get("label") or existing.label).strip() or existing.label
            existing.start_time = max(0.0, float(clip_data.get("start_time") if clip_data.get("start_time") is not None else existing.start_time))
            existing.end_time = max(existing.start_time + 0.1, float(clip_data.get("end_time") if clip_data.get("end_time") is not None else existing.end_time))
            if clip_data.get("source_start") is not None:
                existing.source_start = max(0.0, float(clip_data["source_start"]))
            else:
                existing.source_start = existing.start_time
            if clip_data.get("source_end") is not None:
                existing.source_end = max(existing.source_start + 0.1, float(clip_data["source_end"]))
            else:
                existing.source_end = existing.end_time
            touched_track = existing.track_id
            project.append_log("TIMELINE", "Edit Clip", f"Updated '{cid}' -> [{existing.track_id}] {existing.start_time:.2f}s..{existing.end_time:.2f}s.")
        elif act == "split":
            t_split = float(split_time or 0.0)
            target = next((c for c in project.timeline_clips if c.clip_id == clip_id), None) if clip_id else None
            if target is None:
                target = next((c for c in project.timeline_clips if c.track_id == "V1" and c.start_time + 0.15 < t_split < c.end_time - 0.15), None)
            if not target:
                raise KeyError("No timeline clip spans the requested split time.")
            if not (target.start_time + 0.12 < t_split < target.end_time - 0.12):
                t_split = round((target.start_time + target.end_time) / 2.0, 3)

            orig_end = target.end_time
            orig_src_end = target.source_end
            mid_src = target.source_start + (t_split - target.start_time)
            target.end_time = round(t_split, 3)
            target.source_end = round(min(orig_src_end, mid_src), 3)

            words = target.label.split(" ")
            part1_label = " ".join(words[: max(1, len(words) // 2)]) if target.track_id == "S1" and len(words) > 1 else f"{target.label} (A)"
            part2_label = " ".join(words[max(1, len(words) // 2) :]) if target.track_id == "S1" and len(words) > 1 else f"{target.label} (B)"
            if target.track_id == "S1":
                target.label = part1_label

            second_clip = TimelineClip(
                clip_id=f"{target.clip_id}_p2_{uuid.uuid4().hex[:3]}",
                track_id=target.track_id,
                label=part2_label,
                start_time=round(t_split, 3),
                end_time=round(orig_end, 3),
                source_start=round(mid_src, 3),
                source_end=round(orig_src_end, 3),
                speed=target.speed,
                volume=target.volume,
                transition_in=target.transition_in,
            )
            idx = project.timeline_clips.index(target) + 1
            project.timeline_clips.insert(idx, second_clip)
            touched_track = target.track_id
            project.append_log("TIMELINE", "Split Clip", f"Split '{target.clip_id}' at {t_split:.2f}s -> '{second_clip.clip_id}'.")
        elif act == "clone":
            target = next((c for c in project.timeline_clips if c.clip_id == clip_id), None)
            if not target:
                raise KeyError(f"Timeline clip '{clip_id}' not found.")
            dur = max(0.3, target.end_time - target.start_time)
            copy_clip = TimelineClip(
                clip_id=f"{target.clip_id}_copy_{uuid.uuid4().hex[:3]}",
                track_id=target.track_id,
                label=f"{target.label} (Copy)" if target.track_id != "S1" else target.label,
                start_time=round(target.end_time, 3),
                end_time=round(target.end_time + dur, 3),
                source_start=target.source_start,
                source_end=target.source_end,
                speed=target.speed,
                volume=target.volume,
                transition_in=target.transition_in,
            )
            project.timeline_clips.append(copy_clip)
            touched_track = target.track_id
            project.append_log("TIMELINE", "Clone Clip", f"Cloned '{clip_id}' -> '{copy_clip.clip_id}'.")
        elif act == "delete":
            target = next((c for c in project.timeline_clips if c.clip_id == clip_id), None)
            if target:
                touched_track = target.track_id
            project.timeline_clips = [c for c in project.timeline_clips if c.clip_id != clip_id]
            project.append_log("TIMELINE", "Delete Clip", f"Deleted timeline clip '{clip_id}'.")

        # Always keep S1 subtitle clips synced with project.subtitles
        s1_clips = sorted([c for c in project.timeline_clips if c.track_id == "S1"], key=lambda c: c.start_time)
        if touched_track == "S1" or s1_clips:
            synced_subs: List[SubtitleSegment] = []
            for sc in s1_clips:
                seg = SubtitleSegment(start_time=sc.start_time, end_time=sc.end_time, text=sc.label)
                seg.ensure_word_timestamps()
                synced_subs.append(seg)
            project.subtitles = synced_subs

        if (render_timeline or act == "render") and project.raw_video_path and project.raw_video_path.exists():
            project_dir = self.workspace_root / project.project_id
            v1_clips = sorted([c for c in project.timeline_clips if c.track_id == "V1"], key=lambda c: c.start_time)
            base_video = project.raw_video_path

            if v1_clips:
                cut_dir = project_dir / "timeline_cuts"
                cut_dir.mkdir(parents=True, exist_ok=True)
                trimmed_parts: List[Path] = []
                for idx, vc in enumerate(v1_clips, start=1):
                    part_out = cut_dir / f"part_{idx:02d}.mp4"
                    s_in = max(0.0, vc.source_start)
                    s_out = max(s_in + 0.25, vc.source_end)
                    actual_part = self.processor.trim_video(project.raw_video_path, part_out, s_in, s_out)
                    trimmed_parts.append(actual_part)

                if len(trimmed_parts) == 1:
                    base_video = trimmed_parts[0]
                elif len(trimmed_parts) > 1:
                    assembled = project_dir / f"{project.project_id}_timeline_base.mp4"
                    base_video = self.processor.concat_clips(trimmed_parts, assembled, transition="none")

            base_dur = float(self.processor.probe_media(base_video).get("duration_seconds") or 6.0)
            renderer = RendererFactory.get_renderer(project.engine_type)
            overlay_target = project_dir / f"{project.project_id}_overlay.mp4"
            props = {
                "project_id": project.project_id,
                "engine": project.engine_type.value,
                "animation_preset": project.animation_preset,
                "scene_context": project.scene_context.to_dict(),
                "characters": [c.to_dict() for c in project.characters],
                "duration_seconds": base_dur,
                "subtitles": [s.to_dict() for s in project.subtitles],
            }
            project.overlay_video_path = renderer.render_composition(project.template_id, props, overlay_target)
            final_target = project_dir / f"{project.project_id}_final.mp4"
            project.final_output_path = self.processor.merge_and_export(
                base_video,
                project.overlay_video_path,
                final_target,
                subtitles=project.subtitles,
            )
            project.append_log("TIMELINE", "Render Timeline", f"Rendered {len(v1_clips)} V1 clips + {len(project.subtitles)} S1 cues -> {project.final_output_path.name}.")

        project.current_step = f"Timeline Updated ({len(project.timeline_clips)} clips)"
        return self.repository.save(project)

    def design_custom_voice(
        self,
        name: str,
        prompt_description: str,
        seed: int = 42,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Create and persist a synthetic VoiceProfile using natural-language Voice Design (VoiceStudio)."""
        return self.voice_synthesizer.design_voice(
            name=name,
            prompt_description=prompt_description,
            seed=seed,
            language=language,
        )

    def clone_custom_voice(
        self,
        name: str,
        reference_audio_path: str,
        consent_verified: bool = False,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Clone a voice from a reference audio file after verifying explicit consent (VoiceStudio policy)."""
        return self.voice_synthesizer.clone_voice(
            name=name,
            reference_audio_path=Path(reference_audio_path),
            consent_verified=consent_verified,
            language=language,
        )

    def generate_project_podcast(
        self,
        project_id: str,
        raw_content: str,
        genre: str = "podcast_dialogue",
        host_voice_id: str = "vi-VN-HoaiMyNeural",
        guest_voice_id: str = "vi-VN-NamMinhNeural",
        bgm_volume: float = 0.14,
    ) -> VideoProject:
        """Transform user text/story into a multi-voice expressive Podcast/Audiobook & render full MP4."""
        import re

        project = self.repository.get(project_id)
        if not project:
            # Auto-create a showcase workspace project if project_id does not yet exist
            project = self.create_and_run_project(
                project_id=project_id,
                source_url="demo://sample",
                engine_type="hyperframes",
                template_id="KineticTitleCard",
                script_text="Kinetix Podcast Studio",
            )

        clean_input = raw_content.strip()
        if not clean_input:
            raise ValueError("Podcast content must not be empty.")

        # Split user input by newline / '|' / sentence boundaries into coherent turns
        raw_lines = [p.strip() for ln in clean_input.splitlines() for p in ln.split("|") if p.strip()]
        if len(raw_lines) == 1:
            sentence_parts = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", raw_lines[0]) if s.strip()]
            if len(sentence_parts) > 1:
                raw_lines = sentence_parts

        genre_map = {
            "podcast_dialogue": {"emotion": "warm", "bgm": "bgm_lofi_chill", "pause": 350, "two_speakers": True},
            "late_night_story": {"emotion": "late_night", "bgm": "bgm_ambient_pad", "pause": 550, "two_speakers": False},
            "thriller_mystery": {"emotion": "mysterious", "bgm": "bgm_dramatic_rise", "pause": 480, "two_speakers": False},
            "audiobook_narration": {"emotion": "calm", "bgm": "bgm_ambient_pad", "pause": 420, "two_speakers": False},
            "tech_explainer": {"emotion": "excited", "bgm": "bgm_cyber_pulse", "pause": 300, "two_speakers": True},
            "motivational_epic": {"emotion": "dramatic", "bgm": "bgm_dramatic_rise", "pause": 400, "two_speakers": False},
        }
        cfg = genre_map.get(genre.strip().lower(), genre_map["podcast_dialogue"])

        turns: List[PodcastTurn] = []
        for idx, line in enumerate(raw_lines):
            if ":" in line and len(line.split(":", 1)[0]) <= 24:
                spk_raw, body = line.split(":", 1)
                spk_name = spk_raw.strip()
                voice = guest_voice_id if (idx % 2 == 1 and cfg["two_speakers"]) else host_voice_id
                text_body = body.strip()
            else:
                use_guest = bool(cfg["two_speakers"] and idx % 2 == 1)
                spk_name = "Guest" if use_guest else "Host"
                voice = guest_voice_id if use_guest else host_voice_id
                text_body = line
            turns.append(
                PodcastTurn(
                    turn_id=f"turn_{idx + 1:02d}",
                    speaker_name=spk_name,
                    voice_id=voice,
                    emotion=str(cfg["emotion"]),
                    text=text_body,
                    pause_after_ms=int(cfg["pause"]),
                )
            )

        project_dir = self.workspace_root / project.project_id
        podcast_wav = project_dir / "assets" / "audio" / f"{project.project_id}_podcast.wav"
        stitched_wav, timed_segs = self.voice_synthesizer.synthesize_podcast_script(
            turns=[t.to_dict() for t in turns],
            output_path=podcast_wav,
            genre=genre,
        )

        # Rebuild SubtitleSegments, StoryScenes, and TimelineClips synced 1:1 to voice durations
        project.podcast_turns = turns
        project.subtitles = []
        project.scenes = []
        for idx, seg_info in enumerate(timed_segs, start=1):
            sub = SubtitleSegment(
                start_time=float(seg_info["start_time"]),
                end_time=float(seg_info["end_time"]),
                text=str(seg_info["text"]),
            )
            sub.ensure_word_timestamps()
            project.subtitles.append(sub)
            project.scenes.append(
                StoryScene(
                    scene_id=f"pod_scene_{idx:02d}",
                    title=f"{seg_info['speaker_name']} #{idx}",
                    setting_context=f"{genre} • Studio",
                    character_id=project.characters[idx % len(project.characters)].character_id if project.characters else "char_host",
                    narration_text=str(seg_info["text"]),
                    start_time=float(seg_info["start_time"]),
                    duration_sec=max(0.3, round(float(seg_info["end_time"]) - float(seg_info["start_time"]), 3)),
                    transition_in=project.transition_preset,
                    animation_preset=project.animation_preset,
                )
            )

        total_dur = max(2.0, project.subtitles[-1].end_time if project.subtitles else 6.0)
        project.audio_path = stitched_wav
        project.timeline_clips = []
        project.ensure_timeline_clips(total_dur)

        # Extend base video smoothly to podcast length, replace audio, render overlay & mix genre BGM
        base_for_audio = project.raw_video_path
        if not base_for_audio or not base_for_audio.exists():
            base_for_audio = self.downloader.download("demo://sample", project_dir)
            project.raw_video_path = base_for_audio

        voiced_base = project_dir / f"{project.project_id}_pod_base.mp4"
        voiced_base = self.processor.replace_audio_track(base_for_audio, stitched_wav, voiced_base)

        renderer = RendererFactory.get_renderer(project.engine_type)
        overlay_target = project_dir / f"{project.project_id}_overlay.mp4"
        props = {
            "project_id": project.project_id,
            "engine": project.engine_type.value,
            "animation_preset": project.animation_preset,
            "scene_context": project.scene_context.to_dict(),
            "characters": [c.to_dict() for c in project.characters],
            "duration_seconds": total_dur,
            "subtitles": [s.to_dict() for s in project.subtitles],
        }
        project.overlay_video_path = renderer.render_composition(project.template_id, props, overlay_target)

        merged_out = project_dir / f"{project.project_id}_pod_merged.mp4"
        merged_out = self.processor.merge_and_export(
            voiced_base,
            project.overlay_video_path,
            merged_out,
            subtitles=project.subtitles,
        )

        bgm_wav = self.audio_library.resolve_bgm(str(cfg["bgm"]), project_dir / "assets" / "audio", duration_sec=total_dur)
        final_pod = project_dir / f"{project.project_id}_podcast_final.mp4"
        project.final_output_path = self.processor.mix_audio_tracks(merged_out, bgm_wav, final_pod, bg_volume=bgm_volume)
        project.bgm_preset = str(cfg["bgm"])
        project.status = JobStatus.COMPLETED
        project.progress_percent = 100
        project.current_step = f"Podcast Ready ({genre} • {len(turns)} turns • {total_dur:.1f}s)"
        project.append_log(
            "PODCAST",
            f"Generate Podcast ({genre})",
            f"Synthesized {len(turns)} multi-voice turns ({host_voice_id} / {guest_voice_id}) + BGM '{cfg['bgm']}'.",
        )
        return self.repository.save(project)

    def dub_project_video(
        self,
        project_id: str,
        target_language: str = "vi-VN",
        voice_id: str = "vi-VN-HoaiMyNeural",
        translated_lines: List[str] | None = None,
    ) -> VideoProject:
        """Time-aligned AI Video Dubbing inspired by VoiceStudio (dubbing subtitles matched to timeline windows)."""
        project = self.repository.get(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise KeyError(f"Completed video not found for project: {project_id}")

        lines = translated_lines or [s.text for s in project.subtitles]
        if not lines:
            lines = ["Kinetix Studio Dubbed Narration"]

        turns: List[Dict[str, Any]] = []
        for idx, text in enumerate(lines, start=1):
            turns.append(
                {
                    "turn_id": f"dub_{idx:02d}",
                    "speaker_name": f"Dub ({target_language})",
                    "voice_id": voice_id,
                    "emotion": "warm",
                    "text": text,
                    "pause_after_ms": 200,
                }
            )

        project_dir = self.workspace_root / project.project_id
        dub_wav = project_dir / "assets" / "audio" / f"{project.project_id}_dub_{target_language}.wav"
        stitched_wav, timed_segs = self.voice_synthesizer.synthesize_podcast_script(turns, dub_wav, genre="dubbing")

        dubbed_video = project_dir / f"{project.project_id}_dubbed.mp4"
        project.final_output_path = self.processor.replace_audio_track(project.final_output_path, stitched_wav, dubbed_video)
        project.voice_id = voice_id
        project.subtitles = [
            SubtitleSegment(start_time=float(s["start_time"]), end_time=float(s["end_time"]), text=str(s["text"]))
            for s in timed_segs
        ]
        for s in project.subtitles:
            s.ensure_word_timestamps()

        project.current_step = f"Video Dubbed ({target_language} • {voice_id})"
        project.append_log("DUBBING", "AI Video Dubbing", f"Dubbed {len(turns)} segments in {target_language} using '{voice_id}'.")
        return self.repository.save(project)
