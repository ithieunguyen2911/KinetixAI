"""Pydantic v2 Data Contracts for FastAPI REST Endpoints and Desktop Client (v3.0 Studio)."""

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


class SceneContextSchema(BaseModel):
    world_setting: str = "Modern AI Production Studio — Dark Slate Workstation"
    visual_style: str = "Cinematic Clean UI, Subtle Tech Grid, High Broadcast Contrast"
    lighting_mood: str = "Cool Cobalt Rim Light + Crisp Key Fill"
    camera_lens: str = "35mm Anamorphic Studio Framing"
    continuity_notes: str = "Maintain consistent character badge colors, voice tone, and subtitle styling."


class CharacterProfileSchema(BaseModel):
    character_id: str
    name: str
    role: str = "Presenter"
    visual_description: str = ""
    voice_id: str = "vi-VN-HoaiMyNeural"
    theme_color: str = "#3B82F6"
    avatar_badge: str = "HOST"


class StorySceneSchema(BaseModel):
    scene_id: str
    title: str
    setting_context: str = "Main Studio Desk"
    character_id: str = "char_host"
    narration_text: str = ""
    start_time: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(default=2.0, gt=0.1)
    transition_in: str = "fade_black"
    animation_preset: str = "spring_pop"
    sfx_id: str = "sfx_whoosh_fast"


class AuditLogEntrySchema(BaseModel):
    log_id: str = ""
    timestamp: str = ""
    category: str = "PIPELINE"
    action: str = ""
    details: str = ""
    status: str = "OK"


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


class CloneProjectRequest(BaseModel):
    new_project_id: str | None = None


class ManageSceneRequest(BaseModel):
    action: str = Field(default="upsert", pattern="^(upsert|delete|clone|replace_all)$")
    scene_id: str | None = None
    scene: StorySceneSchema | None = None
    scenes: List[StorySceneSchema] | None = None


class ManageCharacterRequest(BaseModel):
    action: str = Field(default="upsert", pattern="^(upsert|delete|clone|replace_all)$")
    character_id: str | None = None
    character: CharacterProfileSchema | None = None
    characters: List[CharacterProfileSchema] | None = None


class VoiceoverRequest(BaseModel):
    text: str | None = None
    voice_id: str = "vi-VN-HoaiMyNeural"
    rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch_hz: int = Field(default=0, ge=-50, le=50)


class SoundLibraryRequest(BaseModel):
    bgm_preset: str | None = None
    bgm_volume: float = Field(default=0.18, ge=0.0, le=1.0)
    sfx_id: str | None = None
    sfx_timestamp: float = Field(default=0.5, ge=0.0)
    sfx_volume: float = Field(default=0.65, ge=0.0, le=1.5)


class FxMotionRequest(BaseModel):
    transition_preset: str = "fade_black"
    animation_preset: str = "spring_pop"


class BeatCutRequest(BaseModel):
    bpm: int = Field(default=120, ge=40, le=240)
    align_subtitles: bool = True
    pulse_flash: bool = True


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


class TimelineClipSchema(BaseModel):
    clip_id: str = ""
    track_id: str = "V1"
    label: str = "Clip"
    start_time: float = Field(default=0.0, ge=0.0)
    end_time: float = Field(default=2.0, gt=0.0)
    source_start: float = Field(default=0.0, ge=0.0)
    source_end: float = Field(default=2.0, gt=0.0)
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    transition_in: str = "none"


class ManageTimelineClipRequest(BaseModel):
    action: str = Field(default="add", pattern="^(add|update|split|clone|delete|render)$")
    clip_id: str | None = None
    split_time: float | None = None
    render_timeline: bool = False
    clip: TimelineClipSchema | None = None


class PodcastTurnSchema(BaseModel):
    turn_id: str = ""
    speaker_name: str = "Host"
    voice_id: str = "vi-VN-HoaiMyNeural"
    emotion: str = "warm"
    text: str = ""
    pause_after_ms: int = 350


class PodcastRequest(BaseModel):
    raw_content: str = Field(min_length=1)
    genre: str = Field(default="podcast_dialogue")
    host_voice_id: str = Field(default="vi-VN-HoaiMyNeural")
    guest_voice_id: str = Field(default="vi-VN-NamMinhNeural")
    bgm_volume: float = Field(default=0.14, ge=0.0, le=0.8)


class VoiceDesignRequest(BaseModel):
    name: str = Field(min_length=1)
    prompt_description: str = Field(min_length=2)
    seed: int = 42
    language: str = "vi-VN"


class VoiceCloneRequest(BaseModel):
    name: str = Field(min_length=1)
    reference_audio_path: str = Field(min_length=1)
    consent_verified: bool = False
    language: str = "vi-VN"


class DubbingRequest(BaseModel):
    target_language: str = "vi-VN"
    voice_id: str = "vi-VN-HoaiMyNeural"
    translated_lines: List[str] | None = None


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
    animation_preset: str = "spring_pop"
    transition_preset: str = "fade_black"
    voice_id: str = "vi-VN-HoaiMyNeural"
    bgm_preset: str = "bgm_ambient_pad"
    beat_timestamps: List[float] = Field(default_factory=list)
    scene_context: SceneContextSchema = Field(default_factory=SceneContextSchema)
    characters: List[CharacterProfileSchema] = Field(default_factory=list)
    scenes: List[StorySceneSchema] = Field(default_factory=list)
    timeline_clips: List[TimelineClipSchema] = Field(default_factory=list)
    podcast_turns: List[PodcastTurnSchema] = Field(default_factory=list)
    audit_logs: List[AuditLogEntrySchema] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    supported_engines: List[str]
    tools: dict
