"""Write a short-form script for a topic with Claude."""

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You write scripts for 30-45 second vertical videos (YouTube Shorts) in the \
fast "brain rot" style: relentless pacing, no filler, every line pulling the viewer to the next.

Retention rules:
- The hook is the first thing heard. It must create an open loop in under two seconds: a shocking \
claim, a direct "you", or a question the viewer needs answered. Never open with a greeting, \
the channel, or "Did you know".
- Every sentence is short (under 14 words) and adds a new fact, twist, or escalation.
- Put a pattern interrupt roughly every 8 seconds ("But here's the crazy part", "Wait.", a sudden number).
- Hold the payoff of the hook until near the end.
- The final line flows straight back into the hook so the video loops seamlessly when replayed.
- Plain spoken English. No emojis, hashtags, stage directions, or markdown in the narration.
- Wrap 1-3 punchy words per sentence in *asterisks*; they will be highlighted in the captions.
- Total narration (hook + lines + loop_line) is 85-115 words.
- Stay factual. If the topic is a rumour, say so rather than inventing details."""


class Script(BaseModel):
    title: str = Field(description="YouTube title under 70 characters, curiosity-driven")
    hook: str = Field(description="First spoken sentence; the scroll-stopper")
    lines: list[str] = Field(description="Body sentences in order")
    loop_line: str = Field(description="Last sentence, written to flow back into the hook")
    description: str = Field(description="One or two sentence YouTube description")
    hashtags: list[str] = Field(description="3-6 hashtags without the # symbol")

    def sentences(self) -> list[str]:
        return [self.hook, *self.lines, self.loop_line]

    def narration(self) -> str:
        """Text sent to TTS: emphasis markers removed."""
        return " ".join(strip_emphasis(s) for s in self.sentences())

    def word_count(self) -> int:
        return len(self.narration().split())


def strip_emphasis(text: str) -> str:
    return text.replace("*", "")


def emphasized_words(script: Script) -> list[bool]:
    """One flag per narration word: True when it sat inside *asterisks*."""
    flags: list[bool] = []
    for sentence in script.sentences():
        inside = False
        for token in sentence.split():
            starts = token.startswith("*")
            if starts:
                inside = True
            flags.append(inside)
            if token.rstrip(".,!?;:'\"").endswith("*"):
                inside = False
    return flags


def write_script(topic: str, model: str, angle: str | None = None) -> Script:
    """Ask Claude for a script. Needs ANTHROPIC_API_KEY (or another Anthropic credential)."""
    import anthropic

    client = anthropic.Anthropic()
    prompt = f"Topic: {topic}"
    if angle:
        prompt += f"\nAngle: {angle}"
    response = client.beta.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": "medium"},
        output_format=Script,
        # If a safety classifier declines, the API retries on a suitable fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to write a script for {topic!r}")
    if response.parsed_output is None:
        raise RuntimeError(f"No script returned (stop_reason={response.stop_reason})")
    return response.parsed_output


def load_script(path: Path) -> Script:
    return Script.model_validate(json.loads(Path(path).read_text()))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "video"
