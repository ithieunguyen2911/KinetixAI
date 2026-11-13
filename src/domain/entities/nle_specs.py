"""Non-Linear Editing (NLE) Specification Value Objects."""

from dataclasses import dataclass
from typing import Any, Dict

from src.domain.entities.enums import ColorLookPreset


@dataclass
class ColorGradeSpec:
    """Represents color grading and visual filter parameters for NLE processing."""

    preset: ColorLookPreset = ColorLookPreset.NATURAL
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0

    def __post_init__(self) -> None:
        if isinstance(self.preset, str):
            self.preset = ColorLookPreset(self.preset.lower())
        if not (-1.0 <= self.brightness <= 1.0):
            raise ValueError("ColorGradeSpec.brightness must be between -1.0 and 1.0.")
        if not (0.2 <= self.contrast <= 3.0):
            raise ValueError("ColorGradeSpec.contrast must be between 0.2 and 3.0.")
        if not (0.0 <= self.saturation <= 3.0):
            raise ValueError("ColorGradeSpec.saturation must be between 0.0 and 3.0.")
        if not (0.2 <= self.gamma <= 3.0):
            raise ValueError("ColorGradeSpec.gamma must be between 0.2 and 3.0.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preset": self.preset.value,
            "brightness": round(float(self.brightness), 2),
            "contrast": round(float(self.contrast), 2),
            "saturation": round(float(self.saturation), 2),
            "gamma": round(float(self.gamma), 2),
        }
