"""Compose background, captions and voiceover into a 9:16 MP4."""

import random
import subprocess
from pathlib import Path

from .footage import probe_duration


def render(background: Path, captions: Path, audio: Path, out: Path, duration: float,
           width: int = 1080, height: int = 1920, fps: int = 30, rng: random.Random | None = None) -> Path:
    rng = rng or random.Random()
    bg_len = probe_duration(background)
    # Start somewhere random in long clips so repeated videos don't share an opening.
    offset = rng.uniform(0, bg_len - duration) if bg_len > duration + 1 else 0.0
    out.parent.mkdir(parents=True, exist_ok=True)
    video_filter = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={fps},setsar=1[bg];"
        f"[bg][1:v]overlay=0:0:format=auto[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-stream_loop", "-1", "-ss", f"{offset:.2f}", "-i", str(background),
        "-i", str(captions),
        "-i", str(audio),
        "-filter_complex", video_filter,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out
