---
name: yt-seo
description: >-
  Write the description, tags and search-facing text for a YouTube video,
  aimed at the query a real person types. Use for "write my description",
  "tags", "SEO", "help this video get found", "nobody is finding this".
---

# yt-seo

Search is a smaller lever than packaging and a bigger one than people think for evergreen videos.
For a video aimed at the subscriber feed, say so and spend the effort on the `yt-package` skill instead.

## Before you write

1. Read `/voice.md`. That is the creator's voice profile: how they talk, the words they never
   use, who they are talking to, what they will not claim. If it is still the blank template,
   work from `/AGENTS.md` and say in your reply that the voice profile needs filling in.
2. Never invent a number, a result or a source. If a figure would strengthen it and you do not have
   one, ask for it or write the line without it.

## The description

- **The first two lines are the only ones anyone reads.** They show above "...more" and they are
  the search snippet. Say what the video gives them, in the words they would have typed.
- Then the link or the resource, if there is one, so it is above the fold.
- Then chapters (the `yt-chapters` skill writes them).
- Then the long version: what is covered, who it is for, what it assumes.

## Tags, honestly

Tags are a weak signal and YouTube has said so. Use them for disambiguation - spellings, the tool
names, the abbreviations people actually type - and stop. Fifteen is plenty. A wall of tags is not
a strategy and stuffing unrelated ones is against the terms.

## The query test

Before handing anything over, write the three search queries this video should win, and check the
title and first two description lines contain the words in those queries. If they do not, the
problem is the title, not the description.

## The gate

Nothing here publishes. Write your output to the studio path you were given and reply with a
short summary the producer can act on. If you need something only the person has (a number, an
export, a transcript), say exactly what is missing instead of guessing. Rendering a video always
waits for the person's approval.

---
Adapted from [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT).
