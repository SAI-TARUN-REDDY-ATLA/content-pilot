"""The scheduled job: learn from past videos, make the next cartoon history video, upload it, archive everything.

    content-pilot-daily              # full run, uploads publicly
    content-pilot-daily --no-upload  # everything except the upload

1. Refresh retention stats for uploaded videos from YouTube Analytics (library/<id>/stats.json).
2. The producer's team picks a topic, researches, writes, critiques and packages it, unattended.
3. Hard checks in code, not the model: check_script must say OK (two repair rounds allowed).
4. Render (scene art, voice, subtitles, thumbnail), upload, and save every artifact in library/<date>_<slug>/.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
from datetime import date, timedelta
from pathlib import Path

from .config import Settings
from .library import Entry, Library

REPAIR_ROUNDS = 2
STATS_WINDOW_DAYS = 60


def log(msg: str) -> None:
    print(f"[daily] {msg}", flush=True)


def refresh_stats(library: Library) -> None:
    from .youtube import analytics, auth

    if not auth.configured():
        log("YouTube credentials not set; skipping stats")
        return
    recent = [e for e in library.uploaded()
              if date.fromisoformat(e.metadata["date"]) >= date.today() - timedelta(days=STATS_WINDOW_DAYS)]
    if not recent:
        return
    since = min(date.fromisoformat(e.metadata["date"]) for e in recent)
    try:
        stats = analytics.video_stats([e.metadata["youtube_id"] for e in recent], since)
    except Exception as e:  # stats are an input to judgement, never a reason to skip a day
        log(f"stats refresh failed: {e}")
        return
    for entry in recent:
        if entry.metadata["youtube_id"] in stats:
            entry.save_stats(stats[entry.metadata["youtube_id"]])
    log(f"stats refreshed for {len(stats)} of {len(recent)} recent videos")


def produce(model: str | None, today: date):
    """Run the producer team unattended until it returns a script that passes check_script."""
    from .agent import prompts
    from .agent.harness import build_agent
    from .agent.tools import check_script

    agent = build_agent(model=model, autonomous=True)
    config = {"configurable": {"thread_id": f"daily-{today.isoformat()}"}, "recursion_limit": 300}
    message = prompts.DAILY_BRIEF.format(today=today.isoformat(), minutes=f"{Settings().minutes:g}")
    for attempt in range(REPAIR_ROUNDS + 1):
        state = agent.invoke({"messages": [{"role": "user", "content": message}]}, config=config)
        result = state.get("structured_response")
        if result is None:
            raise RuntimeError("producer finished without a result")
        verdict = check_script.invoke({"path": result.script_path})
        log(f"check_script: {verdict.splitlines()[-1]}")
        if verdict.endswith("\nOK"):
            return result, verdict
        message = (f"The nightly checks rejected {result.script_path}:\n{verdict}\n"
                   "Have the scriptwriter fix every problem, re-run check_script until it says OK, "
                   "then return the result again.")
    raise RuntimeError(f"script still failing checks after {REPAIR_ROUNDS} repairs:\n{verdict}")


def hook_score(hook: str) -> int | None:
    from .agent.youtube_tools import score_hooks

    m = re.search(r"VERDICT\s+(\d+)", score_hooks.invoke({"hooks": [hook]}))
    return int(m.group(1)) if m else None


def run(upload: bool, model: str | None = None, settings: Settings | None = None,
        placeholders: bool | None = None) -> Entry:
    from .agent.tools import studio_path
    from .pipeline import make_video
    from .pipeline.script import load_script

    settings = settings or Settings()
    model = model or settings.model
    library = Library()
    today = date.today()
    refresh_stats(library)

    log(f"producer team at work ({settings.minutes:g}-minute video)")
    result, verdict = produce(model, today)
    script_file = studio_path(result.script_path)
    script = load_script(script_file)

    entry = library.create(result.slug, today)
    log(f"archiving to {entry.path}")
    entry.update(date=today.isoformat(), topic=result.topic, slug=result.slug, title=script.title,
                 hook=script.hook, description=script.description, hashtags=script.hashtags,
                 thumbnail_text=result.thumbnail_text, why=result.why, check=verdict,
                 hook_score=hook_score(script.hook), model=model,
                 run_url=_run_url(), release_url=_release_url(entry), status="scripted")
    entry.add(script_file, "script.json")
    for src, name in ((result.research_path, "research.md"), (result.package_path, "package.md")):
        try:
            entry.add(studio_path(src), name)
        except ValueError:
            pass

    try:
        with tempfile.TemporaryDirectory() as tmp:
            video = make_video(None, Path(tmp), settings, script_path=script_file,
                               seed=int(today.strftime("%Y%m%d")), placeholders=placeholders)
            render_meta = json.loads(video.with_suffix(".json").read_text())
            work = Path(tmp) / f"work_{video.stem}"
            entry.add(video, "video.mp4")
            for name in ("voice.mp3", "captions.json", "scenes.json", "thumbnail.jpg"):
                entry.add(work / name)
        entry.update(status="rendered", duration=render_meta["duration"], chapters=render_meta["chapters"],
                     scenes=render_meta["scenes"], music=render_meta["music"],
                     placeholder_art=render_meta["placeholder_art"])
        log(f"rendered {render_meta['duration'] / 60:.1f} min, {render_meta['scenes']} scenes")
        if upload and render_meta["placeholder_art"]:
            raise RuntimeError("rendered with placeholder art (no GOOGLE_API_KEY); refusing to publish")

        if upload:
            from .youtube.upload import upload as yt_upload

            up = yt_upload(entry.path / "video.mp4", script.title, script.description, script.hashtags,
                           render_meta["chapters"], entry.path / "thumbnail.jpg")
            entry.update(status="uploaded", youtube_id=up["id"], youtube_url=up["url"], privacy=up["privacy"],
                         thumbnail=up["thumbnail"])
            log(f"uploaded {up['url']} ({up['privacy']}), thumbnail {up['thumbnail']}")
            if up["privacy"] != "public":
                log("YouTube kept it non-public: unaudited API projects can only upload private videos")
    except Exception as e:
        entry.update(status="failed", error=f"{type(e).__name__}: {e}")
        raise
    finally:
        library.record(entry)
        _github_output(entry=entry.id)
    return entry


def _run_url() -> str | None:
    if os.getenv("GITHUB_RUN_ID"):
        return f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
    return None


def _release_url(entry: Entry) -> str | None:
    """The workflow publishes video.mp4 to a release tagged video-<entry id>."""
    if os.getenv("GITHUB_REPOSITORY"):
        return f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/releases/tag/video-{entry.id}"
    return None


def _github_output(**values) -> None:
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="content-pilot-daily", description=__doc__.split("\n")[0])
    parser.add_argument("--no-upload", action="store_true", help="Do everything except the YouTube upload")
    parser.add_argument("--model", help="Override the model, e.g. google_genai:gemini-3.1-pro-preview")
    args = parser.parse_args()
    try:
        entry = run(upload=not args.no_upload, model=args.model)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    log(f"done: {entry.path}")


if __name__ == "__main__":
    main()
