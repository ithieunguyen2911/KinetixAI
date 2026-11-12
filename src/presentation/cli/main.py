"""Command-Line Interface for KinetixAI Automated Video Production."""

import argparse
import json
import sys

from src.application.services.project_service import ProjectService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KinetixAI (FlowVids-AI) Automated Video Production CLI"
    )
    parser.add_argument("--project-id", required=True, help="Unique project ID")
    parser.add_argument(
        "--source",
        default="demo://sample",
        help="Source video URL, local path, or demo://sample",
    )
    parser.add_argument(
        "--engine",
        choices=["remotion", "hyperframes"],
        default="remotion",
        help="Visual render engine to use (remotion or hyperframes)",
    )
    parser.add_argument(
        "--template",
        default="CaptionTemplate",
        help="Visual template ID",
    )
    parser.add_argument(
        "--script",
        default="KinetixAI Clean Architecture Video Studio|Powered by Remotion, HyperFrames, Whisper & FFmpeg|Spec-Driven Development with GitHub Spec Kit",
        help="Optional subtitle script lines separated by |",
    )

    args = parser.parse_args()
    service = ProjectService()
    project = service.create_and_run_project(
        project_id=args.project_id,
        source_url=args.source,
        engine_type=args.engine,
        template_id=args.template,
        script_text=args.script,
    )
    print(json.dumps(project.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
