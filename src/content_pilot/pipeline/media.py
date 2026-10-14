"""Probe media files and pick background music."""

import json
import random
import subprocess
from pathlib import Path

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".aac"}


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def pick_music(music_dir: Path, rng: random.Random | None = None) -> Path | None:
    """A random royalty-free track from assets/music/, or None to go without music."""
    rng = rng or random.Random()
    tracks = sorted(p for p in music_dir.glob("*") if p.suffix.lower() in AUDIO_EXTS) if music_dir.is_dir() else []
    return rng.choice(tracks) if tracks else None
