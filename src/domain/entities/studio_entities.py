"""Studio Storyboard, Context Bible, Consistent Character & Audit Log Domain Entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class SceneContext:
    """Global world setting, visual art direction, and continuity bible across all scenes."""

    world_setting: str = "Modern AI Production Studio — Dark Slate Workstation"
    visual_style: str = "Cinematic Clean UI, Subtle Tech Grid, High Broadcast Contrast"
    lighting_mood: str = "Cool Cobalt Rim Light + Crisp Key Fill"
    camera_lens: str = "35mm Anamorphic Studio Framing"
    continuity_notes: str = "Maintain consistent character badge colors, voice tone, and subtitle styling."

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "SceneContext":
        if not data:
            return cls()
        return cls(
            world_setting=str(data.get("world_setting") or cls.world_setting),
            visual_style=str(data.get("visual_style") or cls.visual_style),
            lighting_mood=str(data.get("lighting_mood") or cls.lighting_mood),
            camera_lens=str(data.get("camera_lens") or cls.camera_lens),
            continuity_notes=str(data.get("continuity_notes") or cls.continuity_notes),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_setting": self.world_setting,
            "visual_style": self.visual_style,
            "lighting_mood": self.lighting_mood,
            "camera_lens": self.camera_lens,
            "continuity_notes": self.continuity_notes,
        }


@dataclass
class CharacterProfile:
    """Reusable Consistent Character identity bound to voiceover & motion HUD styling."""

    character_id: str
    name: str
    role: str = "Presenter"
    visual_description: str = "Dark navy blazer, sleek studio mic, cyan accents"
    voice_id: str = "vi-VN-HoaiMyNeural"
    theme_color: str = "#3B82F6"
    avatar_badge: str = "HOST"

    def __post_init__(self) -> None:
        self.character_id = self.character_id.strip() or f"char_{uuid.uuid4().hex[:6]}"
        self.name = self.name.strip() or "Studio Character"
        if not self.avatar_badge.strip():
            self.avatar_badge = self.name[:6].upper()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterProfile":
        return cls(
            character_id=str(data.get("character_id") or f"char_{uuid.uuid4().hex[:6]}"),
            name=str(data.get("name") or "Studio Character"),
            role=str(data.get("role") or "Presenter"),
            visual_description=str(data.get("visual_description") or ""),
            voice_id=str(data.get("voice_id") or "vi-VN-HoaiMyNeural"),
            theme_color=str(data.get("theme_color") or "#3B82F6"),
            avatar_badge=str(data.get("avatar_badge") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "role": self.role,
            "visual_description": self.visual_description,
            "voice_id": self.voice_id,
            "theme_color": self.theme_color,
            "avatar_badge": self.avatar_badge,
        }


@dataclass
class StoryScene:
    """Storyboard scene segment binding context, character, voiceover line, transition, SFX & visual illustration."""

    scene_id: str
    title: str
    setting_context: str = "Main Studio Desk"
    character_id: str = "char_host"
    narration_text: str = ""
    start_time: float = 0.0
    duration_sec: float = 2.0
    transition_in: str = "fade_black"
    animation_preset: str = "spring_pop"
    sfx_id: str = "sfx_whoosh_fast"
    visual_prompt: str = ""
    image_path: str | None = None

    def __post_init__(self) -> None:
        self.scene_id = self.scene_id.strip() or f"scene_{uuid.uuid4().hex[:5]}"
        self.title = self.title.strip() or "Untitled Scene"
        self.start_time = max(0.0, float(self.start_time))
        self.duration_sec = max(0.2, float(self.duration_sec))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryScene":
        return cls(
            scene_id=str(data.get("scene_id") or f"scene_{uuid.uuid4().hex[:5]}"),
            title=str(data.get("title") or "Untitled Scene"),
            setting_context=str(data.get("setting_context") or "Main Studio Desk"),
            character_id=str(data.get("character_id") or "char_host"),
            narration_text=str(data.get("narration_text") or ""),
            start_time=float(data.get("start_time") or 0.0),
            duration_sec=float(data.get("duration_sec") or 2.0),
            transition_in=str(data.get("transition_in") or "fade_black"),
            animation_preset=str(data.get("animation_preset") or "spring_pop"),
            sfx_id=str(data.get("sfx_id") or "sfx_whoosh_fast"),
            visual_prompt=str(data.get("visual_prompt") or ""),
            image_path=str(data["image_path"]) if data.get("image_path") else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "setting_context": self.setting_context,
            "character_id": self.character_id,
            "narration_text": self.narration_text,
            "start_time": round(self.start_time, 3),
            "duration_sec": round(self.duration_sec, 3),
            "transition_in": self.transition_in,
            "animation_preset": self.animation_preset,
            "sfx_id": self.sfx_id,
            "visual_prompt": self.visual_prompt,
            "image_path": self.image_path,
        }


@dataclass
class AuditLogEntry:
    """Structured activity & NLE context ledger entry for traceability."""

    action: str
    details: str
    category: str = "PIPELINE"
    status: str = "OK"
    timestamp: str = ""
    log_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.log_id:
            self.log_id = uuid.uuid4().hex[:8]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLogEntry":
        return cls(
            log_id=str(data.get("log_id") or uuid.uuid4().hex[:8]),
            timestamp=str(data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            category=str(data.get("category") or "PIPELINE"),
            action=str(data.get("action") or "Operation"),
            details=str(data.get("details") or ""),
            status=str(data.get("status") or "OK"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp,
            "category": self.category,
            "action": self.action,
            "details": self.details,
            "status": self.status,
        }


@dataclass
class TimelineClip:
    """Interactive Multi-Track NLE Timeline clip block supporting Add, Edit, Split, Clone, and Delete."""

    clip_id: str
    track_id: str = "V1"
    label: str = "Clip"
    start_time: float = 0.0
    end_time: float = 2.0
    source_start: float = 0.0
    source_end: float = 2.0
    speed: float = 1.0
    volume: float = 1.0
    transition_in: str = "none"

    def __post_init__(self) -> None:
        self.clip_id = self.clip_id.strip() or f"clip_{uuid.uuid4().hex[:6]}"
        self.track_id = self.track_id.strip().upper() or "V1"
        self.label = self.label.strip() or f"{self.track_id} Clip"
        self.start_time = max(0.0, float(self.start_time))
        self.end_time = max(self.start_time + 0.1, float(self.end_time))
        self.source_start = max(0.0, float(self.source_start))
        self.source_end = max(self.source_start + 0.1, float(self.source_end))
        self.speed = max(0.25, min(4.0, float(self.speed)))
        self.volume = max(0.0, min(2.0, float(self.volume)))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineClip":
        st = float(data.get("start_time") or 0.0)
        en = float(data.get("end_time") or (st + 2.0))
        return cls(
            clip_id=str(data.get("clip_id") or f"clip_{uuid.uuid4().hex[:6]}"),
            track_id=str(data.get("track_id") or "V1"),
            label=str(data.get("label") or "Clip"),
            start_time=st,
            end_time=en,
            source_start=float(data.get("source_start") if data.get("source_start") is not None else st),
            source_end=float(data.get("source_end") if data.get("source_end") is not None else en),
            speed=float(data.get("speed") or 1.0),
            volume=float(data.get("volume") if data.get("volume") is not None else 1.0),
            transition_in=str(data.get("transition_in") or "none"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "track_id": self.track_id,
            "label": self.label,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "source_start": round(self.source_start, 3),
            "source_end": round(self.source_end, 3),
            "speed": round(self.speed, 2),
            "volume": round(self.volume, 2),
            "transition_in": self.transition_in,
        }


@dataclass
class VoiceProfile:
    """Reusable VoiceStudio AI Voice Cloning & Seeded Voice Design profile."""

    profile_id: str
    name: str
    mode: str = "designed"  # builtin | designed | cloned
    base_voice_id: str = "vi-VN-HoaiMyNeural"
    prompt_description: str = ""
    seed: int = 42
    pitch_hz: int = 0
    rate: float = 1.0
    warmth_eq: float = 0.0
    emotion_style: str = "warm"
    reference_audio_path: str | None = None
    consent_verified: bool = True

    def __post_init__(self) -> None:
        self.profile_id = self.profile_id.strip() or f"vp_{uuid.uuid4().hex[:6]}"
        self.name = self.name.strip() or "Custom Studio Voice"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceProfile":
        return cls(
            profile_id=str(data.get("profile_id") or f"vp_{uuid.uuid4().hex[:6]}"),
            name=str(data.get("name") or "Custom Studio Voice"),
            mode=str(data.get("mode") or "designed"),
            base_voice_id=str(data.get("base_voice_id") or "vi-VN-HoaiMyNeural"),
            prompt_description=str(data.get("prompt_description") or ""),
            seed=int(data.get("seed") or 42),
            pitch_hz=int(data.get("pitch_hz") or 0),
            rate=float(data.get("rate") or 1.0),
            warmth_eq=float(data.get("warmth_eq") or 0.0),
            emotion_style=str(data.get("emotion_style") or "warm"),
            reference_audio_path=data.get("reference_audio_path"),
            consent_verified=bool(data.get("consent_verified", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "mode": self.mode,
            "base_voice_id": self.base_voice_id,
            "prompt_description": self.prompt_description,
            "seed": self.seed,
            "pitch_hz": self.pitch_hz,
            "rate": round(self.rate, 2),
            "warmth_eq": round(self.warmth_eq, 2),
            "emotion_style": self.emotion_style,
            "reference_audio_path": self.reference_audio_path,
            "consent_verified": self.consent_verified,
        }


@dataclass
class PodcastTurn:
    """Single conversational / storytelling turn in a multi-voice Podcast or Audiobook."""

    turn_id: str
    speaker_name: str
    voice_id: str = "vi-VN-HoaiMyNeural"
    emotion: str = "warm"
    text: str = ""
    pause_after_ms: int = 350

    def __post_init__(self) -> None:
        self.turn_id = self.turn_id.strip() or f"turn_{uuid.uuid4().hex[:5]}"
        self.speaker_name = self.speaker_name.strip() or "Host"
        self.text = self.text.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PodcastTurn":
        return cls(
            turn_id=str(data.get("turn_id") or f"turn_{uuid.uuid4().hex[:5]}"),
            speaker_name=str(data.get("speaker_name") or "Host"),
            voice_id=str(data.get("voice_id") or "vi-VN-HoaiMyNeural"),
            emotion=str(data.get("emotion") or "warm"),
            text=str(data.get("text") or ""),
            pause_after_ms=int(data.get("pause_after_ms") or 350),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "speaker_name": self.speaker_name,
            "voice_id": self.voice_id,
            "emotion": self.emotion,
            "text": self.text,
            "pause_after_ms": self.pause_after_ms,
        }
