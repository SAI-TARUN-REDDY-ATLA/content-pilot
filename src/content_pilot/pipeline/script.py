"""Write a long-form cartoon history script for a topic with the configured model (Gemini by default).

A script is chapters of scenes. Each scene is a few narrated sentences plus a description of the
cartoon frame shown while they are read; one image is generated per scene.
"""

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

WORDS_PER_MINUTE = 170  # measured: en-US-AndrewNeural at +0% reads ~173

SYSTEM_PROMPT = """You write scripts for {minutes}-minute animated history videos on YouTube, told \
by a witty, slightly sarcastic narrator over cartoon illustrations (the Oversimplified / Sam O'Nella \
school): real history, told as a story, funny without being stupid.

Story rules:
- The first scene is the cold open. Its first sentence is the hook: the most absurd or dramatic \
true thing about the story, said in under three seconds. Never open with a greeting, the channel, \
"Did you know" or "In this video".
- Then tell it as a story in 4-8 chapters (setup, escalation, the turn, the aftermath). Every \
chapter opens with a re-hook: a question or a twist that makes the viewer need the next part.
- Characters are real people with motives. Give them a running gag or a catchphrase where it fits.
- Plain spoken English, short sentences (under 25 words). No emojis, hashtags or stage directions.
- Wrap 1-3 punchy words per scene in *asterisks*; they are highlighted in the subtitles.
- End on the payoff and one line that makes the viewer want the next video. No "like and subscribe".
- Total narration is {min_words}-{max_words} words, over 30-55 scenes of 8-45 words each.
- Strictly factual. Never invent quotes, numbers or events; say "reportedly" when sources disagree.

Scene images: describe one cartoon frame per scene: who is in it (use the same names as in \
`characters`), what they are doing, the setting and period details, the joke if there is one. \
Never ask for written words, signs, captions or speech bubbles in the image."""


class Scene(BaseModel):
    narration: str = Field(description="1-3 spoken sentences, 8-45 words, *emphasis* allowed")
    image: str = Field(description="The cartoon frame shown during this narration; no written text in it")


class Chapter(BaseModel):
    title: str = Field(description="Chapter name for the YouTube chapter list, under 40 characters")
    scenes: list[Scene]


class Character(BaseModel):
    name: str = Field(description="Name exactly as used in scene image descriptions")
    look: str = Field(description="Fixed cartoon design: build, face, clothes, colours, one prop")


class Script(BaseModel):
    title: str = Field(description="YouTube title under 70 characters, curiosity-driven")
    characters: list[Character] = Field(default_factory=list,
                                        description="Recurring people, so every image draws them the same")
    chapters: list[Chapter]
    description: str = Field(description="Two or three sentence YouTube description")
    hashtags: list[str] = Field(description="3-6 hashtags without the # symbol")
    thumbnail_text: str = Field(description="Thumbnail words, four at most, not repeating the title")
    thumbnail_image: str = Field(description="The thumbnail's cartoon scene: one clear focal point, big emotion")

    def scenes(self) -> list[Scene]:
        return [s for c in self.chapters for s in c.scenes]

    @property
    def hook(self) -> str:
        """The first spoken sentence."""
        first = self.chapters[0].scenes[0].narration if self.chapters and self.chapters[0].scenes else ""
        return re.split(r"(?<=[.!?])\s+", first.strip(), maxsplit=1)[0]

    def sentences(self) -> list[str]:
        return [s.narration for s in self.scenes()]

    def narration(self) -> str:
        """Text sent to TTS: emphasis markers removed."""
        return " ".join(strip_emphasis(s) for s in self.sentences())

    def word_count(self) -> int:
        return len(self.narration().split())

    def minutes(self) -> float:
        return self.word_count() / WORDS_PER_MINUTE


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


def word_range(minutes: float) -> tuple[int, int]:
    """Narration words for a video of about `minutes`, +/-12%."""
    target = minutes * WORDS_PER_MINUTE
    return round(target * 0.88), round(target * 1.12)


def write_script(topic: str, model: str, minutes: float = 5, angle: str | None = None) -> Script:
    """Ask the model for a structured script. `model` is a LangChain id like google_genai:gemini-3.7-flash."""
    from langchain.chat_models import init_chat_model

    lo, hi = word_range(minutes)
    prompt = f"Topic: {topic}"
    if angle:
        prompt += f"\nAngle: {angle}"
    system = SYSTEM_PROMPT.format(minutes=f"{minutes:g}", min_words=lo, max_words=hi)
    writer = init_chat_model(model).with_structured_output(Script)
    script = writer.invoke([{"role": "system", "content": system}, {"role": "user", "content": prompt}])
    if script is None:
        raise RuntimeError(f"No script returned for {topic!r}")
    return script


def load_script(path: Path) -> Script:
    return Script.model_validate(json.loads(Path(path).read_text()))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "video"
