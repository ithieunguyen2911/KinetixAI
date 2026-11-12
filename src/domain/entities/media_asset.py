"""MediaAsset Domain Entity."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class MediaAsset:
    """Metadata for a raw, intermediate, or final media asset."""

    asset_id: str
    file_path: Path
    media_type: str  # "video", "audio", "overlay"
    duration_seconds: float = 0.0
    resolution: str = "1280x720"

    def __post_init__(self) -> None:
        self.asset_id = self.asset_id.strip()
        if not self.asset_id:
            raise ValueError("MediaAsset.asset_id must not be empty.")
        if self.media_type not in {"video", "audio", "overlay"}:
            raise ValueError("MediaAsset.media_type must be 'video', 'audio', or 'overlay'.")
        if self.duration_seconds < 0.0:
            raise ValueError("MediaAsset.duration_seconds must be >= 0.0.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "file_path": str(self.file_path),
            "media_type": self.media_type,
            "duration_seconds": self.duration_seconds,
            "resolution": self.resolution,
        }
