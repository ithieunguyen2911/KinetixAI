"""Integration tests for FastAPI REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


def test_fastapi_health_and_project_lifecycle(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)

    # 1. Health endpoint
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "ok"
    assert "remotion" in health_data["supported_engines"]
    assert "hyperframes" in health_data["supported_engines"]

    # 1b. Inspect source metadata endpoint
    inspect_res = client.post("/api/v1/sources/inspect", json={"source_url": "demo://sample"})
    assert inspect_res.status_code == 200
    assert inspect_res.json()["source_type"] == "demo"
    assert inspect_res.json()["resolution"] == "1280x720"

    # 2. Create and run project via POST /api/v1/projects
    create_res = client.post(
        "/api/v1/projects",
        json={
            "project_id": "api_test_01",
            "source_url": "demo://sample",
            "engine_type": "hyperframes",
            "template_id": "CaptionTemplate",
            "script_text": "API Line 1|API Line 2",
        },
    )
    assert create_res.status_code == 200
    proj_data = create_res.json()
    assert proj_data["project_id"] == "api_test_01"
    assert proj_data["status"] == "completed"
    assert proj_data["progress_percent"] == 100
    assert len(proj_data["subtitles"]) == 2

    # 3. Get project details
    get_res = client.get("/api/v1/projects/api_test_01")
    assert get_res.status_code == 200
    assert get_res.json()["engine_type"] == "hyperframes"

    # 4. Update subtitles and switch engine to remotion
    update_res = client.post(
        "/api/v1/projects/api_test_01/subtitles",
        json={
            "engine_type": "remotion",
            "subtitles": [
                {"start_time": 0.0, "end_time": 3.0, "text": "Updated Remotion Line 1", "words": []},
                {"start_time": 3.0, "end_time": 6.0, "text": "Updated Remotion Line 2", "words": []},
            ],
        },
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["engine_type"] == "remotion"
    assert updated_data["subtitles"][0]["text"] == "Updated Remotion Line 1"

    # 5. Probe media via ffprobe endpoint
    probe_res = client.get("/api/v1/projects/api_test_01/probe")
    assert probe_res.status_code == 200
    probe_data = probe_res.json()
    assert probe_data["width"] == 1280
    assert probe_data["height"] == 720
    assert probe_data["video_codec"] == "h264"

    # 6. Trim final video via FFmpeg trim endpoint
    trim_res = client.post(
        "/api/v1/projects/api_test_01/trim",
        json={"start_time": 0.0, "end_time": 4.0},
    )
    assert trim_res.status_code == 200
    assert trim_res.json()["status"] == "completed"

    # 7. NLE Speed, Color Grade, Reframe, Audio Master & Snapshot endpoints
    speed_res = client.post(
        "/api/v1/projects/api_test_01/speed",
        json={"speed_factor": 1.25},
    )
    assert speed_res.status_code == 200

    grade_res = client.post(
        "/api/v1/projects/api_test_01/color-grade",
        json={"look_preset": "teal_orange", "brightness": 0.03, "contrast": 1.08, "saturation": 1.12},
    )
    assert grade_res.status_code == 200

    reframe_res = client.post(
        "/api/v1/projects/api_test_01/reframe",
        json={"aspect_ratio": "9:16", "blur_background": True},
    )
    assert reframe_res.status_code == 200

    audio_res = client.post(
        "/api/v1/projects/api_test_01/audio-master",
        json={"remove_silences": False, "normalize_loudness": True, "mix_bgm": True, "bgm_volume": 0.15},
    )
    assert audio_res.status_code == 200

    snap_res = client.post(
        "/api/v1/projects/api_test_01/snapshot",
        json={"timestamp_sec": 1.0},
    )
    assert snap_res.status_code == 200
    assert Path(snap_res.json()["snapshot_path"]).exists()

    # 7b. Split, Concat & Multi-format Subtitle Export (.srt, .vtt, .transcript.json)
    split_res = client.post(
        "/api/v1/projects/api_test_01/split",
        json={"split_time": 1.5},
    )
    assert split_res.status_code == 200
    split_data = split_res.json()
    assert Path(split_data["part_a_path"]).exists()
    assert Path(split_data["part_b_path"]).exists()

    concat_res = client.post(
        "/api/v1/projects/api_test_01/concat",
        json={"clip_paths": [split_data["part_a_path"], split_data["part_b_path"]], "transition": "none"},
    )
    assert concat_res.status_code == 200

    for fmt in ("srt", "vtt", "json"):
        exp_res = client.get(f"/api/v1/projects/api_test_01/subtitles/export?fmt={fmt}")
        assert exp_res.status_code == 200
        assert Path(exp_res.json()["export_path"]).exists()

    # 8. Download final video stream
    video_res = client.get("/api/v1/projects/api_test_01/video")
    assert video_res.status_code == 200
    assert len(video_res.content) > 1000
