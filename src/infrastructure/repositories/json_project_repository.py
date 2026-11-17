"""JsonProjectRepository - Hot-reloading file-backed state store for VideoProjects (v5.0)."""

import json
from pathlib import Path
from typing import Dict, List

from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.studio_entities import (
    AuditLogEntry,
    CharacterProfile,
    PodcastTurn,
    SceneContext,
    StoryScene,
    TimelineClip,
)
from src.domain.entities.subtitle_segment import SubtitleSegment, WordTimestamp
from src.domain.entities.video_project import VideoProject


class JsonProjectRepository:
    """Persists VideoProject state with mtime-based hot reload and per-item fault isolation."""

    def __init__(self, storage_file: Path) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, VideoProject] = {}
        self._last_mtime_ns: int = 0
        self._load()

    def _reload_if_changed(self) -> None:
        if not self.storage_file.exists():
            if self._last_mtime_ns != 0:
                self._cache = {}
                self._last_mtime_ns = 0
            return
        try:
            mtime_ns = self.storage_file.stat().st_mtime_ns
        except OSError:
            return
        if mtime_ns != self._last_mtime_ns:
            self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            self._cache = {}
            self._last_mtime_ns = 0
            return
        try:
            stat_before = self.storage_file.stat()
            raw_list = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except Exception:
            return

        if not isinstance(raw_list, list):
            return

        fresh_cache: Dict[str, VideoProject] = {}
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            try:
                proj = self._from_dict(item)
                fresh_cache[proj.project_id] = proj
            except Exception:
                continue

        self._cache = fresh_cache
        try:
            self._last_mtime_ns = self.storage_file.stat().st_mtime_ns
        except OSError:
            self._last_mtime_ns = stat_before.st_mtime_ns

    def _save_to_disk(self) -> None:
        payload = [proj.to_dict() for proj in self._cache.values()]
        self.storage_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            self._last_mtime_ns = self.storage_file.stat().st_mtime_ns
        except OSError:
            pass

    def save(self, project: VideoProject) -> VideoProject:
        self._reload_if_changed()
        self._cache[project.project_id] = project
        self._save_to_disk()
        return project

    def get(self, project_id: str) -> VideoProject | None:
        self._reload_if_changed()
        return self._cache.get(project_id)

    def delete(self, project_id: str) -> bool:
        self._reload_if_changed()
        if project_id in self._cache:
            del self._cache[project_id]
            self._save_to_disk()
            return True
        return False

    def list_all(self) -> List[VideoProject]:
        self._reload_if_changed()
        return list(self._cache.values())

    @staticmethod
    def _from_dict(data: dict) -> VideoProject:
        subtitles: List[SubtitleSegment] = []
        for s in data.get("subtitles", []):
            words = [
                WordTimestamp(
                    word=w["word"],
                    start_time=float(w["start_time"]),
                    end_time=float(w["end_time"]),
                )
                for w in s.get("words", [])
            ]
            subtitles.append(
                SubtitleSegment(
                    start_time=float(s["start_time"]),
                    end_time=float(s["end_time"]),
                    text=str(s["text"]),
                    words=words,
                )
            )
        characters = [CharacterProfile.from_dict(c) for c in data.get("characters", [])]
        scenes = [StoryScene.from_dict(sc) for sc in data.get("scenes", [])]
        timeline_clips = [TimelineClip.from_dict(tc) for tc in data.get("timeline_clips", [])]
        podcast_turns = [PodcastTurn.from_dict(pt) for pt in data.get("podcast_turns", [])]
        audit_logs = [AuditLogEntry.from_dict(a) for a in data.get("audit_logs", [])]
        scene_context = SceneContext.from_dict(data.get("scene_context"))

        return VideoProject(
            project_id=str(data["project_id"]),
            source_url=str(data["source_url"]),
            engine_type=RenderEngineType(str(data.get("engine_type", "remotion")).lower()),
            template_id=str(data.get("template_id", "CaptionTemplate")),
            script_text=data.get("script_text"),
            raw_video_path=Path(data["raw_video_path"]) if data.get("raw_video_path") else None,
            audio_path=Path(data["audio_path"]) if data.get("audio_path") else None,
            overlay_video_path=Path(data["overlay_video_path"]) if data.get("overlay_video_path") else None,
            subtitles=subtitles,
            final_output_path=Path(data["final_output_path"]) if data.get("final_output_path") else None,
            status=JobStatus(str(data.get("status", "pending")).lower()),
            progress_percent=int(data.get("progress_percent", 0)),
            current_step=str(data.get("current_step", "Ready")),
            error_message=data.get("error_message"),
            animation_preset=str(data.get("animation_preset", "spring_pop")),
            transition_preset=str(data.get("transition_preset", "fade_black")),
            voice_id=str(data.get("voice_id", "vi-VN-HoaiMyNeural")),
            bgm_preset=str(data.get("bgm_preset", "bgm_ambient_pad")),
            beat_timestamps=[float(b) for b in data.get("beat_timestamps", [])],
            scene_context=scene_context,
            characters=characters,
            scenes=scenes,
            timeline_clips=timeline_clips,
            podcast_turns=podcast_turns,
            audit_logs=audit_logs,
        )
