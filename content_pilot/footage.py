"""Pick background footage, or make a placeholder loop when none is supplied."""

import json
import random
import subprocess
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}
PLACEHOLDER = "_placeholder.mp4"


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def make_placeholder(path: Path, seconds: int = 20) -> Path:
    """A hypnotic colour-cycling gradient loop. Replace with real gameplay/satisfying clips."""
    path.parent.mkdir(parents=True, exist_ok=True)
    source = f"gradients=s=540x960:r=30:n=5:speed=0.03:type=spiral:d={seconds}"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", source,
         "-vf", "hue=h=t*36:s=1.4,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", str(path)],
        check=True,
    )
    return path


def pick_background(footage_dir: Path, rng: random.Random | None = None) -> Path:
    rng = rng or random.Random()
    clips = sorted(p for p in footage_dir.glob("*") if p.suffix.lower() in VIDEO_EXTS and p.name != PLACEHOLDER)
    if clips:
        return rng.choice(clips)
    placeholder = footage_dir / PLACEHOLDER
    return placeholder if placeholder.exists() else make_placeholder(placeholder)
