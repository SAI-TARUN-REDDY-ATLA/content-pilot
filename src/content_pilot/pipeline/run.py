"""Topic in, finished long-form cartoon history video out."""

import json
import random
from pathlib import Path

from . import captions, images, media, render, script as script_mod, voice
from ..config import Settings


def timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chapter_list(chapters: list[tuple[str, float]]) -> str:
    """YouTube chapters for the description: the first must be 0:00."""
    return "\n".join(f"{timestamp(0 if i == 0 else start)} {title}" for i, (title, start) in enumerate(chapters))


def scene_starts(script: script_mod.Script, cues: list[captions.Cue]) -> list[float]:
    """When each scene's first word is spoken. align() drops tokens that are only '*'."""
    starts, i = [], 0
    for scene in script.scenes():
        starts.append(cues[min(i, len(cues) - 1)].start)
        i += sum(1 for t in scene.narration.split() if t.replace("*", "").strip())
    starts[0] = 0.0
    return starts


def make_video(topic: str | None, out_dir: Path, settings: Settings | None = None,
               script_path: Path | None = None, seed: int | None = None,
               placeholders: bool | None = None) -> Path:
    settings = settings or Settings()
    rng = random.Random(seed)

    if script_path:
        script = script_mod.load_script(script_path)
    elif topic:
        print(f"Writing script with {settings.model}...")
        script = script_mod.write_script(topic, settings.model, settings.minutes)
    else:
        raise ValueError("Give a topic or a script file")

    slug = script_mod.slugify(script.title)
    work = out_dir / f"work_{slug}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "script.json").write_text(script.model_dump_json(indent=2))
    scenes = script.scenes()
    print(f"Script: {script.title!r} ({script.word_count()} words, {len(scenes)} scenes, ~{script.minutes():.1f} min)")

    print(f"Voiceover with {settings.voice}...")
    audio = work / "voice.mp3"
    spoken = voice.synthesize(script.narration(), audio, settings.voice, settings.voice_rate)
    duration = media.probe_duration(audio) + 1.0

    tokens = [t for s in script.sentences() for t in s.split()]
    cues = captions.align(tokens, spoken, script_mod.emphasized_words(script))
    (work / "captions.json").write_text(json.dumps([c.__dict__ for c in cues], indent=1))
    starts = scene_starts(script, cues)
    chapters, n = [], 0
    for chapter in script.chapters:
        chapters.append((chapter.title, starts[n]))
        n += len(chapter.scenes)

    placeholders = images.use_placeholders() if placeholders is None else placeholders
    print(f"Scene art: {len(scenes)} images" + (" (placeholders)" if placeholders else f" with {settings.image_model}"))
    art = images.scene_images(script, work / "images", settings.image_model, settings.art_style,
                              placeholders, settings.font_path)
    thumb = images.thumbnail(script, work / "thumbnail.jpg", settings.image_model, settings.art_style,
                             settings.font_path, placeholders)

    print("Subtitles...")
    overlay = captions.build_overlay(cues, duration, work, settings.width, settings.height,
                                     settings.font_path, settings.caption_size, settings.caption_y)
    music = media.pick_music(settings.music_dir, rng)
    print(f"Rendering {duration / 60:.1f} min" + (f" with music {music.name}" if music else " without music"))
    out = out_dir / f"{slug}.mp4"
    render.render(art, starts, overlay, audio, out, duration, work, music, settings.music_volume,
                  settings.width, settings.height, settings.fps, rng)

    (work / "scenes.json").write_text(json.dumps(
        [{"start": round(t, 2), "image": p.name, "description": s.image} for t, p, s in zip(starts, art, scenes)],
        indent=1))
    (out_dir / f"{slug}.json").write_text(json.dumps({
        "title": script.title,
        "description": script.description,
        "hashtags": script.hashtags,
        "chapters": chapter_list(chapters),
        "duration": round(duration, 2),
        "scenes": len(scenes),
        "music": music.name if music else None,
        "placeholder_art": placeholders,
        "thumbnail": str(thumb),
        "topic": topic,
    }, indent=2))
    print(f"Done: {out} ({duration / 60:.1f} min)")
    return out
