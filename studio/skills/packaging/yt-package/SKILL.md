---
name: yt-package
description: >-
  Write and lint the title and thumbnail for a YouTube video as one pairing,
  checking truncation, duplication and vagueness before publish. Use for
  "title ideas", "what should I call this", "thumbnail text", "my CTR is
  bad", packaging, or any request to rename or repackage an existing video.
---

# yt-package

The title and the thumbnail are ONE unit. Writing them separately is why most packaging fails: the
thumbnail repeats the title, and half the click surface says the same thing twice.

Lint pairings with the `lint_title` tool: `lint_title(titles=[...], thumbnail="AI RAN IT")`.

## Before you write

1. Read `/voice.md`. That is the creator's voice profile: how they talk, the words they never
   use, who they are talking to, what they will not claim. If it is still the blank template,
   work from `/AGENTS.md` and say in your reply that the voice profile needs filling in.
2. Never invent a number, a result or a source. If a figure would strengthen it and you do not have
   one, ask for it or write the line without it.

## Rules the tool enforces, and why

- **60 characters** is where desktop search truncates, **40** is a mobile home feed. Both are
  reported because they fail differently: a desktop cut loses the tail, a mobile cut can lose the
  subject.
- **The thumbnail must not repeat the title.** Different words, same promise.
- **Three words maximum on the thumbnail.** At feed size a fourth word is a grey smear.
- **A number, a name or a date** beats every adjective available to you.
- **Two all-caps words is the ceiling** before a title reads as spam.

## Write ten, keep two

Generate ten titles, run them all through `lint_title`, show the user the top three with their scores
and the specific issue on each. For the winner, write the thumbnail brief: the expression, the
framing, the three words, and what the background has to do to hold contrast at feed size.

## The gate

Nothing here publishes. Write your output to the studio path you were given and reply with a
short summary the producer can act on. If you need something only the person has (a number, an
export, a transcript), say exactly what is missing instead of guessing. Rendering a video always
waits for the person's approval.

---
Adapted from [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT).
