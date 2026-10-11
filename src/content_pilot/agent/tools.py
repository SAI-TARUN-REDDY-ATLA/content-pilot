"""Tools the producer agent calls to check scripts and turn them into videos."""

import json
import random
from pathlib import Path

from langchain.tools import tool
from pydantic import ValidationError

from ..config import OUTPUT_DIR, ROOT, STUDIO_DIR, Settings
from ..library import Library
from ..pipeline import make_video
from ..pipeline.script import Script, emphasized_words


def studio_path(path: str) -> Path:
    """Map an agent path like /scripts/x.json onto studio/, refusing to escape it."""
    resolved = (STUDIO_DIR / path.lstrip("/")).resolve()
    if STUDIO_DIR.resolve() not in resolved.parents:
        raise ValueError(f"{path} is outside the studio")
    return resolved


@tool
def check_script(path: str) -> str:
    """Validate a script JSON file against the Short format and the retention rules.

    Args:
        path: Studio path to the script, e.g. /scripts/great-emu-war.json
    """
    try:
        script = Script.model_validate(json.loads(studio_path(path).read_text()))
    except FileNotFoundError:
        return f"No file at {path}"
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        return f"INVALID: {e}"

    problems = []
    words = script.word_count()
    if not 85 <= words <= 115:
        problems.append(f"narration is {words} words; target 85-115")
    for s in script.sentences():
        n = len(s.split())
        if n >= 14:
            problems.append(f"{n} words, too long: {s!r}")
    if script.hook.lower().startswith(("did you know", "hey", "hi ", "welcome")):
        problems.append("hook opens with a banned opener")
    if not any(emphasized_words(script)):
        problems.append("no *emphasised* words for caption highlights")
    if len(script.title) > 70:
        problems.append(f"title is {len(script.title)} chars; max 70")
    if not 3 <= len(script.hashtags) <= 6:
        problems.append(f"{len(script.hashtags)} hashtags; want 3-6")

    est = words / 3.1  # ~3.1 words/s at the default +12% voice rate
    head = f"{script.title!r}: {words} words, ~{est:.0f}s spoken"
    return head + ("\nOK" if not problems else "\nFix:\n- " + "\n- ".join(problems))


@tool
def render_video(path: str, voice: str | None = None, seed: int | None = None) -> str:
    """Render a checked script into a finished 9:16 MP4 (voice, captions, footage).
    Slow and needs a person's approval; only call once check_script says OK.

    Args:
        path: Studio path to the script, e.g. /scripts/great-emu-war.json
        voice: Optional Edge TTS voice such as en-US-AndrewNeural
        seed: Optional seed so the background clip choice is repeatable
    """
    settings = Settings()
    if voice:
        settings.voice = voice
    out = make_video(None, OUTPUT_DIR, settings, script_path=studio_path(path),
                     seed=seed if seed is not None else random.randrange(10**6))
    meta = json.loads(out.with_suffix(".json").read_text())
    return f"Rendered {out.relative_to(ROOT)} ({meta['duration']}s, background {meta['background']})"


@tool
def list_videos() -> str:
    """Every video the channel has made, newest first, with retention once YouTube reports it:
    views, average % of the Short watched and average seconds watched. Use it to avoid repeating
    topics and to learn which hooks and topics hold viewers."""
    rows = []
    for entry in reversed(Library().entries()):
        meta, st = entry.metadata, entry.stats
        perf = (f"{st.get('views', 0)} views, {st.get('averageViewPercentage', 0):.0f}% watched, "
                f"{st.get('averageViewDuration', 0)}s avg" if st else "no stats yet")
        hook = meta.get("hook", "")
        rows.append(f"- {meta.get('date', entry.id[:10])} | {meta.get('title')} | topic: {meta.get('topic')} | "
                    f"{meta.get('status')} | {perf}" + (f"\n  hook: {hook}" if hook else ""))
    return "\n".join(rows) or "No videos yet."
