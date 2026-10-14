"""Phrase subtitles with highlighted key words, drawn with Pillow and stitched into a transparent overlay.

This avoids depending on an ffmpeg build with libass or drawtext, which many
Homebrew and static builds lack.
"""

import difflib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .voice import Word

WHITE = (255, 255, 255, 255)
YELLOW = (255, 226, 0, 255)
BLACK = (0, 0, 0, 255)
MAX_PHRASE_WORDS = 7
MAX_PHRASE_CHARS = 42


@dataclass
class Cue:
    text: str
    start: float
    end: float
    emphasis: bool = False
    raw: str = ""  # the script token, punctuation kept


def _norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", token.lower())


def align(tokens: list[str], spoken: list[Word], emphasis: list[bool] | None = None) -> list[Cue]:
    """Time each script token using the TTS word boundaries.

    TTS can split or merge words ("1904", "don't"), so tokens are matched with a
    sequence diff and unmatched tokens borrow time from their neighbours.
    """
    emphasis = emphasis or [False] * len(tokens)
    starts: list[float | None] = [None] * len(tokens)
    ends: list[float | None] = [None] * len(tokens)
    matcher = difflib.SequenceMatcher(a=[_norm(t) for t in tokens], b=[_norm(w.text) for w in spoken], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete" or j1 == j2:
            continue
        if tag == "equal":
            for k in range(i2 - i1):
                starts[i1 + k], ends[i1 + k] = spoken[j1 + k].start, spoken[j1 + k].end
        else:  # replace / insert: spread the spoken span evenly over the tokens
            span_start, span_end = spoken[j1].start, spoken[j2 - 1].end
            n = max(i2 - i1, 1)
            if i1 == i2:  # extra spoken words with no token: extend the previous token
                if i1 > 0 and ends[i1 - 1] is not None:
                    ends[i1 - 1] = span_end
                continue
            step = (span_end - span_start) / n
            for k in range(n):
                starts[i1 + k] = span_start + k * step
                ends[i1 + k] = span_start + (k + 1) * step

    # Fill any remaining gaps by interpolation.
    last_end = 0.0
    for i in range(len(tokens)):
        if starts[i] is None:
            nxt = next((starts[j] for j in range(i + 1, len(tokens)) if starts[j] is not None), last_end + 0.25)
            starts[i], ends[i] = last_end, max(nxt, last_end + 0.05)
        last_end = ends[i]

    cues = []
    for i, token in enumerate(tokens):
        text = token.replace("*", "").strip()
        if not text:
            continue
        # Hold each word until the next one starts so captions never blink off mid-sentence,
        # but drop them during long pauses.
        end = ends[i]
        if i + 1 < len(tokens) and starts[i + 1] is not None and starts[i + 1] - end < 0.6:
            end = starts[i + 1]
        cues.append(Cue(text, starts[i], end, emphasis[i], token.replace("*", "")))
    return cues


def _font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def phrases(cues: list[Cue], max_words: int = MAX_PHRASE_WORDS, max_chars: int = MAX_PHRASE_CHARS) -> list[list[Cue]]:
    """Group timed words into subtitle lines, breaking after punctuation, long pauses or when full."""
    groups: list[list[Cue]] = []
    current: list[Cue] = []
    for cue in cues:
        if current and (len(current) >= max_words
                        or len(" ".join(c.text for c in current + [cue])) > max_chars
                        or cue.start - current[-1].end > 0.5):
            groups.append(current)
            current = []
        current.append(cue)
        if cue.raw.endswith((".", "!", "?", ",", ";", ":")) and len(current) >= 3:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def render_frame(words: list[Cue], width: int, height: int, y_frac: float, font: ImageFont.FreeTypeFont) -> Image.Image:
    """One subtitle line, centred, emphasised words in yellow."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(4, font.size // 12)
    space = draw.textlength(" ", font=font)
    widths = [draw.textlength(w.text, font=font) for w in words]
    x = (width - sum(widths) - space * (len(words) - 1)) / 2
    for word, w in zip(words, widths):
        draw.text((x, height * y_frac), word.text, font=font, fill=YELLOW if word.emphasis else WHITE,
                  anchor="lm", stroke_width=stroke, stroke_fill=BLACK)
        x += w + space
    return img


def build_overlay(cues: list[Cue], duration: float, workdir: Path, width: int, height: int,
                  font_path: str | None, size: int, y_frac: float) -> Path:
    """Render subtitle lines to PNGs and stitch them into a transparent .mov the length of the video."""
    frames = workdir / "caption_frames"
    frames.mkdir(parents=True, exist_ok=True)
    font = _font(font_path, size)

    blank = frames / "blank.png"
    Image.new("RGBA", (width, height), (0, 0, 0, 0)).save(blank)

    entries: list[tuple[Path, float]] = []
    clock = 0.0
    for n, line in enumerate(phrases(cues)):
        start, end = line[0].start, line[-1].end
        if start > clock + 0.01:
            entries.append((blank, start - clock))
            clock = start
        frame = frames / f"{n:04d}.png"
        render_frame(line, width, height, y_frac, font).save(frame)
        length = max(end - clock, 0.05)
        entries.append((frame, length))
        clock += length
    if duration > clock:
        entries.append((blank, duration - clock))

    listing = workdir / "captions.txt"
    lines = []
    for path, seconds in entries:
        lines.append(f"file '{path.resolve()}'")
        lines.append(f"duration {seconds:.3f}")
    lines.append(f"file '{entries[-1][0].resolve()}'")  # concat demuxer needs the last file repeated
    listing.write_text("\n".join(lines) + "\n")

    out = workdir / "captions.mov"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-vf", "fps=30,format=argb", "-c:v", "qtrle", str(out)],
        check=True,
    )
    return out
