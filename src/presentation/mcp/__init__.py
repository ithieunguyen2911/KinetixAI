"""Model Context Protocol (MCP) Server Package for KinetixAI."""

from src.presentation.mcp.mcp_server import (
    kinetix_get_project,
    kinetix_health_check,
    kinetix_launch_desktop_app,
    kinetix_list_projects,
    kinetix_produce_video,
    kinetix_update_subtitles,
    mcp,
)

__all__ = [
    "mcp",
    "kinetix_produce_video",
    "kinetix_list_projects",
    "kinetix_get_project",
    "kinetix_update_subtitles",
    "kinetix_launch_desktop_app",
    "kinetix_health_check",
]
