"""Voiceover with word timings, using Microsoft Edge's free neural TTS."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

ATTEMPTS = 3


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
    """Write an MP3 to `out` and return the spoken words with their timings.

    The free Edge endpoint sometimes stalls mid-stream, so each attempt has a hard time limit."""
    out.parent.mkdir(parents=True, exist_ok=True)
    limit = 60 + len(text.split()) * 0.5  # seconds; a 5-minute script normally takes about a minute
    error: Exception | None = None
    for attempt in range(ATTEMPTS):
        try:
            words = asyncio.run(asyncio.wait_for(_synthesize(text, out, voice, rate), limit))
            if words:
                return words
            error = RuntimeError("Edge TTS returned no word timings")
        except Exception as e:  # TimeoutError, dropped websocket, 403 during a handshake rotation
            error = e
        print(f"  voiceover attempt {attempt + 1} failed: {type(error).__name__}: {error}")
    raise RuntimeError(f"Edge TTS failed {ATTEMPTS} times: {error}")
