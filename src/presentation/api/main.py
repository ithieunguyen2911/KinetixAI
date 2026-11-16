"""FastAPI REST Server for KinetixAI Core Orchestrator & MCP HTTP Bridge."""

from pathlib import Path
import shutil
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.application.services.project_service import ProjectService
from src.domain.entities.enums import RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment, WordTimestamp
from src.presentation.schemas.project_schemas import (
    AudioMasterRequest,
    BeatCutRequest,
    CloneProjectRequest,
    ColorGradeRequest,
    ConcatClipsRequest,
    CreateProjectRequest,
    DubbingRequest,
    FxMotionRequest,
    HealthResponse,
    InspectSourceRequest,
    ManageCharacterRequest,
    ManageSceneRequest,
    ManageTimelineClipRequest,
    MixAudioRequest,
    PodcastRequest,
    ProjectResponse,
    ReframeRequest,
    SceneContextSchema,
    SnapshotRequest,
    SoundLibraryRequest,
    SpeedChangeRequest,
    SplitVideoRequest,
    UpdateSubtitlesRequest,
    VoiceCloneRequest,
    VoiceDesignRequest,
    VoiceoverRequest,
)


class AiMcpCommandRequest(BaseModel):
    """Schema for AI / MCP natural or structured video generation commands."""

    prompt: str = Field(
        default="Create Kinetix Studio promo with HyperFrames",
        description="Natural language instruction from AI agent or user",
    )
    project_id: str | None = None
    source_url: str = "demo://sample"
    engine_type: str | None = None
    script_text: str | None = None


class TrimVideoRequest(BaseModel):
    """Schema for FFmpeg video trimming."""

    start_time: float = Field(ge=0.0)
    end_time: float = Field(gt=0.0)


