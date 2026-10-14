"""Cartoon art for every scene and the thumbnail, generated with a Gemini image model.

Without GOOGLE_API_KEY (or with placeholders=True) each scene gets a plain card showing its
description instead, so a script can be rendered and timed offline.
"""

import os
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .script import Character, Script

WORKERS = 4
RETRIES = 3
MAX_FAILED_SHARE = 0.15  # more failed scenes than this and the video is not worth publishing


class QuotaError(RuntimeError):
    """A quota that retrying won't fix: free tier (image models need billing) or the daily cap."""


PALETTE = [(46, 64, 87), (120, 60, 50), (40, 90, 70), (90, 70, 120), (110, 90, 40)]


def scene_prompt(description: str, characters: list[Character], style: str) -> str:
    """The style, then the designs of the characters this scene mentions, then the scene."""
    cast = [f"{c.name}: {c.look}" for c in characters if c.name.lower() in description.lower()]
    parts = [style]
    if cast:
        parts.append("Characters (draw them exactly like this):\n" + "\n".join(cast))
    parts.append(f"Scene: {description}")
    return "\n\n".join(parts)


def _client():
    from google import genai

    return genai.Client()  # reads GOOGLE_API_KEY


def generate(prompt: str, out: Path, model: str, client=None) -> Path:
    """One 16:9 image from `prompt`, saved as PNG. Retries transient failures."""
    from google.genai import types

    client = client or _client()
    config = types.GenerateContentConfig(response_modalities=["IMAGE"],
                                         image_config=types.ImageConfig(aspect_ratio="16:9"))
    error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    out.write_bytes(part.inline_data.data)
                    Image.open(out).convert("RGB").save(out, "PNG")  # normalise JPEG/WebP replies
                    _marker(out).unlink(missing_ok=True)
                    return out
            error = RuntimeError("model returned no image")
        except Exception as e:  # per-minute rate limits and 5xx are common; back off and retry
            text = str(e)
            if "RESOURCE_EXHAUSTED" in text and ("limit: 0" in text or "PerDay" in text):
                raise QuotaError("Gemini image quota exhausted. Image models have no free tier: enable "
                                 "billing on the GOOGLE_API_KEY project, or wait for the daily quota to reset.") from e
            error = e
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"image generation failed for {out.name}: {str(error)[:200]}")


def _marker(image: Path) -> Path:
    return image.with_suffix(".placeholder")


def ready(image: Path) -> bool:
    """A real generated image is cached; placeholders are always retried."""
    return image.exists() and not _marker(image).exists()


def placeholder(description: str, out: Path, n: int, width: int = 1920, height: int = 1080,
                font_path: str | None = None) -> Path:
    img = Image.new("RGB", (width, height), PALETTE[n % len(PALETTE)])
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, 44) if font_path else ImageFont.load_default(size=44)
    text = f"SCENE {n + 1}\n\n" + "\n".join(textwrap.wrap(description, 60)[:8])
    draw.multiline_text((width / 2, height / 2), text, font=font, fill=(240, 240, 240), anchor="mm",
                        align="center", spacing=14)
    img.save(out, "PNG")
    _marker(out).touch()
    return out


def use_placeholders() -> bool:
    return not os.getenv("GOOGLE_API_KEY")


def scene_images(script: Script, out_dir: Path, model: str, style: str, placeholders: bool | None = None,
                 font_path: str | None = None) -> list[Path]:
    """One image per scene, in order. Files already in `out_dir` are reused, so a failed render
    can be retried without paying for the art twice."""
    out_dir.mkdir(parents=True, exist_ok=True)
    placeholders = use_placeholders() if placeholders is None else placeholders
    scenes = script.scenes()
    paths = [out_dir / f"scene_{i:03d}.png" for i in range(len(scenes))]
    if placeholders:
        return [p if p.exists() else placeholder(s.image, p, i, font_path=font_path)
                for i, (s, p) in enumerate(zip(scenes, paths))]

    client = _client()
    todo = [(i, s, p) for i, (s, p) in enumerate(zip(scenes, paths)) if not ready(p)]
    stop = threading.Event()

    def make(item):
        i, scene, path = item
        if stop.is_set():
            return None
        try:
            return generate(scene_prompt(scene.image, script.characters, style), path, model, client)
        except QuotaError:
            stop.set()
            raise
        except RuntimeError as e:
            print(f"  {e}; using a placeholder")
            placeholder(scene.image, path, i, font_path=font_path)
            return None

    with ThreadPoolExecutor(WORKERS) as pool:
        failed = sum(r is None for r in pool.map(make, todo))
    if failed > MAX_FAILED_SHARE * len(scenes):
        raise RuntimeError(f"{failed} of {len(scenes)} scene images failed")
    return paths


def thumbnail(script: Script, out: Path, model: str, style: str, font_path: str | None,
              placeholders: bool | None = None) -> Path:
    """A 1280x720 JPEG: the generated scene with the thumbnail words stamped on the left."""
    placeholders = use_placeholders() if placeholders is None else placeholders
    art = out.with_name("thumbnail_art.png")
    if placeholders:
        if not art.exists():
            placeholder(script.thumbnail_image, art, 0, font_path=font_path)
    elif not ready(art):
        prompt = scene_prompt(script.thumbnail_image, script.characters, style)
        generate(prompt + "\n\nLeave the left third of the frame simple and uncluttered.", art, model)
    img = Image.open(art).convert("RGB").resize((1280, 720))
    draw = ImageDraw.Draw(img)
    words = script.thumbnail_text.upper().split()
    lines = textwrap.wrap(" ".join(words), 10) or [""]
    size = 150
    font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default(size=size)
    while max(draw.textlength(l, font=font) for l in lines) > 560 and size > 60:
        size -= 10
        font = font.font_variant(size=size)
    y = 360 - len(lines) * size * 0.55
    for line in lines:
        draw.text((40, y), line, font=font, fill=(255, 226, 0), stroke_width=max(6, size // 12),
                  stroke_fill=(0, 0, 0))
        y += size * 1.1
    img.save(out, "JPEG", quality=90)
    return out
