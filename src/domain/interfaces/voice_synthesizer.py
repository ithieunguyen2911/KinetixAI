"""IVoiceSynthesizer Abstract Interface for Neural TTS, Voice Cloning, Voice Design & Podcast Synthesis."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Tuple


class IVoiceSynthesizer(ABC):
    """Domain interface for VoiceStudio-inspired Text-to-Speech, Cloning, Design & Multi-Voice Podcast synthesis."""

    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """Return available curated built-in and custom voice presets."""
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
        """Synthesize spoken voiceover WAV from text (parsing VoiceStudio tags) into output_path."""
        pass

    def design_voice(
        self,
        name: str,
        prompt_description: str,
        seed: int = 42,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Design and persist a synthetic VoiceProfile from natural-language traits + deterministic seed."""
        raise NotImplementedError("design_voice is not implemented.")

    def clone_voice(
        self,
        name: str,
        reference_audio_path: Path,
        consent_verified: bool = False,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Extract acoustic profile from clean reference audio (enforcing explicit consent) and save profile."""
        raise NotImplementedError("clone_voice is not implemented.")

    def list_custom_profiles(self) -> List[Dict[str, Any]]:
        """Return saved VoiceDesign and VoiceCloning profiles."""
        return []

    def synthesize_podcast_script(
        self,
        turns: List[Dict[str, Any]],
        output_path: Path,
        genre: str = "podcast_dialogue",
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        """Synthesize multi-voice expressive turns, stitch pauses, and return (wav_path, timed_segments)."""
        raise NotImplementedError("synthesize_podcast_script is not implemented.")
