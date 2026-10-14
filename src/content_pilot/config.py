"""Settings shared across the pipeline. Override with environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Project root (repo checkout). Override when the package is installed elsewhere.
ROOT = Path(os.getenv("CONTENT_PILOT_HOME", Path(__file__).resolve().parents[2]))
# Local secrets and overrides. Real environment variables (e.g. GitHub secrets) win.
load_dotenv(ROOT / ".env", override=False)

ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"

STUDIO_DIR = ROOT / "studio"  # the producer agent's workspace
LIBRARY_DIR = ROOT / "library"  # every finished video and what made it

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/impact.ttf",
]


def _first_font() -> str | None:
    override = os.getenv("CONTENT_PILOT_FONT")
    if override:
        return override
    return next((f for f in FONT_CANDIDATES if Path(f).exists()), None)


# The channel's look. Every scene image and the thumbnail are drawn in this style.
ART_STYLE = os.getenv("CONTENT_PILOT_ART_STYLE", (
    "Flat 2D cartoon illustration in the style of a comedic animated history explainer: bold clean "
    "black outlines, simple rounded characters with big expressive eyes and exaggerated emotions, "
    "flat bright colours with soft cel shading, simple uncluttered backgrounds, historically "
    "accurate clothing and objects, 16:9 widescreen composition. No text, letters, captions, signs, "
    "speech bubbles or watermarks anywhere in the image."
))


@dataclass
class Settings:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    # Target video length; the script's narration is sized to it. Raise it as the channel grows.
    minutes: float = float(os.getenv("CONTENT_PILOT_MINUTES", "5"))
    # Any LangChain "provider:model" id; Gemini needs GOOGLE_API_KEY.
    model: str = os.getenv("CONTENT_PILOT_MODEL", "google_genai:gemini-3.7-flash")
    # Gemini image model for scene art and thumbnails (same GOOGLE_API_KEY).
    image_model: str = os.getenv("CONTENT_PILOT_IMAGE_MODEL", "gemini-2.5-flash-image")
    art_style: str = ART_STYLE
    voice: str = os.getenv("CONTENT_PILOT_VOICE", "en-US-AndrewNeural")
    voice_rate: str = os.getenv("CONTENT_PILOT_VOICE_RATE", "+0%")
    music_dir: Path = field(default_factory=lambda: Path(os.getenv("CONTENT_PILOT_MUSIC", ASSETS_DIR / "music")))
    music_volume: float = float(os.getenv("CONTENT_PILOT_MUSIC_VOLUME", "0.10"))
    font_path: str | None = field(default_factory=_first_font)
    caption_size: int = 58
    caption_y: float = 0.9  # vertical centre of subtitles, as a fraction of height
