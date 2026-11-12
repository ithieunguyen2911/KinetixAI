"""RemotionAdapter - Infrastructure Adapter wrapping remotion-dev/remotion."""

import json
from pathlib import Path
import subprocess
from typing import Any, Dict

from src.domain.interfaces.visual_renderer import IVisualRenderer


class RemotionAdapter(IVisualRenderer):
    """Adapter encapsulating Remotion React composition rendering."""

    def __init__(self, engine_dir: Path | None = None, use_npx_cli: bool = False) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.engine_dir = engine_dir or (repo_root / "render_engines" / "remotion_engine")
        self.use_npx_cli = use_npx_cli

    def render_composition(self, template_id: str, props: Dict[str, Any], output_path: Path) -> Path:
        """Render a Remotion React composition with JSON props into output_path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        props_payload = {
            "template_id": template_id,
            **props,
        }
        props_json = json.dumps(props_payload, ensure_ascii=False)

        render_script = self.engine_dir / "render.mjs"
        if not self.use_npx_cli and render_script.exists():
            props_file = output_path.parent / f"{output_path.stem}_remotion_props.json"
            props_file.write_text(props_json, encoding="utf-8")
            cmd = [
                "node",
                str(render_script),
                "--template",
                template_id,
                "--props",
                str(props_file),
                "--output",
                str(output_path),
            ]
        else:
            cmd = [
                "npx",
                "remotion",
                "render",
                template_id,
                str(output_path),
                f"--props={props_json}",
            ]

        subprocess.run(cmd, check=True)
        return output_path
