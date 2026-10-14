---
name: history-script
description: How to write a content-pilot cartoon history script JSON (characters, chapters of scenes, each with narration and a cartoon image description) that passes check_script and renders cleanly. Use before writing or revising any file in /scripts/.
---

# Writing a cartoon history script

The channel tells real history as a story, read by a witty narrator over flat cartoon
illustrations: one generated image per scene, with a slow zoom or pan, subtitles underneath.
Videos are about 5 minutes (check_script prints the exact word range for the current length).

## File format
Write one JSON object to `/scripts/<slug>.json`:

```json
{
  "title": "Under 70 chars, a curiosity gap",
  "characters": [
    {"name": "Meredith", "look": "stocky officer, khaki 1930s uniform, round glasses, binoculars"}
  ],
  "chapters": [
    {"title": "Cold Open", "scenes": [
      {"narration": "In 1932, the Australian army declared war on a bird. And the bird *won*.",
       "image": "Meredith beside a machine gun in a wheat field while an emu eats his hat"}
    ]}
  ],
  "description": "Two or three sentences for YouTube.",
  "hashtags": ["history", "animatedhistory", "funnyhistory"],
  "thumbnail_text": "THE BIRDS WON",
  "thumbnail_image": "One focal point, big emotion, simple background"
}
```

`example.json` in this folder is a complete script (the Great Emu War) that passes check_script.

## Story
- **Cold open (first chapter, 2-4 scenes):** the first sentence is the hook, the most absurd or
  dramatic true thing in the story, in under three seconds. No greeting, no "Did you know", no
  "In this video". Then promise what the viewer is about to see.
- **4-8 chapters** in story order: setup (why anyone cared), escalation, the turn, the aftermath.
  Each chapter opens with a re-hook ("So Meredith got creative.", "But the emus kept eating.").
- **People, not dates.** Give real people motives and reactions. A running gag is gold.
- **Payoff then tease.** End on the answer the hook promised, then one line teasing another
  story. Never "like and subscribe".

## Narration
- Spoken English, sentences under 25 words, scenes 8-45 words (a scene is one image on screen
  for roughly 3-15 seconds).
- Wrap 1-3 punchy words per scene in `*asterisks*`; they are highlighted yellow in subtitles.
- Write numbers the way they should be spoken when it matters ("nine hundred and eighty-six").
- No emojis, hashtags, stage directions or markdown in narration.

## Facts
Use only facts in the research notes. Never invent quotes, numbers or events. When sources
disagree, say "reportedly" or "around". Quotes are paraphrased unless the research has the exact
wording with a source.

## Images
- One frame per scene: who (character names exactly as in `characters`), doing what, where, the
  period details, and the visual joke.
- Every recurring person and the recurring animal/group gets a `characters` entry with a fixed
  look; any scene whose `image` mentions that name is drawn with that design.
- Never ask for written words, signs, labels, captions or speech bubbles: image models garble text.
- Vary the shots: wide landscape, close-up face, crowd, object detail.
- Keep it non-graphic: violence is implied or slapstick, never gore.

## Steps
1. Read the research notes; find the hook and the payoff.
2. Outline the chapters, then write the cold open and the ending first.
3. Fill the scenes, then write `characters`, `thumbnail_text` and `thumbnail_image`.
4. Run `check_script` and fix everything it lists.
