"""Topic in, finished Short out."""

import json
import random
from pathlib import Path

from . import captions, footage, render, script as script_mod, voice
from ..config import Settings


def make_video(topic: str | None, out_dir: Path, settings: Settings | None = None,
               script_path: Path | None = None, seed: int | None = None) -> Path:
    settings = settings or Settings()
    rng = random.Random(seed)

    if script_path:
        script = script_mod.load_script(script_path)
    elif topic:
        print(f"Writing script with {settings.model}...")
        script = script_mod.write_script(topic, settings.model)
    else:
        raise ValueError("Give a topic or a script file")

    slug = script_mod.slugify(script.title)
    work = out_dir / f"work_{slug}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "script.json").write_text(script.model_dump_json(indent=2))
    print(f"Script: {script.title!r} ({script.word_count()} words)")

    print(f"Voiceover with {settings.voice}...")
    audio = work / "voice.mp3"
    spoken = voice.synthesize(script.narration(), audio, settings.voice, settings.voice_rate)
    duration = footage.probe_duration(audio) + 0.3

    tokens = [t for s in script.sentences() for t in s.split()]
    cues = captions.align(tokens, spoken, script_mod.emphasized_words(script))
    (work / "captions.json").write_text(json.dumps([c.__dict__ for c in cues], indent=1))
    print(f"Rendering {len(cues)} captions...")
    overlay = captions.build_overlay(cues, duration, work, settings.width, settings.height,
                                     settings.font_path, settings.caption_size, settings.caption_y)

    background = footage.pick_background(settings.footage_dir, rng)
    print(f"Background: {background.name}")
    out = out_dir / f"{slug}.mp4"
    render.render(background, overlay, audio, out, duration, settings.width, settings.height, settings.fps, rng)

    (out_dir / f"{slug}.json").write_text(json.dumps({
        "title": script.title,
        "description": script.description,
        "hashtags": script.hashtags,
        "duration": round(duration, 2),
        "background": background.name,
        "topic": topic,
    }, indent=2))
    print(f"Done: {out} ({duration:.1f}s)")
    return out
