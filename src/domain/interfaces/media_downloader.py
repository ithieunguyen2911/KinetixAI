"""IMediaDownloader Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class IMediaDownloader(ABC):
    """Interface for downloading or ingesting source video assets."""

    @abstractmethod
    def download(
        self,
        url: str,
        output_dir: Path,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> Path:
        """Download source video from URL or local/demo URI into output_dir."""
        pass

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Inspect remote URL or local media metadata without downloading the full stream."""
        return {
            "id": "unknown",
            "title": url,
            "duration": 0.0,
            "resolution": "1280x720",
            "fps": 30,
            "source_type": "generic",
        }
