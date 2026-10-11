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


@dataclass
class Settings:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    # Any LangChain "provider:model" id; Gemini needs GOOGLE_API_KEY.
    model: str = os.getenv("CONTENT_PILOT_MODEL", "google_genai:gemini-3.7-flash")
    voice: str = os.getenv("CONTENT_PILOT_VOICE", "en-US-ChristopherNeural")
    voice_rate: str = os.getenv("CONTENT_PILOT_VOICE_RATE", "+12%")
    footage_dir: Path = field(default_factory=lambda: Path(os.getenv("CONTENT_PILOT_FOOTAGE", ASSETS_DIR / "footage")))
    font_path: str | None = field(default_factory=_first_font)
    caption_size: int = 130
    caption_y: float = 0.62  # vertical centre of captions, as a fraction of height
