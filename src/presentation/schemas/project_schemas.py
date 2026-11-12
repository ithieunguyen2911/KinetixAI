"""Pydantic v2 Data Contracts for FastAPI REST Endpoints and Desktop Client."""

from typing import List
from pydantic import BaseModel, Field


class WordTimestampSchema(BaseModel):
    word: str
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)


class SubtitleSegmentSchema(BaseModel):
    start_time: float = Field(ge=0.0)
    end_time: float = Field(gt=0.0)
    text: str = Field(min_length=1)
    words: List[WordTimestampSchema] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    project_id: str = Field(min_length=1, description="Unique project slug")
    source_url: str = Field(
        default="demo://sample",
        min_length=1,
        description="Video URL, local file path, or demo://sample",
    )
    engine_type: str = Field(
        default="remotion",
        pattern="^(remotion|hyperframes)$",
        description="Visual render engine: remotion or hyperframes",
    )
    template_id: str = Field(default="CaptionTemplate")
    script_text: str | None = Field(
        default=None,
        description="Optional script separated by | or newlines (leave empty to auto-transcribe audio with Whisper)",
    )


class InspectSourceRequest(BaseModel):
    source_url: str = Field(min_length=1, description="Video URL, local file path, or demo://sample")


class MixAudioRequest(BaseModel):
    background_audio_path: str = Field(min_length=1, description="Path to background audio WAV/MP3 file")
    bg_volume: float = Field(default=0.20, ge=0.0, le=1.0)


class UpdateSubtitlesRequest(BaseModel):
    engine_type: str | None = Field(default=None, pattern="^(remotion|hyperframes)$")
    subtitles: List[SubtitleSegmentSchema]


class ProjectResponse(BaseModel):
    project_id: str
    source_url: str
    engine_type: str
    template_id: str
    script_text: str | None = None
    raw_video_path: str | None = None
    audio_path: str | None = None
    overlay_video_path: str | None = None
    subtitles: List[SubtitleSegmentSchema] = Field(default_factory=list)
    final_output_path: str | None = None
    status: str
    progress_percent: int
    current_step: str
    error_message: str | None = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    supported_engines: List[str]
    tools: dict
