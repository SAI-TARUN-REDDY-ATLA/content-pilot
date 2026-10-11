---
name: yt-edit
description: >-
  Turn a raw recording's transcript into an edit decision list - dead air,
  filler cues and retakes, with timecodes. Use for "edit this", "cut the
  dead space", "tighten this video", "I rambled", or any request to shorten
  footage from a transcript.
---

# yt-edit

An edit decision list from a timestamped transcript. It prints the cuts. You apply them.

Build the decision list with `find_dead_air(transcript_path, floor=0.45)`. Transcripts
(.srt, .vtt or whisper .json) live in `/inputs/`.

No transcript yet? Ask for one, or produce one first - `whisper`, `faster-whisper`, or the caption
track YouTube generates on an unlisted upload all work. Do not guess at timings.

## What it finds

- **DEAD** - gaps longer than the floor, trimmed from the MIDDLE so both sides keep a breath.
  Cutting flush against speech is what makes a tightened take sound gasping.
- **FILLER** - cues that are nothing but "um", "so yeah", "basically".
- **REPEAT** - a sentence restarted. Compared against the last cue that was actually speech, not
  the literal previous cue, because most retakes have an "um" between the two attempts.

## What it will not do

It does not touch media. It has no opinion about your B-roll. A 40% cut on the report is a 40% cut
of SPEECH, and if the video has a long silent demo in it that number is wrong - check the report
against the footage before you trust the runtime at the bottom.

## The gate

Nothing here publishes. Write your output to the studio path you were given and reply with a
short summary the producer can act on. If you need something only the person has (a number, an
export, a transcript), say exactly what is missing instead of guessing. Rendering a video always
waits for the person's approval.

---
Adapted from [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT).
