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
        json={"start_time": 0.0, "end_time": 3.0},
    )
    assert trim_res.status_code == 200
    assert trim_res.json()["status"] == "completed"

    # 7. Download final video stream
    video_res = client.get("/api/v1/projects/api_test_01/video")
    assert video_res.status_code == 200
    assert len(video_res.content) > 1000
