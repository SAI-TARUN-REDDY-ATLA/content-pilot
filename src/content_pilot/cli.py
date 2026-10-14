"""Command line: `content-pilot` researches a history story itself and makes the video.

    content-pilot                     # agents pick + research a topic, write, render, archive
    content-pilot --upload            # ...and upload it to YouTube
    content-pilot --topic "..."       # skip the agents: one model call writes the script
    content-pilot --script file.json --placeholder-art  # render a script, no API key needed
"""

import argparse
import sys
from pathlib import Path

from .config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="content-pilot", description=__doc__.split("\n")[0])
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--topic", help="Write a script for this topic directly, without the agent team")
    src.add_argument("--script", type=Path, help="Render an existing script JSON")
    parser.add_argument("--upload", action="store_true", help="Upload the finished video to YouTube")
    parser.add_argument("--out", type=Path, default=Path("output"),
                        help="Output folder for --topic/--script (default: output/)")
    parser.add_argument("--voice", help="Edge TTS voice, e.g. en-US-AndrewNeural")
    parser.add_argument("--music", type=Path, help="Folder of background music tracks")
    parser.add_argument("--placeholder-art", action="store_true",
                        help="Draw plain scene cards instead of generating images (free, for previews)")
    parser.add_argument("--minutes", type=float, help="Target video length for --topic (default 5)")
    parser.add_argument("--seed", type=int, help="Make camera moves and music choice repeatable")
    parser.add_argument("--model", help="LangChain model id, e.g. google_genai:gemini-3.7-flash")
    args = parser.parse_args()

    settings = Settings()
    if args.voice:
        settings.voice = args.voice
    if args.music:
        settings.music_dir = args.music
    if args.minutes:
        settings.minutes = args.minutes
    if args.model:
        settings.model = args.model

    if args.topic or args.script:
        if args.upload:
            parser.error("--upload only works in the default mode (no --topic/--script)")
        from .pipeline import make_video

        make_video(args.topic, args.out, settings, script_path=args.script, seed=args.seed,
                   placeholders=True if args.placeholder_art else None)
        return

    from . import daily

    try:
        entry = daily.run(upload=args.upload, settings=settings)
    except Exception as e:
        sys.exit(f"content-pilot: {type(e).__name__}: {e}")
    print(f"\nVideo: {entry.path / 'video.mp4'}")


if __name__ == "__main__":
    main()
