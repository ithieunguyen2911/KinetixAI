"""IAudioAssetLibrary Abstract Interface for BGM Music Beds & SFX Sound Effects."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class IAudioAssetLibrary(ABC):
    """Domain interface for resolving curated BGM tracks and SFX cues into local WAV assets."""

    @abstractmethod
    def list_bgm_presets(self) -> List[Dict[str, Any]]:
        """List available background music presets (id, name, bpm, mood)."""
        pass

    @abstractmethod
    def list_sfx_presets(self) -> List[Dict[str, Any]]:
        """List available sound effect presets (id, name, category, duration_sec)."""
        pass

    @abstractmethod
    def resolve_bgm(
        self,
        preset_id: str,
        output_dir: Path,
        duration_sec: float = 8.0,
    ) -> Path:
        """Materialize a BGM WAV track into output_dir."""
        pass

    @abstractmethod
    def resolve_sfx(
        self,
        sfx_id: str,
        output_dir: Path,
    ) -> Path:
        """Materialize a sound effect WAV clip into output_dir."""
        pass
