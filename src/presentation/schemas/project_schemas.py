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


class SpeedChangeRequest(BaseModel):
    speed_factor: float = Field(default=1.25, ge=0.25, le=4.0)


class ColorGradeRequest(BaseModel):
    preset: str = Field(default="natural")
    brightness: float = Field(default=0.0, ge=-1.0, le=1.0)
    contrast: float = Field(default=1.0, ge=0.2, le=3.0)
    saturation: float = Field(default=1.0, ge=0.0, le=3.0)
    gamma: float = Field(default=1.0, ge=0.2, le=3.0)


class ReframeRequest(BaseModel):
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")


class AudioMasterRequest(BaseModel):
    remove_silence: bool = Field(default=False)
    normalize_loudness: bool = Field(default=True)
    mix_bgm: bool = Field(default=False)
    bgm_source: str = Field(default="demo://bgm")
    bg_volume: float = Field(default=0.18, ge=0.0, le=1.0)


class SnapshotRequest(BaseModel):
    timestamp_sec: float = Field(default=1.0, ge=0.0)


class SplitVideoRequest(BaseModel):
    split_time: float = Field(default=3.0, gt=0.0)


class ConcatClipsRequest(BaseModel):
    clip_paths: List[str] = Field(min_length=1)
    transition: str = Field(default="none")


class UpdateSubtitlesRequest(BaseModel):
    engine_type: str | None = Field(default=None, pattern="^(remotion|hyperframes)$")
    template_id: str | None = Field(default=None)
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
