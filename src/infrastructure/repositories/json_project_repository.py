"""JsonProjectRepository - File-backed state store for VideoProjects."""

import json
from pathlib import Path
from typing import Dict, List

from src.domain.entities.enums import JobStatus, RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment, WordTimestamp
from src.domain.entities.video_project import VideoProject


class JsonProjectRepository:
    """Persists VideoProject state into a workspace JSON file."""

    def __init__(self, storage_file: Path) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, VideoProject] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            return
        try:
            raw_list = json.loads(self.storage_file.read_text(encoding="utf-8"))
            for item in raw_list:
                proj = self._from_dict(item)
                self._cache[proj.project_id] = proj
        except Exception:
            self._cache = {}

    def _save_to_disk(self) -> None:
        payload = [proj.to_dict() for proj in self._cache.values()]
        self.storage_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def save(self, project: VideoProject) -> VideoProject:
        self._cache[project.project_id] = project
        self._save_to_disk()
        return project

    def get(self, project_id: str) -> VideoProject | None:
        return self._cache.get(project_id)

    def list_all(self) -> List[VideoProject]:
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
        )
