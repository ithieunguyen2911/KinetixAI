"""End-to-End Integration Tests for KinetixAI with real FFmpeg, Remotion, and HyperFrames."""

from pathlib import Path

from src.application.services.project_service import ProjectService
from src.domain.entities.enums import JobStatus, RenderEngineType


def test_end_to_end_pipeline_with_remotion_and_hyperframes(tmp_path: Path) -> None:
    service = ProjectService(workspace_root=tmp_path)

    # 1. Execute full 5-step pipeline with REMOTION engine
    proj_remotion = service.create_and_run_project(
        project_id="e2e_remotion",
        source_url="demo://sample",
        engine_type=RenderEngineType.REMOTION,
        script_text="Remotion Engine Test|Clean Architecture Solid|Final MP4 Output",
    )
    assert proj_remotion.status == JobStatus.COMPLETED
    assert proj_remotion.progress_percent == 100
    assert proj_remotion.final_output_path is not None
    assert proj_remotion.final_output_path.exists()
    assert proj_remotion.final_output_path.stat().st_size > 2000
    assert proj_remotion.final_output_path.with_suffix(".srt").exists()

    # 2. Execute full 5-step pipeline with HYPERFRAMES engine
    proj_hf = service.create_and_run_project(
        project_id="e2e_hyperframes",
        source_url="demo://sample",
        engine_type=RenderEngineType.HYPERFRAMES,
        script_text="HyperFrames HTML GSAP|Deterministic Rendering|Fast FFmpeg Overlay",
    )
    assert proj_hf.status == JobStatus.COMPLETED
    assert proj_hf.progress_percent == 100
    assert proj_hf.final_output_path is not None
    assert proj_hf.final_output_path.exists()
    assert proj_hf.final_output_path.stat().st_size > 2000
