"""IMediaDownloader Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class IMediaDownloader(ABC):
    """Interface for downloading or ingesting source video assets."""

    @abstractmethod
    def download(self, url: str, output_dir: Path) -> Path:
        """Download source video from URL or local/demo URI into output_dir."""
        pass
