"""IVoiceSynthesizer Abstract Interface for Multi-Language Neural & Studio TTS."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class IVoiceSynthesizer(ABC):
    """Domain interface for Text-to-Speech voiceover generation (edge-tts / Windows SAPI)."""

    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """Return available curated voice presets with locale, gender, and style metadata."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_id: str = "vi-VN-HoaiMyNeural",
        rate: float = 1.0,
        pitch_hz: int = 0,
    ) -> Path:
        """Synthesize spoken voiceover WAV/MP3 from text into output_path."""
        pass
