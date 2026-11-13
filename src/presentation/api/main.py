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
    ColorGradeRequest,
    CreateProjectRequest,
    HealthResponse,
    InspectSourceRequest,
    MixAudioRequest,
    ProjectResponse,
    ReframeRequest,
    SnapshotRequest,
    SpeedChangeRequest,
    UpdateSubtitlesRequest,
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
                "kinetix_inspect_source",
                "kinetix_launch_desktop_app",
                "kinetix_health_check",
            ],
        }

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
