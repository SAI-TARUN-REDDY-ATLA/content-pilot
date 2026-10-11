"""Agent tools wrapping the youtube_kit analysis scripts (hooks, titles, transcripts, retention)."""

import subprocess
import sys
import tempfile
from pathlib import Path

from langchain.tools import tool

from .tools import studio_path

KIT = Path(__file__).resolve().parent / "youtube_kit"


def _run(script: str, *args: str) -> str:
    """Run one kit script with this interpreter and return what it printed."""
    proc = subprocess.run([sys.executable, str(KIT / script), *args],
                          capture_output=True, text=True, timeout=120)
    out = (proc.stdout + proc.stderr).strip()
    return out or f"{script} printed nothing (exit {proc.returncode})"


def _input(path: str) -> str:
    """Resolve a studio path the agent gave us, failing clearly if the file is missing."""
    p = studio_path(path)
    if not p.is_file():
        raise FileNotFoundError(f"No file at {path}. Inputs from the person go in /inputs/.")
    return str(p)


def _lines_file(lines: list[str]) -> str:
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    f.write("\n".join(line.replace("\n", " ") for line in lines))
    f.close()
    return f.name


@tool
def score_hooks(hooks: list[str]) -> str:
    """Score hook lines on specificity, address, stakes, curiosity and brevity, ranked best first,
    with the formula each matches and its weakest property. A heuristic: a low score means look
    again, a high score is not a promise.

    Args:
        hooks: One or more candidate opening lines, without *emphasis* markers
    """
    return _run("yt-script/hookscore.py", _lines_file([h.replace("*", "") for h in hooks]))


@tool
def lint_title(titles: list[str], thumbnail: str | None = None) -> str:
    """Lint YouTube titles (and optionally the thumbnail text they pair with) for truncation,
    duplication between title and thumbnail, vagueness and shouting. Several titles come back ranked.

    Args:
        titles: Candidate titles
        thumbnail: Thumbnail text to check against each title, three words at most
    """
    extra = ["--thumb", thumbnail] if thumbnail else []
    if len(titles) == 1:
        return _run("yt-package/title.py", "--title", titles[0], *extra)
    return _run("yt-package/title.py", _lines_file(titles), *extra)


@tool
def find_dead_air(transcript_path: str, floor: float = 0.45) -> str:
    """Build an edit decision list from a timestamped transcript (.srt, .vtt or whisper .json):
    dead air, filler-only cues and restarted sentences, with timecodes and the runtime saved.

    Args:
        transcript_path: Studio path, e.g. /inputs/episode-12.srt
        floor: Shortest gap in seconds that counts as dead air
    """
    return _run("yt-edit/deadair.py", _input(transcript_path), "--floor", str(floor))


@tool
def make_chapters(transcript_path: str, target: int = 7) -> str:
    """Draft YouTube chapters from a timestamped transcript, validated against YouTube's rules
    (starts at 00:00, at least three, each at least 10 seconds). Titles are drafts to rewrite.

    Args:
        transcript_path: Studio path, e.g. /inputs/episode-12.srt
        target: Roughly how many chapters to aim for
    """
    return _run("yt-chapters/chapters.py", _input(transcript_path), "--target", str(target))


@tool
def read_retention(csv_path: str, transcript_path: str | None = None, duration: float | None = None) -> str:
    """Read a YouTube Studio audience-retention CSV and report the hook leak, the cliffs and the
    slide. With a transcript it names what was being said at each cliff.

    Args:
        csv_path: Studio path to the export, e.g. /inputs/retention.csv
        transcript_path: Optional studio path to the video's transcript
        duration: Video length in seconds, if the export uses percent positions
    """
    args = [_input(csv_path)]
    if transcript_path:
        args += ["--transcript", _input(transcript_path)]
    if duration:
        args += ["--duration", str(duration)]
    return _run("yt-retention/retention.py", *args)


@tool
def rank_outliers(data_path: str, min_multiple: float = 2.0) -> str:
    """Rank collected videos by how far each beat its own channel's median views, and name the
    title formula each used. Needs at least four videos per channel.

    Args:
        data_path: Studio path to a JSON list of {"channel", "title", "views", "url", "duration"}
        min_multiple: Only show videos at or above this multiple of their channel median
    """
    return _run("yt-viral/swipe.py", _input(data_path), "--min", str(min_multiple))


YOUTUBE_TOOLS = [score_hooks, lint_title, find_dead_air, make_chapters, read_retention, rank_outliers]
