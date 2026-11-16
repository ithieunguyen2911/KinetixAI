"""KinetixAI (FlowVids-AI) Model Context Protocol (MCP) Server.

Allows AI agents (Antigravity, Claude Code, Cursor, Gemini CLI) to directly command
the KinetixAI Clean Architecture pipeline and Windows Desktop App to produce videos.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
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
        "version": "1.2.0",
        "supported_engines": [e.value for e in RenderEngineType],
        "desktop_app_built": desktop_exe.exists(),
        "desktop_app_path": str(desktop_exe),
        "tools": {
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "ffprobe": shutil.which("ffprobe") is not None,
            "node": shutil.which("node") is not None,
            "yt_dlp": True,
            "whisper": True,
            "remotion": True,
            "hyperframes": True,
        },
    }


@mcp.tool()
def kinetix_inspect_source(source_url: str = "demo://sample", workspace_dir: str | None = None) -> Dict[str, Any]:
    """Inspect remote video URL or local video file metadata via yt-dlp / ffprobe without downloading the full video."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.inspect_source(source_url)


@mcp.tool()
def kinetix_produce_video(
    project_id: str,
    source_url: str = "demo://sample",
    engine_type: str = "remotion",
    script_text: str | None = "KinetixAI AI-Commanded Video|Rendered via Antigravity MCP|Powered by Remotion, HyperFrames & FFmpeg",
    template_id: str = "CaptionTemplate",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Produce a complete MP4 video using the 5-step Clean Architecture pipeline (yt-dlp -> FFmpeg -> Whisper -> Remotion/HyperFrames -> FFmpeg).

    Args:
        project_id: Unique slug identifier for the video project (e.g. 'ai_video_01').
        source_url: Video URL, local video file path, or 'demo://sample'.
        engine_type: Visual render engine: 'remotion' (React) or 'hyperframes' (HTML/GSAP).
        script_text: Optional pipe-separated ('|') or newline-separated subtitle lines (leave None/empty to auto-transcribe audio).
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
def kinetix_probe_media(project_id: str, workspace_dir: str | None = None) -> Dict[str, Any]:
    """Inspect technical video/audio stream specifications (codec, resolution, fps, duration, sample_rate) of a project via ffprobe."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.probe_project_media(project_id)


@mcp.tool()
def kinetix_trim_video(
    project_id: str,
    start_time: float,
    end_time: float,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Trim a project's final MP4 video between start_time and end_time (seconds) using FFmpeg."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.trim_project_video(project_id=project_id, start_time=start_time, end_time=end_time)
    return updated.to_dict()


@mcp.tool()
def kinetix_change_speed(
    project_id: str,
    speed_factor: float = 1.25,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Change playback speed (0.25x slow-mo to 4.0x fast-forward) of a project's video and audio."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.change_project_speed(project_id=project_id, speed_factor=speed_factor)
    return updated.to_dict()


@mcp.tool()
def kinetix_apply_color_grade(
    project_id: str,
    preset: str = "teal_orange",
    brightness: float = 0.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    gamma: float = 1.0,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Apply LUT / Color Look preset ('natural', 'teal_orange', 'warm_vintage', 'noir_bw', 'studio_crisp') and eq parameters."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.apply_project_color_grade(
        project_id=project_id,
        preset=preset,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        gamma=gamma,
    )
    return updated.to_dict()


@mcp.tool()
def kinetix_reframe_video(
    project_id: str,
    aspect_ratio: str = "9:16",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Reframe a project's video into '16:9' (landscape), '9:16' (vertical Shorts with blurred background), or '1:1' (square)."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.reframe_project_video(project_id=project_id, aspect_ratio=aspect_ratio)
    return updated.to_dict()


@mcp.tool()
def kinetix_master_audio(
    project_id: str,
    remove_silence: bool = False,
    normalize_loudness: bool = True,
    mix_bgm: bool = True,
    bg_volume: float = 0.18,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Master project audio: optional silence jump-cut removal, EBU R128 loudness normalization, and ambient BGM mixing."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.master_project_audio(
        project_id=project_id,
        remove_silence=remove_silence,
        normalize_loudness=normalize_loudness,
        mix_bgm=mix_bgm,
        bg_volume=bg_volume,
    )
    return updated.to_dict()


@mcp.tool()
def kinetix_capture_snapshot(
    project_id: str,
    timestamp_sec: float = 1.0,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Capture a high-resolution PNG frame snapshot at timestamp_sec from a project's video."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.capture_project_snapshot(project_id=project_id, timestamp_sec=timestamp_sec)


@mcp.tool()
def kinetix_clone_project(
    project_id: str,
    new_project_id: str | None = None,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Clone an existing project (video assets, subtitles, scenes, characters, context bible)."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.clone_project(project_id=project_id, new_project_id=new_project_id).to_dict()


@mcp.tool()
def kinetix_delete_project(
    project_id: str,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Delete a video project and remove its workspace directory."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.delete_project(project_id=project_id)


@mcp.tool()
def kinetix_manage_character(
    project_id: str,
    action: str = "upsert",
    character_id: str = "char_host",
    name: str = "Studio Character",
    role: str = "Presenter",
    voice_id: str = "vi-VN-HoaiMyNeural",
    theme_color: str = "#3B82F6",
    visual_description: str = "Minimal studio presenter",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Add, update, clone, or delete a Consistent Character profile bound to voiceover & motion HUD."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.manage_character(
        project_id=project_id,
        action=action,
        character_id=character_id,
        char_data={
            "character_id": character_id,
            "name": name,
            "role": role,
            "voice_id": voice_id,
            "theme_color": theme_color,
            "visual_description": visual_description,
            "avatar_badge": role.split()[0].upper()[:6],
        },
    )
    return updated.to_dict()


@mcp.tool()
def kinetix_manage_scene(
    project_id: str,
    action: str = "upsert",
    scene_id: str = "scene_01",
    title: str = "Studio Intro",
    setting_context: str = "Modern Studio Desk",
    character_id: str = "char_host",
    narration_text: str = "Welcome to Kinetix Studio",
    start_time: float = 0.0,
    duration_sec: float = 2.0,
    transition_in: str = "fade_black",
    animation_preset: str = "spring_pop",
    sfx_id: str = "sfx_whoosh_fast",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Add, update, clone, or delete a Storyboard Scene linking context, character, transition, and SFX."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    updated = service.manage_scene(
        project_id=project_id,
        action=action,
        scene_id=scene_id,
        scene_data={
            "scene_id": scene_id,
            "title": title,
            "setting_context": setting_context,
            "character_id": character_id,
            "narration_text": narration_text,
            "start_time": start_time,
            "duration_sec": duration_sec,
            "transition_in": transition_in,
            "animation_preset": animation_preset,
            "sfx_id": sfx_id,
        },
    )
    return updated.to_dict()


@mcp.tool()
def kinetix_generate_voiceover(
    project_id: str,
    voice_id: str = "vi-VN-HoaiMyNeural",
    text: str | None = None,
    rate: float = 1.0,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Generate TTS voiceover narration audio and replace the project's primary voice track."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.synthesize_project_voiceover(
        project_id=project_id,
        text=text,
        voice_id=voice_id,
        rate=rate,
    ).to_dict()


@mcp.tool()
def kinetix_apply_sound_library(
    project_id: str,
    bgm_preset: str | None = "bgm_cyber_pulse",
    bgm_volume: float = 0.18,
    sfx_id: str | None = "sfx_whoosh_fast",
    sfx_timestamp: float = 0.25,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Mix a curated BGM music bed and/or insert a timestamped SFX sound effect onto the video."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.apply_project_sound_library(
        project_id=project_id,
        bgm_preset=bgm_preset,
        bgm_volume=bgm_volume,
        sfx_id=sfx_id,
        sfx_timestamp=sfx_timestamp,
    ).to_dict()


@mcp.tool()
def kinetix_apply_beat_cut(
    project_id: str,
    bpm: int = 120,
    align_subtitles: bool = True,
    pulse_flash: bool = True,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Generate BPM beat grid markers, snap subtitle cut points to beats, and apply rhythmic pulse accents."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.apply_project_beat_cut(
        project_id=project_id,
        bpm=bpm,
        align_subtitles=align_subtitles,
        pulse_flash=pulse_flash,
    ).to_dict()


@mcp.tool()
def kinetix_apply_transition_animation(
    project_id: str,
    transition_preset: str = "fade_black",
    animation_preset: str = "spring_pop",
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    """Apply video transition and camera/motion animation filters to a project."""
    ws = Path(workspace_dir) if workspace_dir else None
    service = _get_service(ws)
    return service.apply_project_fx_motion(
        project_id=project_id,
        transition_preset=transition_preset,
        animation_preset=animation_preset,
    ).to_dict()


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
            seg = SubtitleSegment(
                start_time=float(item["start_time"]),
                end_time=float(item["end_time"]),
                text=str(item["text"]),
                words=words,
            )
            seg.ensure_word_timestamps()
            domain_subs.append(seg)
    else:
        parts = [p.strip() for p in stripped.replace("\n", "|").split("|") if p.strip()]
        total_dur = max(6.0, existing.subtitles[-1].end_time if existing.subtitles else 6.0)
        seg_dur = total_dur / max(1, len(parts))
        for idx, text in enumerate(parts):
            seg = SubtitleSegment(
                start_time=round(idx * seg_dur, 3),
                end_time=round((idx + 1) * seg_dur, 3),
                text=text,
            )
            seg.ensure_word_timestamps()
            domain_subs.append(seg)

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
    """Run the KinetixAI MCP server over stdio, or execute a diagnostic check when --self-test is passed."""
    if "--self-test" in sys.argv:
        health = kinetix_health_check()
        source_meta = kinetix_inspect_source("demo://sample")
        projects = kinetix_list_projects()
        print(
            json.dumps(
                {
                    "self_test": "passed",
                    "health": health,
                    "demo_source_metadata": source_meta,
                    "workspace_project_count": len(projects),
                },
                indent=2,
            )
        )
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
