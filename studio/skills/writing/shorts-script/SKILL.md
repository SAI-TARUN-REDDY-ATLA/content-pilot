---
name: shorts-script
description: How to write a content-pilot Shorts script JSON (hook, lines, loop line, emphasis markers) that passes check_script and renders cleanly. Use before writing or revising any file in /scripts/.
---

# Writing a Shorts script

## File format
Write one JSON object to `/scripts/<slug>.json`:

```json
{
  "title": "Under 70 chars, a curiosity gap",
  "hook": "First spoken sentence, the scroll-stopper.",
  "lines": ["Body sentence one.", "Body sentence two."],
  "loop_line": "Last sentence, flows straight back into the hook.",
  "description": "One or two sentence YouTube description.",
  "hashtags": ["history", "shorts", "weirdhistory"]
}
```

See `example.json` in this folder for a complete script that rendered well.

## Retention rules
- The hook opens a loop in under two seconds: a shocking claim, a direct "you", or a question.
  Never open with a greeting, the channel, or "Did you know".
- Every sentence is under 14 words and adds a new fact, twist or escalation.
- A pattern interrupt roughly every 8 seconds ("But here's the crazy part.", "Wait.", a sudden number).
- Hold the hook's payoff until near the end.
- The loop line flows back into the hook so a replay feels seamless.
- Plain spoken English: no emojis, hashtags, stage directions or markdown in spoken text.
- Wrap 1-3 punchy words per sentence in `*asterisks*`; they are highlighted yellow in captions.
- Narration (hook + lines + loop line) totals 85-115 words.
- Hashtags: 3-6, no `#` symbol.

## Steps
1. Read the research notes and pick the single strongest payoff.
2. Write the hook toward that payoff, then the body in escalating order.
3. Write the loop line last, reading it into the hook out loud in your head.
4. Run `check_script` and fix everything it lists.
