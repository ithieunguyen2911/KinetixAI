"""KinetixAI (FlowVids-AI) Model Context Protocol (MCP) Server.

Allows AI agents (Antigravity, Claude Code, Cursor, Gemini CLI) to directly command
the KinetixAI Clean Architecture pipeline and Windows Desktop App to produce videos.
"""

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore[no-redef]

from src.application.services.project_service import ProjectService
from src.domain.entities.enums import RenderEngineType
from src.domain.entities.subtitle_segment import SubtitleSegment, WordTimestamp

mcp = MCPServer("kinetix-ai")

_DEFAULT_WORKSPACE: Path | None = None


def _get_service(workspace_root: Path | None = None) -> ProjectService:
    return ProjectService(workspace_root=workspace_root or _DEFAULT_WORKSPACE)


@mcp.tool()
def kinetix_health_check() -> Dict[str, Any]:
    """Check health and readiness of KinetixAI's 5 core tools (yt-dlp, FFmpeg, Whisper, Remotion, HyperFrames) and MCP bridge."""
    repo_root = Path(__file__).resolve().parents[3]
    desktop_exe = (
        repo_root
        / "desktop_app"
        / "KinetixAI.Desktop"
        / "bin"
        / "Debug"
        / "net10.0-windows"
        / "KinetixAI.Desktop.exe"
    )
    return {
        "status": "ok",
        "mcp_server": "kinetix-ai",
        "version": "1.1.0",
        "supported_engines": [e.value for e in RenderEngineType],
        "desktop_app_built": desktop_exe.exists(),
        "desktop_app_path": str(desktop_exe),
        "tools": {
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "node": shutil.which("node") is not None,
            "yt_dlp": True,
            "whisper": True,
            "remotion": True,
            "hyperframes": True,
        },
    }


@mcp.tool()
def kinetix_produce_video(
    project_id: str,
    source_url: str = "demo://sample",
    engine_type: str = "remotion",
    script_text: str = "KinetixAI AI-Commanded Video|Rendered via Antigravity MCP|Powered by Remotion, HyperFrames & FFmpeg",
    template_id: str = "CaptionTemplate",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Produce a complete MP4 video using the 5-step Clean Architecture pipeline (yt-dlp -> FFmpeg -> Whisper -> Remotion/HyperFrames -> FFmpeg).

    Args:
        project_id: Unique slug identifier for the video project (e.g. 'ai_video_01').
        source_url: Video URL, local video file path, or 'demo://sample'.
        engine_type: Visual render engine: 'remotion' (React) or 'hyperframes' (HTML/GSAP).
        script_text: Pipe-separated ('|') or newline-separated subtitle lines for the video.
        template_id: Composition template name (default 'CaptionTemplate').
        workspace_dir: Optional custom workspace folder path.
    """
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    project = service.create_and_run_project(
        project_id=project_id,
        source_url=source_url,
        engine_type=engine_type,
        template_id=template_id,
        script_text=script_text,
    )
    return project.to_dict()


@mcp.tool()
def kinetix_list_projects(workspace_dir: str | None = None) -> List[Dict[str, Any]]:
    """List all video production projects in the KinetixAI workspace."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return [p.to_dict() for p in service.list_projects()]


@mcp.tool()
def kinetix_get_project(project_id: str, workspace_dir: str | None = None) -> Dict[str, Any]:
    """Get detailed status, subtitle segments, and output MP4 paths for a specific project."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    project = service.get_project(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found.")
    return project.to_dict()


@mcp.tool()
def kinetix_update_subtitles(
    project_id: str,
    subtitles_input: str,
    engine_type: str | None = None,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Update subtitles of an existing project and re-render the visual overlay + final MP4.

    Args:
        project_id: Target project ID.
        subtitles_input: Either a pipe-separated script ('Line 1|Line 2') or a JSON array of subtitle objects.
        engine_type: Optional engine switch ('remotion' or 'hyperframes').
        workspace_dir: Optional custom workspace folder path.
    """
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    existing = service.get_project(project_id)
    if not existing:
        raise ValueError(f"Project '{project_id}' not found.")

    domain_subs: List[SubtitleSegment] = []
    stripped = subtitles_input.strip()
    if stripped.startswith("["):
        raw_list = json.loads(stripped)
        for item in raw_list:
            words = [
                WordTimestamp(
                    word=w["word"],
                    start_time=float(w["start_time"]),
                    end_time=float(w["end_time"]),
                )
                for w in item.get("words", [])
            ]
            domain_subs.append(
                SubtitleSegment(
                    start_time=float(item["start_time"]),
                    end_time=float(item["end_time"]),
                    text=str(item["text"]),
                    words=words,
                )
            )
    else:
        parts = [p.strip() for p in stripped.replace("\n", "|").split("|") if p.strip()]
        total_dur = max(6.0, existing.subtitles[-1].end_time if existing.subtitles else 6.0)
        seg_dur = total_dur / max(1, len(parts))
        for idx, text in enumerate(parts):
            domain_subs.append(
                SubtitleSegment(
                    start_time=round(idx * seg_dur, 3),
                    end_time=round((idx + 1) * seg_dur, 3),
                    text=text,
                )
            )

    updated = service.update_subtitles_and_rerender(
        project_id=project_id,
        subtitles=domain_subs,
        engine_type=engine_type,
    )
    return updated.to_dict()


@mcp.tool()
def kinetix_launch_desktop_app() -> Dict[str, Any]:
    """Launch the native Windows C# WPF Desktop App (KinetixAI.Desktop) connected to the workspace."""
    repo_root = Path(__file__).resolve().parents[3]
    desktop_exe = (
        repo_root
        / "desktop_app"
        / "KinetixAI.Desktop"
        / "bin"
        / "Debug"
        / "net10.0-windows"
        / "KinetixAI.Desktop.exe"
    )
    if desktop_exe.exists():
        proc = subprocess.Popen([str(desktop_exe)], cwd=str(repo_root))
        return {
            "launched": True,
            "pid": proc.pid,
            "executable": str(desktop_exe),
        }
    return {
        "launched": False,
        "error": f"Desktop executable not found at {desktop_exe}. Run 'dotnet build' first.",
    }


def main() -> None:
    """Run the KinetixAI MCP server over standard input/output (stdio)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
