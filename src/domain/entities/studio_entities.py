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
    """Storyboard scene segment binding context, character, voiceover line, transition & SFX."""

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
