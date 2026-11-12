"""Streamlit Studio Dashboard for KinetixAI (FlowVids-AI)."""

import streamlit as st

from src.application.services.project_service import ProjectService


def render_streamlit_studio() -> None:
    st.set_page_config(page_title="KinetixAI Video Studio", layout="wide")
    st.title("🎬 KinetixAI (FlowVids-AI) Automated Video Studio")
    st.caption(
        "Clean Architecture Polyglot Pipeline: yt-dlp • FFmpeg • Whisper • Remotion • HyperFrames"
    )

    service = ProjectService()

    with st.sidebar:
        st.header("⚙️ New Video Project")
        project_id = st.text_input("Project ID", value="studio_demo_01")
        source_url = st.text_input("Source URL / Path", value="demo://sample")
        engine_type = st.selectbox("Visual Render Engine", ["remotion", "hyperframes"])
        template_id = st.text_input("Template ID", value="CaptionTemplate")
        script_text = st.text_area(
            "Script / Subtitle Lines (separated by |)",
            value="KinetixAI Clean Architecture Studio|Powered by Remotion & HyperFrames|Automated with Whisper & FFmpeg",
        )
        run_btn = st.button("🚀 Run 5-Step Production Pipeline", type="primary")

    if run_btn:
        with st.spinner(f"Running 5-step pipeline with {engine_type.upper()}..."):
            proj = service.create_and_run_project(
                project_id=project_id,
                source_url=source_url,
                engine_type=engine_type,
                template_id=template_id,
                script_text=script_text,
            )
            st.success(f"Completed! Final MP4: {proj.final_output_path}")

    st.subheader("📂 Workspace Projects")
    projects = service.list_projects()
    for p in reversed(projects):
        with st.expander(f"🎞️ {p.project_id} [{p.engine_type.value.upper()}] — {p.status.value.upper()} ({p.progress_percent}%)", expanded=True):
            col1, col2 = st.columns([3, 2])
            with col1:
                if p.final_output_path and p.final_output_path.exists():
                    st.video(str(p.final_output_path))
                st.json(p.to_dict())
            with col2:
                st.markdown("**Generated Subtitles**")
                st.table([s.to_dict() for s in p.subtitles])


if __name__ == "__main__":
    render_streamlit_studio()
