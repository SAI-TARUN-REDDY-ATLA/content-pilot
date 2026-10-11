"""Command line for the pipeline: content-pilot --topic "..." """

import argparse
from pathlib import Path

from .config import Settings
from .pipeline import make_video


def main() -> None:
    parser = argparse.ArgumentParser(prog="content_pilot", description="Generate a vertical Short from a topic.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help="What the video is about; Claude writes the script")
    src.add_argument("--script", type=Path, help="Use an existing script JSON instead of calling Claude")
    parser.add_argument("--out", type=Path, default=Path("output"), help="Output folder (default: output/)")
    parser.add_argument("--voice", help="Edge TTS voice, e.g. en-US-AndrewNeural")
    parser.add_argument("--footage", type=Path, help="Folder of background clips")
    parser.add_argument("--seed", type=int, help="Make clip choice and start offset repeatable")
    args = parser.parse_args()

    settings = Settings()
    if args.voice:
        settings.voice = args.voice
    if args.footage:
        settings.footage_dir = args.footage
    make_video(args.topic, args.out, settings, script_path=args.script, seed=args.seed)


if __name__ == "__main__":
    main()