def create_app(workspace_root: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="KinetixAI (FlowVids-AI) Core Orchestrator & MCP API",
        version="1.2.0",
        description="Clean Architecture Polyglot Automated Video Production Backend (yt-dlp + Whisper + FFmpeg + Remotion + HyperFrames + Antigravity MCP)",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    service = ProjectService(workspace_root=workspace_root)
    app.state.project_service = service

    @app.get("/api/v1/health", response_model=HealthResponse)
    def get_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name="Kinetix Studio Core Orchestrator",
            version="1.2.0",
            supported_engines=[e.value for e in RenderEngineType],
            tools={
                "ffmpeg": shutil.which("ffmpeg") is not None,
                "ffprobe": shutil.which("ffprobe") is not None,
                "node": shutil.which("node") is not None,
                "yt_dlp": True,
                "whisper": True,
                "remotion": True,
                "hyperframes": True,
                "mcp_server": True,
            },
        )

    @app.get("/api/v1/projects", response_model=List[ProjectResponse])
    def list_projects() -> List[ProjectResponse]:
        projects = service.list_projects()
        return [ProjectResponse(**p.to_dict()) for p in projects]

    @app.post("/api/v1/sources/inspect")
    def inspect_source(request: InspectSourceRequest) -> Dict[str, Any]:
        try:
            return service.inspect_source(request.source_url)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects", response_model=ProjectResponse)
    def create_and_run_project(request: CreateProjectRequest) -> ProjectResponse:
        try:
            project = service.create_and_run_project(
                project_id=request.project_id,
                source_url=request.source_url,
                engine_type=request.engine_type,
                template_id=request.template_id,
                script_text=request.script_text,
            )
            return ProjectResponse(**project.to_dict())
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/mcp/command", response_model=ProjectResponse)
    def execute_ai_mcp_command(request: AiMcpCommandRequest) -> ProjectResponse:
        """Execute an AI Antigravity / MCP command to automatically configure and produce a video."""
        prompt_lower = request.prompt.lower()
        engine = request.engine_type
        if not engine:
            engine = "hyperframes" if "hyperframes" in prompt_lower else "remotion"

        existing_count = len(service.list_projects()) + 1
        project_id = request.project_id or f"mcp_{engine}_{existing_count:02d}"
        script_text = request.script_text or (
            f"Kinetix Studio ({engine.upper()})|"
            f"{request.prompt.strip()[:60]}|"
            "Automated via Antigravity MCP & Clean Architecture"
        )
        try:
            project = service.create_and_run_project(
                project_id=project_id,
                source_url=request.source_url,
                engine_type=engine,
                template_id="CaptionTemplate",
                script_text=script_text,
            )
            return ProjectResponse(**project.to_dict())
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/mcp/tools")
    def list_mcp_tools() -> Dict[str, Any]:
        return {
            "mcp_server": "kinetix-ai",
            "transport": ["stdio", "http-bridge"],
            "tools": [
                "kinetix_produce_video",
                "kinetix_list_projects",
                "kinetix_get_project",
                "kinetix_update_subtitles",
                "kinetix_probe_media",
                "kinetix_trim_video",
                "kinetix_change_speed",
                "kinetix_apply_color_grade",
                "kinetix_reframe_video",
                "kinetix_master_audio",
                "kinetix_capture_snapshot",
                "kinetix_clone_project",
                "kinetix_delete_project",
                "kinetix_manage_character",
                "kinetix_manage_scene",
                "kinetix_generate_voiceover",
                "kinetix_apply_sound_library",
                "kinetix_apply_beat_cut",
                "kinetix_apply_transition_animation",
                "kinetix_manage_timeline_clip",
                "kinetix_produce_podcast",
                "kinetix_design_voice",
                "kinetix_clone_voice",
                "kinetix_dub_video",
                "kinetix_inspect_source",
                "kinetix_launch_desktop_app",
                "kinetix_health_check",
            ],
        }

    @app.get("/api/v1/catalog/studio")
    def get_studio_catalog() -> Dict[str, Any]:
        return service.get_studio_catalog()

    @app.get("/api/v1/voices/profiles")
    def list_voice_profiles() -> List[Dict[str, Any]]:
        return service.voice_synthesizer.list_voices()

    @app.post("/api/v1/voices/design")
    def design_custom_voice(request: VoiceDesignRequest) -> Dict[str, Any]:
        try:
            return service.design_custom_voice(
                name=request.name,
                prompt_description=request.prompt_description,
                seed=request.seed,
                language=request.language,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/voices/clone")
    def clone_custom_voice(request: VoiceCloneRequest) -> Dict[str, Any]:
        try:
            return service.clone_custom_voice(
                name=request.name,
                reference_audio_path=request.reference_audio_path,
                consent_verified=request.consent_verified,
                language=request.language,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
    def get_project(project_id: str) -> ProjectResponse:
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        return ProjectResponse(**project.to_dict())

    @app.get("/api/v1/projects/{project_id}/probe")
    def probe_project(project_id: str) -> Dict[str, Any]:
        try:
            return service.probe_project_media(project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/trim", response_model=ProjectResponse)
    def trim_project_video(project_id: str, request: TrimVideoRequest) -> ProjectResponse:
        try:
            project = service.trim_project_video(
                project_id=project_id,
                start_time=request.start_time,
                end_time=request.end_time,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/mix-audio", response_model=ProjectResponse)
    def mix_project_audio(project_id: str, request: MixAudioRequest) -> ProjectResponse:
        try:
            project = service.mix_project_audio(
                project_id=project_id,
                background_audio_path=Path(request.background_audio_path),
                bg_volume=request.bg_volume,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/speed", response_model=ProjectResponse)
    def change_project_speed(project_id: str, request: SpeedChangeRequest) -> ProjectResponse:
        try:
            project = service.change_project_speed(
                project_id=project_id,
                speed_factor=request.speed_factor,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/color-grade", response_model=ProjectResponse)
    def apply_project_color_grade(project_id: str, request: ColorGradeRequest) -> ProjectResponse:
        try:
            project = service.apply_project_color_grade(
                project_id=project_id,
                preset=request.preset,
                brightness=request.brightness,
                contrast=request.contrast,
                saturation=request.saturation,
                gamma=request.gamma,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/reframe", response_model=ProjectResponse)
    def reframe_project_video(project_id: str, request: ReframeRequest) -> ProjectResponse:
        try:
            project = service.reframe_project_video(
                project_id=project_id,
                aspect_ratio=request.aspect_ratio,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/audio-master", response_model=ProjectResponse)
    def master_project_audio(project_id: str, request: AudioMasterRequest) -> ProjectResponse:
        try:
            project = service.master_project_audio(
                project_id=project_id,
                remove_silence=request.remove_silence,
                normalize_loudness=request.normalize_loudness,
                mix_bgm=request.mix_bgm,
                bgm_source=request.bgm_source,
                bg_volume=request.bg_volume,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/snapshot")
    def capture_project_snapshot(project_id: str, request: SnapshotRequest) -> Dict[str, Any]:
        try:
            return service.capture_project_snapshot(
                project_id=project_id,
                timestamp_sec=request.timestamp_sec,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/split")
    def split_project_video(project_id: str, request: SplitVideoRequest) -> Dict[str, Any]:
        try:
            return service.split_project_video(
                project_id=project_id,
                split_time=request.split_time,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/concat", response_model=ProjectResponse)
    def concat_project_clips(project_id: str, request: ConcatClipsRequest) -> ProjectResponse:
        try:
            project = service.concat_project_clips(
                project_id=project_id,
                clip_paths=request.clip_paths,
                transition=request.transition,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/projects/{project_id}/subtitles/export")
    def export_project_subtitles(project_id: str, fmt: str = "srt") -> Dict[str, Any]:
        try:
            return service.export_project_subtitles(project_id=project_id, fmt=fmt)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/clone", response_model=ProjectResponse)
    def clone_project(project_id: str, request: CloneProjectRequest | None = None) -> ProjectResponse:
        try:
            new_id = request.new_project_id if request else None
            cloned = service.clone_project(project_id=project_id, new_project_id=new_id)
            return ProjectResponse(**cloned.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/v1/projects/{project_id}")
    def delete_project(project_id: str) -> Dict[str, Any]:
        try:
            return service.delete_project(project_id=project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/context", response_model=ProjectResponse)
    def update_scene_context(project_id: str, request: SceneContextSchema) -> ProjectResponse:
        try:
            updated = service.update_scene_context(project_id=project_id, context_data=request.model_dump())
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/scenes", response_model=ProjectResponse)
    def manage_scenes(project_id: str, request: ManageSceneRequest) -> ProjectResponse:
        try:
            updated = service.manage_scene(
                project_id=project_id,
                action=request.action,
                scene_data=request.scene.model_dump() if request.scene else None,
                scene_id=request.scene_id,
                scenes_list=[s.model_dump() for s in request.scenes] if request.scenes is not None else None,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/characters", response_model=ProjectResponse)
    def manage_characters(project_id: str, request: ManageCharacterRequest) -> ProjectResponse:
        try:
            updated = service.manage_character(
                project_id=project_id,
                action=request.action,
                char_data=request.character.model_dump() if request.character else None,
                character_id=request.character_id,
                characters_list=[c.model_dump() for c in request.characters] if request.characters is not None else None,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/voiceover", response_model=ProjectResponse)
    def synthesize_voiceover(project_id: str, request: VoiceoverRequest) -> ProjectResponse:
        try:
            updated = service.synthesize_project_voiceover(
                project_id=project_id,
                text=request.text,
                voice_id=request.voice_id,
                rate=request.rate,
                pitch_hz=request.pitch_hz,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/sound-library", response_model=ProjectResponse)
    def apply_sound_library(project_id: str, request: SoundLibraryRequest) -> ProjectResponse:
        try:
            updated = service.apply_project_sound_library(
                project_id=project_id,
                bgm_preset=request.bgm_preset,
                bgm_volume=request.bgm_volume,
                sfx_id=request.sfx_id,
                sfx_timestamp=request.sfx_timestamp,
                sfx_volume=request.sfx_volume,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/fx-motion", response_model=ProjectResponse)
    def apply_fx_motion(project_id: str, request: FxMotionRequest) -> ProjectResponse:
        try:
            updated = service.apply_project_fx_motion(
                project_id=project_id,
                transition_preset=request.transition_preset,
                animation_preset=request.animation_preset,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/beat-cut", response_model=ProjectResponse)
    def apply_beat_cut(project_id: str, request: BeatCutRequest) -> ProjectResponse:
        try:
            updated = service.apply_project_beat_cut(
                project_id=project_id,
                bpm=request.bpm,
                align_subtitles=request.align_subtitles,
                pulse_flash=request.pulse_flash,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/timeline-clips", response_model=ProjectResponse)
    def manage_timeline_clips(project_id: str, request: ManageTimelineClipRequest) -> ProjectResponse:
        try:
            updated = service.manage_timeline_clip(
                project_id=project_id,
                action=request.action,
                clip_data=request.clip.model_dump() if request.clip else None,
                clip_id=request.clip_id,
                split_time=request.split_time,
                render_timeline=request.render_timeline,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/podcast", response_model=ProjectResponse)
    def generate_podcast(project_id: str, request: PodcastRequest) -> ProjectResponse:
        try:
            updated = service.generate_project_podcast(
                project_id=project_id,
                raw_content=request.raw_content,
                genre=request.genre,
                host_voice_id=request.host_voice_id,
                guest_voice_id=request.guest_voice_id,
                bgm_volume=request.bgm_volume,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/dubbing", response_model=ProjectResponse)
    def dub_video(project_id: str, request: DubbingRequest) -> ProjectResponse:
        try:
            updated = service.dub_project_video(
                project_id=project_id,
                target_language=request.target_language,
                voice_id=request.voice_id,
                translated_lines=request.translated_lines,
            )
            return ProjectResponse(**updated.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/projects/{project_id}/subtitles", response_model=ProjectResponse)
    def update_subtitles(project_id: str, request: UpdateSubtitlesRequest) -> ProjectResponse:
        try:
            domain_subs = [
                SubtitleSegment(
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.text,
                    words=[
                        WordTimestamp(word=w.word, start_time=w.start_time, end_time=w.end_time)
                        for w in s.words
                    ],
                )
                for s in request.subtitles
            ]
            project = service.update_subtitles_and_rerender(
                project_id=project_id,
                subtitles=domain_subs,
                engine_type=request.engine_type,
                template_id=request.template_id,
            )
            return ProjectResponse(**project.to_dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/projects/{project_id}/video")
    def download_final_video(project_id: str) -> FileResponse:
        project = service.get_project(project_id)
        if not project or not project.final_output_path or not project.final_output_path.exists():
            raise HTTPException(status_code=404, detail="Final video not available.")
        return FileResponse(
            path=str(project.final_output_path),
            media_type="video/mp4",
            filename=project.final_output_path.name,
        )

    return app


app = create_app()
