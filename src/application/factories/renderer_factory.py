"""RendererFactory - Factory Pattern for switching between Remotion and HyperFrames."""

from src.domain.entities.enums import RenderEngineType
from src.domain.interfaces.visual_renderer import IVisualRenderer
from src.infrastructure.renderers.hyperframes_adapter import HyperFramesAdapter
from src.infrastructure.renderers.remotion_adapter import RemotionAdapter


class RendererFactory:
    """Factory Pattern enabling instant switching between Remotion and HyperFrames."""

    @staticmethod
    def get_renderer(engine_type: RenderEngineType | str) -> IVisualRenderer:
        if isinstance(engine_type, str):
            try:
                engine_type = RenderEngineType(engine_type.lower())
            except ValueError as exc:
                raise ValueError(f"Unsupported engine: {engine_type}") from exc

        if engine_type == RenderEngineType.REMOTION:
            return RemotionAdapter()
        if engine_type == RenderEngineType.HYPERFRAMES:
            return HyperFramesAdapter()
        raise ValueError(f"Unsupported engine: {engine_type}")
