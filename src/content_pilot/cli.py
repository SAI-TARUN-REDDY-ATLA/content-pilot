"""Command line: `content-pilot` researches a topic itself and makes the Short.

    content-pilot                     # agents pick + research a topic, write, render, archive
    content-pilot --upload            # ...and upload it to YouTube
    content-pilot --topic "..."       # skip the agents: one model call writes the script
    content-pilot --script file.json  # render an existing script, no API key needed
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
    parser.add_argument("--footage", type=Path, help="Folder of background clips")
    parser.add_argument("--seed", type=int, help="Make clip choice and start offset repeatable")
    parser.add_argument("--model", help="LangChain model id, e.g. google_genai:gemini-3.7-flash")
    args = parser.parse_args()

    settings = Settings()
    if args.voice:
        settings.voice = args.voice
    if args.footage:
        settings.footage_dir = args.footage
    if args.model:
        settings.model = args.model

    if args.topic or args.script:
        if args.upload:
            parser.error("--upload only works in the default mode (no --topic/--script)")
        from .pipeline import make_video

        make_video(args.topic, args.out, settings, script_path=args.script, seed=args.seed)
        return

    from . import daily

    try:
        entry = daily.run(upload=args.upload, settings=settings)
    except Exception as e:
        sys.exit(f"content-pilot: {type(e).__name__}: {e}")
    print(f"\nVideo: {entry.path / 'video.mp4'}")


if __name__ == "__main__":
    main()
