"""Tools the producer agent calls to check scripts and turn them into videos."""

import json
import random
import re
from pathlib import Path

from langchain.tools import tool
from pydantic import ValidationError

from ..config import OUTPUT_DIR, ROOT, STUDIO_DIR, Settings
from ..library import Library
from ..pipeline import make_video
from ..pipeline.script import Script, emphasized_words, word_range


def studio_path(path: str) -> Path:
    """Map an agent path like /scripts/x.json onto studio/, refusing to escape it."""
    resolved = (STUDIO_DIR / path.lstrip("/")).resolve()
    if STUDIO_DIR.resolve() not in resolved.parents:
        raise ValueError(f"{path} is outside the studio")
    return resolved


@tool
def check_script(path: str) -> str:
    """Validate a script JSON file against the cartoon history format and the retention rules.

    Args:
        path: Studio path to the script, e.g. /scripts/great-emu-war.json
    """
    try:
        script = Script.model_validate(json.loads(studio_path(path).read_text()))
    except FileNotFoundError:
        return f"No file at {path}"
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        return f"INVALID: {e}"

    minutes = Settings().minutes
    lo, hi = word_range(minutes)
    problems = []
    words = script.word_count()
    if not lo <= words <= hi:
        problems.append(f"narration is {words} words; target {lo}-{hi} for {minutes:g} minutes")
    if not 4 <= len(script.chapters) <= 8:
        problems.append(f"{len(script.chapters)} chapters; want 4-8")
    for chapter in script.chapters:
        if len(chapter.title) > 40:
            problems.append(f"chapter title over 40 chars: {chapter.title!r}")
        if not chapter.scenes:
            problems.append(f"chapter {chapter.title!r} has no scenes")
    scenes = script.scenes()
    for n, scene in enumerate(scenes, 1):
        count = len(scene.narration.split())
        if not 8 <= count <= 45:
            problems.append(f"scene {n} narration is {count} words; want 8-45")
        for sentence in re.split(r"(?<=[.!?])\s+", scene.narration):
            if len(sentence.split()) >= 25:
                problems.append(f"scene {n}: sentence too long: {sentence!r}")
        if len(scene.image.split()) < 8:
            problems.append(f"scene {n}: image description too thin to draw")
    if script.hook.lower().startswith(("did you know", "hey", "hi ", "welcome", "in this video")):
        problems.append("hook opens with a banned opener")
    if not any(emphasized_words(script)):
        problems.append("no *emphasised* words for subtitle highlights")
    if len(script.title) > 70:
        problems.append(f"title is {len(script.title)} chars; max 70")
    if not 3 <= len(script.hashtags) <= 6:
        problems.append(f"{len(script.hashtags)} hashtags; want 3-6")
    if not 1 <= len(script.thumbnail_text.split()) <= 4:
        problems.append("thumbnail_text should be 1-4 words")
    if len(script.thumbnail_image.split()) < 8:
        problems.append("thumbnail_image description too thin to draw")

    head = (f"{script.title!r}: {words} words, {len(script.chapters)} chapters, {len(scenes)} scenes, "
            f"~{script.minutes():.1f} min spoken")
    return head + ("\nOK" if not problems else "\nFix:\n- " + "\n- ".join(problems))


@tool
def render_video(path: str, voice: str | None = None, seed: int | None = None) -> str:
    """Render a checked script into a finished 16:9 MP4: voice, one generated cartoon per scene,
    subtitles, music and a thumbnail. Slow, costs image-generation credits, and needs a person's
    approval; only call once check_script says OK.

    Args:
        path: Studio path to the script, e.g. /scripts/great-emu-war.json
        voice: Optional Edge TTS voice such as en-US-AndrewNeural
        seed: Optional seed so camera moves and music choice are repeatable
    """
    settings = Settings()
    if voice:
        settings.voice = voice
    out = make_video(None, OUTPUT_DIR, settings, script_path=studio_path(path),
                     seed=seed if seed is not None else random.randrange(10**6))
    meta = json.loads(out.with_suffix(".json").read_text())
    return (f"Rendered {out.relative_to(ROOT)} ({meta['duration'] / 60:.1f} min, {meta['scenes']} scenes, "
            f"thumbnail {meta['thumbnail']})\nChapters:\n{meta['chapters']}")


@tool
def list_videos() -> str:
    """Every video the channel has made, newest first, with retention once YouTube reports it:
    views, average % of the video watched and average seconds watched. Use it to avoid repeating
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
