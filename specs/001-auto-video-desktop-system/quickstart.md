# Quickstart & Validation Guide: KinetixAI (FlowVids-AI) v3.0 Studio

## 1. Run Full Unit & Integration Test Suite
```powershell
uv run pytest -v
```

## 2. Verify Studio Catalog & MCP Server Self-Test
```powershell
uv run python -m src.presentation.mcp.mcp_server --self-test
```

## 3. Launch Native Windows WPF Workstation v6.1
```powershell
.\run_desktop.ps1
```

## 4. Verify FullScreen Cinema Mode in Desktop App (US14)
1. In `Kinetix Studio` Desktop, select any project with an exported MP4 (e.g. `tap_01_tuoi_30_podcast`).
2. In the **Program Monitor Transport Deck**, click the new **"⛶ Toàn Màn Hình"** button, press `F11`, or double-click the video screen.
3. Observe the borderless Cinema Fullscreen Window:
   - Video renders at native 1080p/4K monitor resolution with black bars (`Stretch="Uniform"`).
   - Glass HUD docked at the bottom displays real-time timecode (`mm:ss.ff`), scrubber slider, play/pause state, volume slider, and resolution badge (`1280x720 • 30fps`).
4. Keep the mouse still for 2.5 seconds:
   - The HUD smoothly fades to `Opacity=0.0` for 100% unobstructed viewing of subtitles and Ken Burns visuals.
5. Move the mouse:
   - The HUD immediately fades back in.
6. Test keyboard navigation:
   - `Space`: Toggles Play / Pause.
   - `←` / `→`: Jumps backward / forward 5 seconds.
   - `M`: Toggles audio mute.
   - `Esc` or `F11`: Closes FullScreen mode and returns to `MainWindow` with playhead position preserved.
