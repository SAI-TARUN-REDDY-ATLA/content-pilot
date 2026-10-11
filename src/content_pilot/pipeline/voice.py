"""Voiceover with word timings, using Microsoft Edge's free neural TTS."""

import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Word:
    text: str
    start: float  # seconds
    end: float


async def _synthesize(text: str, out: Path, voice: str, rate: str) -> list[Word]:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, boundary="WordBoundary")
    words: list[Word] = []
    with out.open("wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000  # 100ns ticks
                words.append(Word(chunk["text"], start, start + chunk["duration"] / 10_000_000))
    return words


def synthesize(text: str, out: Path, voice: str, rate: str = "+0%") -> list[Word]:
    """Write an MP3 to `out` and return the spoken words with their timings."""
    out.parent.mkdir(parents=True, exist_ok=True)
    words = asyncio.run(_synthesize(text, out, voice, rate))
    if not words:
        raise RuntimeError("Edge TTS returned no word timings")
    return words
