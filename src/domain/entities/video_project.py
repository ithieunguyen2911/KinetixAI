"""VideoProject Aggregate Root Domain Entity."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.studio_entities import (
    AuditLogEntry,
    CharacterProfile,
    PodcastTurn,
    SceneContext,
    StoryScene,
    TimelineClip,
)
from src.domain.entities.subtitle_segment import SubtitleSegment


@dataclass
class VideoProject:
    """Aggregate root representing an automated video production, podcast & NLE storyboard project."""

    project_id: str
    source_url: str
    engine_type: RenderEngineType = RenderEngineType.REMOTION
    template_id: str = "CaptionTemplate"
    script_text: str | None = None
    raw_video_path: Path | None = None
    audio_path: Path | None = None
    overlay_video_path: Path | None = None
    subtitles: List[SubtitleSegment] = field(default_factory=list)
    final_output_path: Path | None = None
    status: JobStatus = JobStatus.PENDING
    progress_percent: int = 0
    current_step: str = "Ready"
    error_message: str | None = None
    # v3.0 / v4.0 Studio Storyboard, Character, Podcast, Timeline & Audio properties
    animation_preset: str = "spring_pop"
    transition_preset: str = "fade_black"
    voice_id: str = "vi-VN-HoaiMyNeural"
    bgm_preset: str = "bgm_ambient_pad"
    beat_timestamps: List[float] = field(default_factory=list)
    scene_context: SceneContext = field(default_factory=SceneContext)
    characters: List[CharacterProfile] = field(default_factory=list)
    scenes: List[StoryScene] = field(default_factory=list)
    timeline_clips: List[TimelineClip] = field(default_factory=list)
    podcast_turns: List[PodcastTurn] = field(default_factory=list)
    audit_logs: List[AuditLogEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.project_id = self.project_id.strip()
        self.source_url = self.source_url.strip()
        if not self.project_id:
            raise ValueError("VideoProject.project_id must not be empty.")
        if not self.source_url:
            raise ValueError("VideoProject.source_url must not be empty.")
        if isinstance(self.engine_type, str):
            self.engine_type = RenderEngineType(self.engine_type.lower())
        if isinstance(self.status, str):
            self.status = JobStatus(self.status.lower())
        if not (0 <= self.progress_percent <= 100):
            raise ValueError("VideoProject.progress_percent must be between 0 and 100.")
        if isinstance(self.scene_context, dict):
            self.scene_context = SceneContext.from_dict(self.scene_context)
        if not self.characters:
            self.characters = [
                CharacterProfile(
                    character_id="char_host",
                    name="Minh Anh (Host)",
                    role="Primary Presenter",
                    visual_description="Midnight blue studio blazer, minimal glowing cyan badge, calm studio lighting",
                    voice_id="vi-VN-HoaiMyNeural",
                    theme_color="#3B82F6",
                    avatar_badge="HOST",
                ),
                CharacterProfile(
                    character_id="char_architect",
                    name="Kien Quoc (Architect)",
                    role="Tech Analyst",
                    visual_description="Charcoal turtleneck, titanium glasses, emerald HUD telemetry",
                    voice_id="vi-VN-NamMinhNeural",
                    theme_color="#10B981",
                    avatar_badge="TECH",
                ),
            ]

    def ensure_timeline_clips(self, duration_sec: float = 6.0) -> None:
        """Populate default interactive TimelineClip blocks across V2, V1, S1, A1, B1 if missing."""
        dur = max(1.0, float(duration_sec))
        if not self.timeline_clips:
            clips: List[TimelineClip] = [
                TimelineClip(
                    clip_id="v2_overlay_01",
                    track_id="V2",
                    label=f"{self.engine_type.value.upper()} • {self.template_id}",
                    start_time=0.0,
                    end_time=dur,
                    source_start=0.0,
                    source_end=dur,
                ),
                TimelineClip(
                    clip_id="v1_video_01",
                    track_id="V1",
                    label=f"Master Clip 01 ({dur:.1f}s)",
                    start_time=0.0,
                    end_time=dur,
                    source_start=0.0,
                    source_end=dur,
                ),
                TimelineClip(
                    clip_id="a1_audio_01",
                    track_id="A1",
                    label=f"Voice ({self.voice_id}) + Audio",
                    start_time=0.0,
                    end_time=dur,
                    source_start=0.0,
                    source_end=dur,
                ),
            ]
            for idx, seg in enumerate(self.subtitles, start=1):
                clips.append(
                    TimelineClip(
                        clip_id=f"s1_sub_{idx:02d}",
                        track_id="S1",
                        label=seg.text,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        source_start=seg.start_time,
                        source_end=seg.end_time,
                    )
                )
            for idx, b in enumerate(self.beat_timestamps, start=1):
                clips.append(
                    TimelineClip(
                        clip_id=f"b1_beat_{idx:02d}",
                        track_id="B1",
                        label=f"Beat #{idx}",
                        start_time=b,
                        end_time=min(dur, round(b + 0.25, 3)),
                    )
                )
            self.timeline_clips = clips

    def append_log(self, category: str, action: str, details: str, status: str = "OK") -> None:
        """Append a structured audit log entry while bounding history length to 200 items."""
        entry = AuditLogEntry(
            category=category.upper(),
            action=action,
            details=details,
            status=status.upper(),
        )
        self.audit_logs.append(entry)
        if len(self.audit_logs) > 200:
            self.audit_logs = self.audit_logs[-200:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_url": self.source_url,
            "engine_type": self.engine_type.value,
            "template_id": self.template_id,
            "script_text": self.script_text,
            "raw_video_path": str(self.raw_video_path) if self.raw_video_path else None,
            "audio_path": str(self.audio_path) if self.audio_path else None,
            "overlay_video_path": str(self.overlay_video_path) if self.overlay_video_path else None,
            "subtitles": [s.to_dict() for s in self.subtitles],
            "final_output_path": str(self.final_output_path) if self.final_output_path else None,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "animation_preset": self.animation_preset,
            "transition_preset": self.transition_preset,
            "voice_id": self.voice_id,
            "bgm_preset": self.bgm_preset,
            "beat_timestamps": [round(float(b), 3) for b in self.beat_timestamps],
            "scene_context": self.scene_context.to_dict(),
            "characters": [c.to_dict() for c in self.characters],
            "scenes": [s.to_dict() for s in self.scenes],
            "timeline_clips": [t.to_dict() for t in self.timeline_clips],
            "podcast_turns": [p.to_dict() for p in self.podcast_turns],
            "audit_logs": [a.to_dict() for a in self.audit_logs],
        }
