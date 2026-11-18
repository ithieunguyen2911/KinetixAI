"""StoryboardVisualAdapter - Infrastructure Adapter for 1280x720 Cinematic Storyboard Illustrations."""

from __future__ import annotations

import base64
import hashlib
from io import BytesIO
import math
import os
from pathlib import Path
import re
from typing import Dict, List, Tuple
import urllib.parse

import httpx
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from src.domain.interfaces.visual_generator import IVisualAssetGenerator

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
TARGET_SIZE = (TARGET_WIDTH, TARGET_HEIGHT)


class StoryboardVisualAdapter(IVisualAssetGenerator):
    """Resolves pre-rendered artwork, optional cloud AI illustrations, or procedural moody 16:9 cinema frames."""

    def __init__(
        self,
        allow_remote: bool = False,
        repo_root: Path | None = None,
        timeout_sec: float = 12.0,
    ) -> None:
        self.allow_remote = bool(allow_remote)
        self.repo_root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
        self.timeout_sec = max(2.0, float(timeout_sec))

    def resolve_scene_illustration(
        self,
        scene_id: str,
        title: str,
        visual_prompt: str,
        mood: str,
        output_dir: Path,
        existing_image_path: str | None = None,
    ) -> Path:
        """Resolve an existing scene image or generate a 1280x720 cinematic illustration PNG in output_dir."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(scene_id or "scene_01").strip()) or "scene_01"
        target_path = output_dir / f"{safe_id}.png"

        # =====================================================================
        # PRIORITY 1: Existing / Pre-Rendered AI Storyboard Artwork on Disk
        # =====================================================================
        pre_rendered = self._find_existing_artwork(safe_id, target_path, existing_image_path)
        if pre_rendered is not None:
            try:
                return self._fit_and_save_png(pre_rendered, target_path)
            except Exception:
                pass

        # =====================================================================
        # PRIORITY 2: Optional Cloud AI Generation (Gemini Imagen / Pollinations)
        # =====================================================================
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if gemini_key or self.allow_remote:
            cloud_img = self._try_fetch_cloud_illustration(
                scene_id=safe_id,
                title=title,
                visual_prompt=visual_prompt,
                mood=mood,
                gemini_key=gemini_key,
            )
            if cloud_img is not None:
                try:
                    fitted = ImageOps.fit(
                        cloud_img.convert("RGB"),
                        TARGET_SIZE,
                        method=Image.Resampling.LANCZOS,
                        centering=(0.5, 0.5),
                    )
                    fitted.save(target_path, format="PNG")
                    if target_path.exists() and target_path.stat().st_size > 10_240:
                        return target_path
                except Exception:
                    pass

        # =====================================================================
        # PRIORITY 3: Rich Procedural Cinematic Atmosphere Illustration (PIL+NumPy)
        # =====================================================================
        procedural_img = self._render_procedural_cinematic_scene(
            scene_id=safe_id,
            title=title,
            visual_prompt=visual_prompt,
            mood=mood,
        )
        procedural_img.save(target_path, format="PNG", compress_level=5)
        return target_path

    # -------------------------------------------------------------------------
    # Priority 1 Helpers
    # -------------------------------------------------------------------------
    def _find_existing_artwork(
        self,
        safe_id: str,
        target_path: Path,
        existing_image_path: str | None,
    ) -> Path | None:
        candidates: List[Path] = []
        if existing_image_path:
            candidates.append(Path(existing_image_path))

        if target_path.is_file() and target_path.stat().st_size > 10_240:
            candidates.append(target_path)

        storyboard_dir = self.repo_root / "docs" / "storyboard_tap_01"
        if storyboard_dir.is_dir():
            stem_variants = [safe_id]
            num_match = re.search(r"(\d+)$", safe_id)
            if num_match:
                idx = int(num_match.group(1))
                normalized = f"scene_{idx:02d}"
                if normalized not in stem_variants:
                    stem_variants.append(normalized)
            for stem in stem_variants:
                for ext in (".png", ".jpg", ".jpeg", ".webp"):
                    candidates.append(storyboard_dir / f"{stem}{ext}")

        for cand in candidates:
            try:
                if cand.is_file() and cand.stat().st_size > 2_048:
                    if cand.resolve() == target_path.resolve() and cand.stat().st_size <= 10_240:
                        continue
                    return cand
            except OSError:
                continue
        return None

    @staticmethod
    def _fit_and_save_png(source_path: Path, target_path: Path) -> Path:
        with Image.open(source_path) as raw_img:
            raw_img.load()
            if (
                source_path.resolve() == target_path.resolve()
                and raw_img.size == TARGET_SIZE
                and raw_img.mode == "RGB"
                and target_path.stat().st_size > 10_240
            ):
                return target_path
            rgb = raw_img.convert("RGB")
            fitted = ImageOps.fit(
                rgb,
                TARGET_SIZE,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        fitted.save(target_path, format="PNG")
        return target_path

    # -------------------------------------------------------------------------
    # Priority 2 Helpers (Cloud AI w/ Short Timeout)
    # -------------------------------------------------------------------------
    def _try_fetch_cloud_illustration(
        self,
        scene_id: str,
        title: str,
        visual_prompt: str,
        mood: str,
        gemini_key: str,
    ) -> Image.Image | None:
        prompt_core = " ".join(str(visual_prompt or title or "cinematic night scene").split())
        full_prompt = (
            f"Cinematic 16:9 moody editorial illustration, {mood} atmosphere, "
            f"dramatic volumetric lighting, shallow depth of field, no text, no watermark: {prompt_core}"
        )[:650]

        if gemini_key:
            try:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"imagen-3.0-generate-002:predict?key={gemini_key}"
                )
                payload = {
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "16:9"},
                }
                with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        preds = data.get("predictions") or []
                        if preds and preds[0].get("bytesBase64Encoded"):
                            raw_bytes = base64.b64decode(preds[0]["bytesBase64Encoded"])
                            img = Image.open(BytesIO(raw_bytes))
                            img.load()
                            return img
            except Exception:
                pass

        if self.allow_remote:
            try:
                seed_int = int(hashlib.md5(scene_id.encode("utf-8")).hexdigest()[:8], 16) % 999999
                encoded = urllib.parse.quote(full_prompt)
                poll_url = (
                    f"https://image.pollinations.ai/prompt/{encoded}"
                    f"?width={TARGET_WIDTH}&height={TARGET_HEIGHT}&nologo=true&seed={seed_int}"
                )
                with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
                    resp = client.get(poll_url)
                    if resp.status_code == 200 and len(resp.content) > 8_192:
                        img = Image.open(BytesIO(resp.content))
                        img.load()
                        return img
            except Exception:
                pass

        return None

    # -------------------------------------------------------------------------
    # Priority 3 Helpers (Procedural Cinematic Widescreen Illustration)
    # -------------------------------------------------------------------------
    @classmethod
    def _render_procedural_cinematic_scene(
        cls,
        scene_id: str,
        title: str,
        visual_prompt: str,
        mood: str,
    ) -> Image.Image:
        seed_hex = hashlib.sha256(
            f"{scene_id}|{title}|{visual_prompt}|{mood}".encode("utf-8")
        ).hexdigest()
        seed = int(seed_hex[:12], 16)
        rng = np.random.default_rng(seed)

        combined_text = f"{title} {visual_prompt}".lower()
        mood_norm = cls._classify_mood(mood, combined_text)
        motif = cls._classify_motif(combined_text, scene_id)
        palette = cls._get_palette(mood_norm)

        # 1. Multi-stop twilight sky / interior gradient + horizon radial bloom
        canvas_arr = cls._build_sky_gradient(palette, rng)
        base_img = Image.fromarray(canvas_arr).convert("RGBA")

        # 2. Celestial / Window Light Orb + Volumetric Light Rays (GaussianBlur)
        light_x = int(rng.integers(260, 1020))
        if motif == "desk_window":
            light_x = 960 if (seed % 2 == 0) else 320
        elif motif == "tree_roots":
            light_x = int(rng.integers(520, 780))
        light_y = int(rng.integers(130, 290)) if mood_norm != "hopeful" else int(rng.integers(250, 390))

        base_img = cls._Composite_volumetric_light(
            base_img=base_img,
            light_pos=(light_x, light_y),
            palette=palette,
            mood=mood_norm,
            rng=rng,
        )

        # 3. Distant atmospheric mountain/cloud ridges (layered aerial perspective)
        base_img = cls._draw_distant_ridges(base_img, palette, rng)

        # 4. Motif-specific foreground & midground cinematic silhouettes
        if motif == "desk_window":
            base_img = cls._draw_desk_window_motif(base_img, palette, mood_norm, light_x, rng)
        elif motif == "market_crash":
            base_img = cls._draw_market_chart_city_motif(base_img, palette, mood_norm, rng)
        elif motif == "tree_roots":
            base_img = cls._draw_tree_and_roots_motif(base_img, palette, mood_norm, light_x, rng)
        elif motif == "city_skyline":
            base_img = cls._draw_city_skyline_motif(base_img, palette, mood_norm, rng)
        else:
            base_img = cls._draw_mountain_horizon_motif(base_img, palette, mood_norm, light_x, rng)

        # 5. Bokeh dust motes / rain particles + optical vignette + organic film grain
        base_img = cls._draw_atmospheric_particles(base_img, palette, mood_norm, rng)
        final_rgb = cls._apply_vignette_and_film_grain(base_img.convert("RGB"), rng)
        return final_rgb

    @staticmethod
    def _classify_mood(mood: str, combined_text: str) -> str:
        m = str(mood or "melancholic").strip().lower()
        if m in ("hopeful", "inspiring", "warm", "uplifting"):
            return "hopeful"
        if m in ("dramatic", "intense", "storm", "crisis", "crash"):
            return "dramatic"
        if any(
            kw in combined_text
            for kw in (
                "crash",
                "storm",
                "collapse",
                "debt",
                "panic",
                "sập",
                "lao dốc",
                "hoảng loạn",
                "khủng hoảng",
                "vỡ nợ",
                "đỏ rực",
            )
        ):
            return "dramatic"
        if m in ("neutral", "calm", "studio"):
            return "neutral"
        return "melancholic"

    @staticmethod
    def _classify_motif(combined_text: str, scene_id: str) -> str:
        # Priority matching on prompt/title visual nouns (English + Vietnamese)
        if any(
            kw in combined_text
            for kw in ("tree", "root", "roots", "seed", "branch", "cây", "rễ", "bén rễ", "mầm", "lòng đất")
        ):
            return "tree_roots"
        if any(
            kw in combined_text
            for kw in ("chart", "graph", "candlestick", "crypto", "coin", "market", "biểu đồ", "giá coin", "thị trường sập")
        ):
            return "market_crash"
        if any(
            kw in combined_text
            for kw in (
                "desk",
                "window",
                "laptop",
                "computer",
                "mining",
                "rig",
                "cv",
                "resume",
                "room",
                "bàn",
                "cửa sổ",
                "máy đào",
                "máy tính",
                "hồ sơ",
                "xin việc",
                "phòng",
            )
        ):
            return "desk_window"
        if any(
            kw in combined_text
            for kw in ("city", "skyline", "street", "building", "tower", "urban", "thành phố", "cao ốc", "đèn đường", "phố")
        ):
            return "city_skyline"

        # Varied deterministic fallback by scene index so consecutive scenes never look identical
        num_match = re.search(r"(\d+)$", scene_id)
        if num_match:
            idx = int(num_match.group(1))
            cycle = ["desk_window", "city_skyline", "market_crash", "mountain_dawn", "tree_roots"]
            return cycle[(idx - 1) % len(cycle)]
        return "mountain_dawn"

    @staticmethod
    def _get_palette(mood: str) -> Dict[str, Tuple[int, int, int]]:
        palettes: Dict[str, Dict[str, Tuple[int, int, int]]] = {
            "melancholic": {
                "sky_top": (7, 12, 26),
                "sky_upper": (14, 30, 58),
                "sky_mid": (24, 62, 92),
                "sky_horizon": (58, 124, 158),
                "glow": (108, 194, 238),
                "ray": (125, 206, 248),
                "ridge_far": (18, 36, 60),
                "ridge_mid": (12, 24, 44),
                "silhouette": (7, 11, 20),
                "accent": (56, 189, 248),
                "accent_warm": (245, 178, 86),
                "mist": (74, 146, 182),
            },
            "dramatic": {
                "sky_top": (14, 7, 16),
                "sky_upper": (42, 14, 30),
                "sky_mid": (92, 24, 38),
                "sky_horizon": (168, 54, 46),
                "glow": (244, 102, 68),
                "ray": (236, 94, 72),
                "ridge_far": (38, 16, 28),
                "ridge_mid": (24, 10, 20),
                "silhouette": (10, 6, 12),
                "accent": (239, 68, 68),
                "accent_warm": (251, 146, 60),
                "mist": (148, 52, 58),
            },
            "hopeful": {
                "sky_top": (16, 22, 46),
                "sky_upper": (54, 44, 82),
                "sky_mid": (148, 92, 68),
                "sky_horizon": (244, 182, 94),
                "glow": (255, 224, 142),
                "ray": (255, 214, 130),
                "ridge_far": (58, 46, 68),
                "ridge_mid": (34, 28, 46),
                "silhouette": (15, 14, 24),
                "accent": (251, 191, 36),
                "accent_warm": (253, 224, 132),
                "mist": (238, 176, 108),
            },
            "neutral": {
                "sky_top": (10, 16, 30),
                "sky_upper": (24, 40, 66),
                "sky_mid": (46, 76, 108),
                "sky_horizon": (98, 138, 168),
                "glow": (168, 210, 238),
                "ray": (162, 206, 236),
                "ridge_far": (26, 42, 64),
                "ridge_mid": (16, 28, 46),
                "silhouette": (9, 13, 22),
                "accent": (96, 165, 250),
                "accent_warm": (250, 204, 105),
                "mist": (112, 152, 182),
            },
        }
        return palettes.get(mood, palettes["melancholic"])

    @staticmethod
    def _build_sky_gradient(
        palette: Dict[str, Tuple[int, int, int]],
        rng: np.random.Generator,
    ) -> np.ndarray:
        y_norm = np.linspace(0.0, 1.0, TARGET_HEIGHT, dtype=np.float32)[:, None]
        x_norm = np.linspace(0.0, 1.0, TARGET_WIDTH, dtype=np.float32)[None, :]

        stops = [0.0, 0.34, 0.66, 1.0]
        colors = np.array(
            [
                palette["sky_top"],
                palette["sky_upper"],
                palette["sky_mid"],
                palette["sky_horizon"],
            ],
            dtype=np.float32,
        )

        canvas = np.zeros((TARGET_HEIGHT, TARGET_WIDTH, 3), dtype=np.float32)
        for c in range(3):
            col_1d = np.interp(y_norm[:, 0], stops, colors[:, c])
            canvas[:, :, c] = col_1d[:, None]

        # Subtle atmospheric cloud/aurora wave modulation across the upper sky
        phase1 = float(rng.uniform(0.0, math.tau))
        phase2 = float(rng.uniform(0.0, math.tau))
        cloud_wave = (
            np.sin(x_norm * 5.2 + y_norm * 2.8 + phase1) * 0.5
            + np.cos(x_norm * 9.4 - y_norm * 4.1 + phase2) * 0.5
        )
        sky_mask = np.clip(1.0 - y_norm * 1.15, 0.0, 1.0)
        glow_vec = np.array(palette["glow"], dtype=np.float32)[None, None, :]
        canvas += (cloud_wave[:, :, None] * 0.065 + 0.03) * sky_mask[:, :, None] * (glow_vec * 0.35)

        return np.clip(canvas, 0, 255).astype(np.uint8)

    @staticmethod
    def _Composite_volumetric_light(
        base_img: Image.Image,
        light_pos: Tuple[int, int],
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        rng: np.random.Generator,
    ) -> Image.Image:
        lx, ly = light_pos
        glow_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_layer)

        glow_rgb = palette["glow"]
        ray_rgb = palette["ray"]

        # Wide ambient atmospheric bloom around light source
        for rad, alpha in ((340, 38), (210, 62), (110, 95), (46, 165)):
            gdraw.ellipse(
                (lx - rad, ly - rad, lx + rad, ly + rad),
                fill=(glow_rgb[0], glow_rgb[1], glow_rgb[2], alpha),
            )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=36))

        # Diagonal volumetric god-rays / sunbeams / moonbeams
        ray_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ray_layer)
        num_rays = 8 if mood == "hopeful" else 6
        target_base_x = TARGET_WIDTH // 2 + (140 if lx < TARGET_WIDTH // 2 else -140)
        for i in range(num_rays):
            spread = (i - num_rays / 2.0) * float(rng.uniform(95.0, 145.0))
            bx1 = int(target_base_x + spread - rng.uniform(45, 95))
            bx2 = int(target_base_x + spread + rng.uniform(55, 120))
            ray_alpha = int(rng.integers(20, 44)) if mood != "hopeful" else int(rng.integers(28, 56))
            poly = [
                (lx - 18, ly - 10),
                (lx + 18, ly + 10),
                (bx2, TARGET_HEIGHT),
                (bx1, TARGET_HEIGHT),
            ]
            rdraw.polygon(poly, fill=(ray_rgb[0], ray_rgb[1], ray_rgb[2], ray_alpha))

        ray_layer = ray_layer.filter(ImageFilter.GaussianBlur(radius=24))
        out = Image.alpha_composite(base_img, glow_layer)
        out = Image.alpha_composite(out, ray_layer)
        return out

    @staticmethod
    def _draw_distant_ridges(
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        rng: np.random.Generator,
    ) -> Image.Image:
        out = base_img
        xs = np.linspace(0, TARGET_WIDTH, 160)
        for layer_idx, (base_y, amp, col_key, alpha) in enumerate(
            [
                (445, 52.0, "ridge_far", 195),
                (505, 38.0, "ridge_mid", 230),
            ]
        ):
            layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)
            p1 = float(rng.uniform(0, math.tau))
            p2 = float(rng.uniform(0, math.tau))
            p3 = float(rng.uniform(0, math.tau))
            ys = (
                base_y
                - amp * 0.55 * np.sin(xs / 210.0 + p1)
                - amp * 0.30 * np.cos(xs / 95.0 + p2)
                - amp * 0.15 * np.sin(xs / 42.0 + p3)
            )
            pts = [(0, TARGET_HEIGHT)] + [(int(x), int(y)) for x, y in zip(xs, ys)] + [(TARGET_WIDTH, TARGET_HEIGHT)]
            c = palette[col_key]
            draw.polygon(pts, fill=(c[0], c[1], c[2], alpha))

            # Subtle mist band along valley base
            mist_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
            mdraw = ImageDraw.Draw(mist_layer)
            mc = palette["mist"]
            mist_y = base_y + 18 + layer_idx * 14
            mdraw.rectangle(
                (0, mist_y - 24, TARGET_WIDTH, mist_y + 34),
                fill=(mc[0], mc[1], mc[2], 38),
            )
            mist_layer = mist_layer.filter(ImageFilter.GaussianBlur(radius=22))
            out = Image.alpha_composite(out, layer)
            out = Image.alpha_composite(out, mist_layer)
        return out

    @staticmethod
    def _draw_city_skyline_motif(
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        rng: np.random.Generator,
    ) -> Image.Image:
        layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        win_glow = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        wdraw = ImageDraw.Draw(win_glow)

        horizon_y = 555
        # Background skyline tier
        x = -10
        far_c = palette["ridge_mid"]
        while x < TARGET_WIDTH + 20:
            bw = int(rng.integers(36, 78))
            bh = int(rng.integers(85, 220))
            draw.rectangle(
                (x, horizon_y - bh, x + bw - 3, horizon_y),
                fill=(far_c[0], far_c[1], far_c[2], 238),
            )
            x += bw - int(rng.integers(4, 14))

        # Foreground architectural towers + glowing apartment windows
        sil = palette["silhouette"]
        warm = palette["accent_warm"]
        cool = palette["accent"]
        x = 0
        while x < TARGET_WIDTH:
            bw = int(rng.integers(44, 96))
            bh = int(rng.integers(110, 295))
            top_y = horizon_y - bh
            draw.rectangle((x, top_y, x + bw, horizon_y + 12), fill=(sil[0], sil[1], sil[2], 252))
            # Optional rooftop spire / stepped crown
            if rng.random() < 0.42:
                crown_w = max(14, bw // 2)
                cx = x + (bw - crown_w) // 2
                draw.rectangle((cx, top_y - 18, cx + crown_w, top_y), fill=(sil[0], sil[1], sil[2], 252))
                if rng.random() < 0.5:
                    draw.line((x + bw // 2, top_y - 42, x + bw // 2, top_y - 18), fill=(sil[0], sil[1], sil[2], 240), width=2)
                    wdraw.ellipse(
                        (x + bw // 2 - 3, top_y - 45, x + bw // 2 + 3, top_y - 39),
                        fill=(239, 68, 68, 210),
                    )

            # Lit windows
            for wy in range(top_y + 12, horizon_y - 14, 13):
                for wx in range(x + 7, x + bw - 9, 11):
                    if rng.random() < (0.34 if mood != "melancholic" else 0.22):
                        use_warm = rng.random() < (0.72 if mood == "hopeful" else 0.45)
                        wc = warm if use_warm else cool
                        alpha = int(rng.integers(110, 225))
                        wdraw.rectangle((wx, wy, wx + 5, wy + 7), fill=(wc[0], wc[1], wc[2], alpha))
            x += bw + int(rng.integers(3, 14))

        # Wet street / harbor dark reflective foreground (y=555..720)
        draw.rectangle((0, horizon_y, TARGET_WIDTH, TARGET_HEIGHT), fill=(sil[0], sil[1], sil[2], 246))
        refl = win_glow.crop((0, horizon_y - 165, TARGET_WIDTH, horizon_y)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        refl = refl.filter(ImageFilter.GaussianBlur(radius=6))
        refl_alpha = refl.getchannel("A").point(lambda a: int(a * 0.38))
        refl.putalpha(refl_alpha)

        soft_win = win_glow.filter(ImageFilter.GaussianBlur(radius=3))
        out = Image.alpha_composite(base_img, layer)
        out = Image.alpha_composite(out, soft_win)
        out = Image.alpha_composite(out, win_glow)
        refl_canvas = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        refl_canvas.paste(refl, (0, horizon_y))
        out = Image.alpha_composite(out, refl_canvas)
        return out

    @classmethod
    def _draw_market_chart_city_motif(
        cls,
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        rng: np.random.Generator,
    ) -> Image.Image:
        out = cls._draw_city_skyline_motif(base_img, palette, mood, rng)

        chart_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(chart_layer)

        # Subtle perspective data grid in mid-air
        grid_c = palette["accent"]
        for gy in range(170, 490, 52):
            cdraw.line((110, gy, 1170, gy), fill=(grid_c[0], grid_c[1], grid_c[2], 24), width=1)
        for gx in range(140, 1160, 84):
            cdraw.line((gx, 150, gx, 495), fill=(grid_c[0], grid_c[1], grid_c[2], 20), width=1)

        # Luminous candlestick trajectory (crash cliff vs hopeful recovery)
        n_pts = 34
        xs = np.linspace(135, 1145, n_pts)
        ys: List[float] = []
        cur_y = 220.0 if mood != "hopeful" else 425.0
        for idx in range(n_pts):
            t = idx / float(n_pts - 1)
            if mood == "hopeful":
                drift = -5.8 - 3.2 * t
            else:
                drift = 2.5 if t < 0.32 else 11.2
            step = drift + float(rng.normal(0.0, 11.5))
            cur_y = float(np.clip(cur_y + step, 155.0, 475.0))
            ys.append(cur_y)

        line_col = (251, 191, 36) if mood == "hopeful" else (244, 63, 94)
        for i in range(n_pts):
            cx = int(xs[i])
            cy = int(ys[i])
            prev_y = int(ys[max(0, i - 1)])
            top_b = min(cy, prev_y) - int(rng.integers(2, 10))
            bot_b = max(cy, prev_y) + int(rng.integers(2, 10))
            wick_top = top_b - int(rng.integers(8, 22))
            wick_bot = bot_b + int(rng.integers(8, 22))
            is_up = cy <= prev_y
            c_bar = (52, 211, 153) if is_up else line_col
            cdraw.line((cx, wick_top, cx, wick_bot), fill=(c_bar[0], c_bar[1], c_bar[2], 125), width=2)
            cdraw.rectangle((cx - 7, top_b, cx + 7, max(top_b + 4, bot_b)), fill=(c_bar[0], c_bar[1], c_bar[2], 155))

        pts = [(int(x), int(y)) for x, y in zip(xs, ys)]
        cdraw.line(pts, fill=(line_col[0], line_col[1], line_col[2], 235), width=4)

        glow_chart = chart_layer.filter(ImageFilter.GaussianBlur(radius=10))
        out = Image.alpha_composite(out, glow_chart)
        out = Image.alpha_composite(out, chart_layer)
        return out

    @staticmethod
    def _draw_desk_window_motif(
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        light_x: int,
        rng: np.random.Generator,
    ) -> Image.Image:
        out = base_img
        sil = palette["silhouette"]
        rim = palette["glow"]
        warm = palette["accent_warm"]
        cool = palette["accent"]

        # Distant city silhouettes visible outside the window
        city_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(city_layer)
        cx = 60
        while cx < TARGET_WIDTH - 60:
            bw = int(rng.integers(38, 76))
            bh = int(rng.integers(90, 220))
            cdraw.rectangle((cx, 500 - bh, cx + bw, 520), fill=(sil[0] + 8, sil[1] + 12, sil[2] + 20, 175))
            cx += bw + int(rng.integers(6, 18))
        out = Image.alpha_composite(out, city_layer)

        room = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(room)

        # Architectural window framing (left/right wall pillars + top lintel + mullions)
        win_left = 170 if light_x < 640 else 440
        win_right = win_left + 670
        win_top = 86
        win_bot = 492

        wall_c = (sil[0], sil[1], sil[2], 244)
        rdraw.rectangle((0, 0, win_left, TARGET_HEIGHT), fill=wall_c)
        rdraw.rectangle((win_right, 0, TARGET_WIDTH, TARGET_HEIGHT), fill=wall_c)
        rdraw.rectangle((win_left, 0, win_right, win_top), fill=wall_c)
        rdraw.rectangle((0, win_bot, TARGET_WIDTH, TARGET_HEIGHT), fill=(sil[0], sil[1], sil[2], 252))

        # Window mullions + subtle rim highlight
        for mx in (win_left + 220, win_left + 446):
            rdraw.rectangle((mx - 5, win_top, mx + 5, win_bot), fill=wall_c)
            rdraw.line((mx + 5, win_top, mx + 5, win_bot), fill=(rim[0], rim[1], rim[2], 70), width=1)
        rdraw.rectangle((win_left, win_top + 210, win_right, win_top + 220), fill=wall_c)
        rdraw.line((win_left, win_bot, win_right, win_bot), fill=(rim[0], rim[1], rim[2], 120), width=2)

        # Desk surface highlight + monitor / silent rig / lamp silhouettes
        desk_y = 508
        rdraw.polygon(
            [(110, desk_y), (1170, desk_y), (1250, 565), (40, 565)],
            fill=(sil[0] + 10, sil[1] + 14, sil[2] + 24, 255),
        )
        rdraw.line((120, desk_y, 1160, desk_y), fill=(rim[0], rim[1], rim[2], 95), width=2)

        # Monitor silhouette on desk
        mon_x = 500
        mon_y = 338
        mon_w = 270
        mon_h = 152
        rdraw.rounded_rectangle(
            (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h),
            radius=8,
            fill=(sil[0] + 4, sil[1] + 6, sil[2] + 12, 252),
            outline=(rim[0], rim[1], rim[2], 90),
            width=2,
        )
        rdraw.rectangle((mon_x + 122, mon_y + mon_h, mon_x + 148, desk_y), fill=wall_c)
        rdraw.rectangle((mon_x + 88, desk_y - 6, mon_x + 182, desk_y + 2), fill=wall_c)

        # Screen ambient glow
        glow = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        scr_c = warm if mood == "hopeful" else cool
        gdraw.rectangle(
            (mon_x + 10, mon_y + 10, mon_x + mon_w - 10, mon_y + mon_h - 12),
            fill=(scr_c[0], scr_c[1], scr_c[2], 68 if mood != "dramatic" else 92),
        )
        # Rig tower / stack silhouette on side + tiny status LEDs
        rig_x = 835 if win_left < 300 else 255
        rdraw.rounded_rectangle(
            (rig_x, 352, rig_x + 112, desk_y),
            radius=6,
            fill=(sil[0] + 6, sil[1] + 8, sil[2] + 15, 252),
            outline=(rim[0], rim[1], rim[2], 65),
            width=1,
        )
        led_col = (239, 68, 68, 210) if mood != "hopeful" else (52, 211, 153, 210)
        gdraw.ellipse((rig_x + 20, 374, rig_x + 27, 381), fill=led_col)
        gdraw.ellipse((rig_x + 36, 374, rig_x + 43, 381), fill=(warm[0], warm[1], warm[2], 160))

        # Warm desk lamp or glowing phone notification on desk
        phone_x = mon_x - 105
        gdraw.polygon(
            [(phone_x, desk_y + 14), (phone_x + 54, desk_y + 10), (phone_x + 66, desk_y + 26), (phone_x - 10, desk_y + 30)],
            fill=(warm[0], warm[1], warm[2], 185),
        )
        glow_blur = glow.filter(ImageFilter.GaussianBlur(radius=14))
        out = Image.alpha_composite(out, room)
        out = Image.alpha_composite(out, glow_blur)
        out = Image.alpha_composite(out, glow)
        return out

    @classmethod
    def _draw_tree_and_roots_motif(
        cls,
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        light_x: int,
        rng: np.random.Generator,
    ) -> Image.Image:
        layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        root_glow = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(root_glow)

        sil = palette["silhouette"]
        warm = palette["accent_warm"]

        # Rolling earth mound horizon around y=485
        xs = np.linspace(0, TARGET_WIDTH, 140)
        tree_x = int(np.clip(light_x, 420, 860))
        mound_y = 500 - 34 * np.exp(-((xs - tree_x) ** 2) / (2 * 260.0**2))
        pts = [(0, TARGET_HEIGHT)] + [(int(x), int(y)) for x, y in zip(xs, mound_y)] + [(TARGET_WIDTH, TARGET_HEIGHT)]
        draw.polygon(pts, fill=(sil[0], sil[1], sil[2], 250))

        base_y = 468

        # Recursive upward tree branches
        def _branch(x0: float, y0: float, angle: float, length: float, width: float, depth: int) -> None:
            if depth <= 0 or length < 8:
                gdraw.ellipse(
                    (x0 - 5, y0 - 5, x0 + 5, y0 + 5),
                    fill=(warm[0], warm[1], warm[2], int(rng.integers(95, 190))),
                )
                return
            x1 = x0 + math.cos(angle) * length
            y1 = y0 + math.sin(angle) * length
            draw.line((x0, y0, x1, y1), fill=(sil[0], sil[1], sil[2], 255), width=max(1, int(round(width))))
            for sub_ang in (
                angle - float(rng.uniform(0.24, 0.46)),
                angle + float(rng.uniform(0.24, 0.46)),
            ):
                _branch(x1, y1, sub_ang, length * float(rng.uniform(0.68, 0.78)), width * 0.68, depth - 1)

        _branch(float(tree_x), float(base_y + 6), -math.pi / 2.0, 96.0, 14.0, 6)

        # Luminous subterranean roots weaving downward through dark soil
        root_col = warm if mood == "hopeful" else palette["accent"]

        def _root(x0: float, y0: float, angle: float, length: float, width: float, depth: int) -> None:
            if depth <= 0 or length < 8 or y0 >= TARGET_HEIGHT - 6:
                return
            x1 = x0 + math.cos(angle) * length
            y1 = min(float(TARGET_HEIGHT - 2), y0 + math.sin(angle) * length)
            alpha = max(45, 42 * depth)
            gdraw.line(
                (x0, y0, x1, y1),
                fill=(root_col[0], root_col[1], root_col[2], min(210, alpha)),
                width=max(1, int(round(width))),
            )
            for sub_ang in (
                angle - float(rng.uniform(0.22, 0.48)),
                angle + float(rng.uniform(0.22, 0.48)),
            ):
                _root(x1, y1, sub_ang, length * float(rng.uniform(0.66, 0.78)), width * 0.66, depth - 1)

        _root(float(tree_x), float(base_y + 10), math.pi / 2.0, 64.0, 7.0, 5)

        soft_glow = root_glow.filter(ImageFilter.GaussianBlur(radius=8))
        out = Image.alpha_composite(base_img, layer)
        out = Image.alpha_composite(out, soft_glow)
        out = Image.alpha_composite(out, root_glow)
        return out

    @staticmethod
    def _draw_mountain_horizon_motif(
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        light_x: int,
        rng: np.random.Generator,
    ) -> Image.Image:
        layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        sil = palette["silhouette"]

        # Dramatic foreground cliff overlook + reflective valley mist
        xs = np.linspace(0, TARGET_WIDTH, 160)
        p1 = float(rng.uniform(0, math.tau))
        cliff_y = 548 - 46 * np.exp(-((xs - 340.0) ** 2) / (2 * 220.0**2)) + 14 * np.sin(xs / 80.0 + p1)
        pts = [(0, TARGET_HEIGHT)] + [(int(x), int(y)) for x, y in zip(xs, cliff_y)] + [(TARGET_WIDTH, TARGET_HEIGHT)]
        draw.polygon(pts, fill=(sil[0], sil[1], sil[2], 252))

        # Solitary contemplative figure silhouette on ridge facing the light
        fig_x = 340 if light_x >= 520 else 860
        idx_near = int(np.argmin(np.abs(xs - fig_x)))
        ground_y = int(cliff_y[idx_near])
        draw.ellipse((fig_x - 6, ground_y - 44, fig_x + 6, ground_y - 32), fill=(sil[0], sil[1], sil[2], 255))
        draw.polygon(
            [
                (fig_x - 11, ground_y - 31),
                (fig_x + 11, ground_y - 31),
                (fig_x + 14, ground_y - 10),
                (fig_x - 14, ground_y - 10),
            ],
            fill=(sil[0], sil[1], sil[2], 255),
        )
        draw.rectangle((fig_x - 8, ground_y - 10, fig_x - 2, ground_y + 2), fill=(sil[0], sil[1], sil[2], 255))
        draw.rectangle((fig_x + 2, ground_y - 10, fig_x + 8, ground_y + 2), fill=(sil[0], sil[1], sil[2], 255))

        return Image.alpha_composite(base_img, layer)

    @staticmethod
    def _draw_atmospheric_particles(
        base_img: Image.Image,
        palette: Dict[str, Tuple[int, int, int]],
        mood: str,
        rng: np.random.Generator,
    ) -> Image.Image:
        out = base_img
        bokeh_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(bokeh_layer)

        warm = palette["accent_warm"]
        cool = palette["accent"]

        # Soft out-of-focus bokeh orbs & floating dust motes
        n_bokeh = 42 if mood == "hopeful" else 28
        for _ in range(n_bokeh):
            bx = int(rng.integers(20, TARGET_WIDTH - 20))
            by = int(rng.integers(40, TARGET_HEIGHT - 40))
            rad = int(rng.integers(3, 24))
            use_warm = rng.random() < (0.80 if mood == "hopeful" else 0.35)
            col = warm if use_warm else cool
            alpha = int(rng.integers(18, 68)) if rad > 10 else int(rng.integers(55, 135))
            bdraw.ellipse((bx - rad, by - rad, bx + rad, by + rad), fill=(col[0], col[1], col[2], alpha))

        bokeh_soft = bokeh_layer.filter(ImageFilter.GaussianBlur(radius=4))
        out = Image.alpha_composite(out, bokeh_soft)

        # Fine diagonal rain streaks in melancholic / dramatic scenes
        if mood in ("melancholic", "dramatic"):
            rain_layer = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
            rdraw = ImageDraw.Draw(rain_layer)
            rc = palette["glow"]
            for _ in range(135):
                rx = int(rng.integers(-40, TARGET_WIDTH + 40))
                ry = int(rng.integers(-20, TARGET_HEIGHT))
                rlen = int(rng.integers(18, 46))
                ralpha = int(rng.integers(18, 52))
                rdraw.line((rx, ry, rx - rlen // 4, ry + rlen), fill=(rc[0], rc[1], rc[2], ralpha), width=1)
            rain_layer = rain_layer.filter(ImageFilter.GaussianBlur(radius=0.7))
            out = Image.alpha_composite(out, rain_layer)

        return out

    @staticmethod
    def _apply_vignette_and_film_grain(
        rgb_img: Image.Image,
        rng: np.random.Generator,
    ) -> Image.Image:
        arr = np.asarray(rgb_img, dtype=np.float32)

        # Smooth elliptical cinema vignette preserving bright 75% center
        yy = np.linspace(-1.0, 1.0, TARGET_HEIGHT, dtype=np.float32)[:, None]
        xx = np.linspace(-1.0, 1.0, TARGET_WIDTH, dtype=np.float32)[None, :]
        dist2 = (xx * 0.92) ** 2 + (yy * 1.04) ** 2
        vignette = np.clip(1.0 - 0.34 * np.clip(dist2 - 0.22, 0.0, 1.5), 0.52, 1.0)
        arr *= vignette[:, :, None]

        # Subtle organic 35mm cinema film grain (prevents banding & enriches dark tones)
        grain = rng.normal(loc=0.0, scale=2.9, size=arr.shape).astype(np.float32)
        arr = np.clip(arr + grain, 0.0, 255.0).astype(np.uint8)
        return Image.fromarray(arr)
