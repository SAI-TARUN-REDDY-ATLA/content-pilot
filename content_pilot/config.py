"""Settings shared across the pipeline. Override with environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
    claude_model: str = os.getenv("CONTENT_PILOT_MODEL", "claude-opus-5-5")
    voice: str = os.getenv("CONTENT_PILOT_VOICE", "en-US-ChristopherNeural")
    voice_rate: str = os.getenv("CONTENT_PILOT_VOICE_RATE", "+12%")
    footage_dir: Path = field(default_factory=lambda: Path(os.getenv("CONTENT_PILOT_FOOTAGE", ROOT / "assets" / "footage")))
    font_path: str | None = field(default_factory=_first_font)
    caption_size: int = 130
    caption_y: float = 0.62  # vertical centre of captions, as a fraction of height
