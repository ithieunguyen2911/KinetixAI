"""IVisualAssetGenerator Abstract Interface for AI Storyboard Illustrations & Cinematic B-Roll."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class IVisualAssetGenerator(ABC):
    """Domain interface for resolving or generating 16:9 cinematic storyboard illustrations per scene."""

    @abstractmethod
    def resolve_scene_illustration(
        self,
        scene_id: str,
        title: str,
        visual_prompt: str,
        mood: str,
        output_dir: Path,
        existing_image_path: str | None = None,
    ) -> Path:
        """Resolve an existing scene image or generate a 1280x720 cinematic illustration PNG in output_dir."""
        pass

    def resolve_storyboard_batch(
        self,
        scenes: List[Dict[str, Any]],
        output_dir: Path,
    ) -> List[Dict[str, Any]]:
        """Resolve illustrations for an ordered list of scene dicts and return enriched dicts with 'image_path'."""
        resolved: List[Dict[str, Any]] = []
        for idx, sc in enumerate(scenes, start=1):
            sid = str(sc.get("scene_id") or f"scene_{idx:02d}")
            img = self.resolve_scene_illustration(
                scene_id=sid,
                title=str(sc.get("title") or f"Scene {idx}"),
                visual_prompt=str(sc.get("visual_prompt") or sc.get("narration_text") or ""),
                mood=str(sc.get("mood") or "melancholic"),
                output_dir=output_dir,
                existing_image_path=sc.get("image_path"),
            )
            item = dict(sc)
            item["image_path"] = str(img)
            resolved.append(item)
        return resolved
