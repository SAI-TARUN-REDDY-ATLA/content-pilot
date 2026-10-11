---
name: yt-chapters
description: >-
  Write YouTube chapters from a transcript, validated against YouTube's own
  rules so they actually render. Use for "add chapters", "timestamps",
  "break this video into sections".
---

# yt-chapters

Draft chapters with `make_chapters(transcript_path, target=8)`. Transcripts live in `/inputs/`.

## The rules, which are not optional

A chapter list that breaks any of these silently does not become chapters at all - the block just
sits in the description doing nothing:

- The first entry must be **00:00**.
- There must be **at least three**.
- Each must be **at least 10 seconds** long.

The tool checks all three and tells you when a list is invalid rather than letting you paste it.

## Retitle every line

`make_chapters` finds the BOUNDARIES well - it scores the pauses you actually took by how much the
vocabulary shifts across them. The titles it emits are the topic words, and they are a draft. A
chapter called "Thumbnails Titles Packaging" is a placeholder. Rewrite each one as the promise of
that section, in the user's voice, three to five words.

Chapters are also a retention diagnostic: if a section cannot be named in five words, it is two
sections or it is filler.

## The gate

Nothing here publishes. Write your output to the studio path you were given and reply with a
short summary the producer can act on. If you need something only the person has (a number, an
export, a transcript), say exactly what is missing instead of guessing. Rendering a video always
waits for the person's approval.

---
Adapted from [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT).
