"""Word-by-word "pop" captions, drawn with Pillow and stitched into a transparent overlay.

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
POP_SECONDS = 0.07  # how long a word shows enlarged before settling


@dataclass
class Cue:
    text: str
    start: float
    end: float
    emphasis: bool = False


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
        text = token.replace("*", "").strip().rstrip(".,;:")
        if not text:
            continue
        # Hold each word until the next one starts so captions never blink off mid-sentence,
        # but drop them during long pauses.
        end = ends[i]
        if i + 1 < len(tokens) and starts[i + 1] is not None and starts[i + 1] - end < 0.6:
            end = starts[i + 1]
        cues.append(Cue(text, starts[i], end, emphasis[i]))
    return cues


def _font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def render_frame(text: str, width: int, height: int, y_frac: float, font: ImageFont.FreeTypeFont, color) -> Image.Image:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    label = text.upper()
    stroke = max(6, font.size // 11)
    # Shrink very long words so they fit inside the frame.
    while draw.textlength(label, font=font) + 2 * stroke > width * 0.9 and font.size > 40:
        font = font.font_variant(size=int(font.size * 0.9))
    draw.text(
        (width / 2, height * y_frac),
        label,
        font=font,
        fill=color,
        anchor="mm",
        stroke_width=stroke,
        stroke_fill=BLACK,
    )
    return img


def build_overlay(cues: list[Cue], duration: float, workdir: Path, width: int, height: int,
                  font_path: str | None, size: int, y_frac: float) -> Path:
    """Render cues to PNGs and stitch them into a transparent .mov the length of the video."""
    frames = workdir / "caption_frames"
    frames.mkdir(parents=True, exist_ok=True)
    base_font = _font(font_path, size)
    pop_font = base_font.font_variant(size=int(size * 1.18))

    blank = frames / "blank.png"
    Image.new("RGBA", (width, height), (0, 0, 0, 0)).save(blank)

    entries: list[tuple[Path, float]] = []
    clock = 0.0
    for n, cue in enumerate(cues):
        if cue.start > clock + 0.01:
            entries.append((blank, cue.start - clock))
        color = YELLOW if cue.emphasis else WHITE
        pop = frames / f"{n:04d}_pop.png"
        rest = frames / f"{n:04d}.png"
        render_frame(cue.text, width, height, y_frac, pop_font, color).save(pop)
        render_frame(cue.text, width, height, y_frac, base_font, color).save(rest)
        length = max(cue.end - cue.start, 0.05)
        pop_len = min(POP_SECONDS, length / 2)
        entries.append((pop, pop_len))
        entries.append((rest, length - pop_len))
        clock = cue.start + length
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
