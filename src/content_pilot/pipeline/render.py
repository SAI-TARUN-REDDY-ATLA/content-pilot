"""Compose scene art, subtitles, voiceover and music into a 16:9 MP4.

Every scene image becomes its own clip with a slow zoom or pan (the "Ken Burns" move), rendered in
parallel; the clips are joined and the subtitles, voice and music are laid over them in one pass.
"""

import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ZOOM = 0.12  # how far a scene zooms or pans over its length
MOVES = ("in", "out", "left", "right")


def motion(move: str, frames: int) -> str:
    """zoompan expressions (z, x, y) for one move over `frames` frames."""
    t = f"(on/{max(frames - 1, 1)})"
    centre_x, centre_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if move == "in":
        return f"z='1+{ZOOM}*{t}':x='{centre_x}':y='{centre_y}'"
    if move == "out":
        return f"z='{1 + ZOOM}-{ZOOM}*{t}':x='{centre_x}':y='{centre_y}'"
    pan = f"(iw-iw/zoom)*{t}" if move == "right" else f"(iw-iw/zoom)*(1-{t})"
    return f"z='{1 + ZOOM}':x='{pan}':y='{centre_y}'"


def scene_clip(image: Path, out: Path, frames: int, move: str, width: int, height: int, fps: int) -> Path:
    # Upscale first: zoompan rounds to whole pixels, which jitters on a small source.
    vf = (f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,crop={width * 2}:{height * 2},"
          f"zoompan={motion(move, frames)}:d={frames}:s={width}x{height}:fps={fps},setsar=1,format=yuv420p")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out)],
        check=True,
    )
    return out


def scene_frames(starts: list[float], duration: float, fps: int) -> list[int]:
    """Frames per scene from scene start times, rounded on the cumulative clock so cuts never drift."""
    bounds = [round(s * fps) for s in starts] + [round(duration * fps)]
    bounds[0] = 0
    return [max(b - a, 1) for a, b in zip(bounds, bounds[1:])]


def render(images: list[Path], starts: list[float], captions: Path, voice: Path, out: Path, duration: float,
           workdir: Path, music: Path | None = None, music_volume: float = 0.1,
           width: int = 1920, height: int = 1080, fps: int = 30, rng: random.Random | None = None) -> Path:
    rng = rng or random.Random()
    clips_dir = workdir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    frames = scene_frames(starts, duration, fps)
    moves, last = [], None
    for _ in images:  # never the same move twice in a row
        last = rng.choice([m for m in MOVES if m != last])
        moves.append(last)
    jobs = [(img, clips_dir / f"clip_{i:03d}.mp4", n, mv)
            for i, (img, n, mv) in enumerate(zip(images, frames, moves))]
    with ThreadPoolExecutor(max(os.cpu_count() or 2, 2)) as pool:
        clips = list(pool.map(lambda j: scene_clip(*j, width, height, fps), jobs))

    listing = workdir / "clips.txt"
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))

    inputs = ["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(captions), "-i", str(voice)]
    graph = "[0:v][1:v]overlay=0:0:format=auto[v]"
    audio = "2:a"
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        fade = max(duration - 3, 0)
        graph += (f";[3:a]volume={music_volume},afade=t=out:st={fade:.2f}:d=3[bed]"
                  f";[2:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]")
        audio = "[a]"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
         "-map", "[v]", "-map", audio, "-t", f"{duration:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)],
        check=True,
    )
    return out
