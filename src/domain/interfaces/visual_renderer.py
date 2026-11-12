"""IVisualRenderer Abstract Interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class IVisualRenderer(ABC):
    """Interface for code-driven visual composition engines (Remotion / HyperFrames)."""

    @abstractmethod
    def render_composition(self, template_id: str, props: Dict[str, Any], output_path: Path) -> Path:
        """Render a visual composition from template_id and JSON props into output_path."""
        pass
