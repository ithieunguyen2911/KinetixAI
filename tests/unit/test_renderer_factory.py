"""Unit tests for RendererFactory and Visual Render Adapters."""

import pytest

from src.application.factories.renderer_factory import RendererFactory
from src.domain.entities.enums import RenderEngineType
from src.infrastructure.renderers.hyperframes_adapter import HyperFramesAdapter
from src.infrastructure.renderers.remotion_adapter import RemotionAdapter


def test_renderer_factory_returns_remotion_adapter() -> None:
    renderer = RendererFactory.get_renderer(RenderEngineType.REMOTION)
    assert isinstance(renderer, RemotionAdapter)
    renderer_str = RendererFactory.get_renderer("remotion")
    assert isinstance(renderer_str, RemotionAdapter)


def test_renderer_factory_returns_hyperframes_adapter() -> None:
    renderer = RendererFactory.get_renderer(RenderEngineType.HYPERFRAMES)
    assert isinstance(renderer, HyperFramesAdapter)
    renderer_str = RendererFactory.get_renderer("hyperframes")
    assert isinstance(renderer_str, HyperFramesAdapter)


def test_renderer_factory_raises_for_invalid_engine() -> None:
    with pytest.raises(ValueError, match="Unsupported engine"):
        RendererFactory.get_renderer("invalid_engine")
