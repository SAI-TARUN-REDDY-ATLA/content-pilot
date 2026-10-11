# content-pilot

AI guided YouTube Shorts generator: give it a topic and it produces a 30-45 second,
9:16 "brain rot" style video with a hard-hitting hook, a fast neural voiceover and
word-by-word pop captions over looping background footage.

## How a video is made

1. **Script**: Claude (`claude-opus-5-5`) writes a hook, short escalating lines and a
   loop line that flows back into the hook, with key words marked for highlighting.
2. **Voice**: free Microsoft Edge neural TTS reads it and reports each word's timing.
3. **Captions**: one word at a time, upper-case, thick outline, a short "pop" on entry,
   highlighted words in yellow. Drawn with Pillow, so any ffmpeg build works.
4. **Render**: ffmpeg crops a random background clip to 1080x1920, loops it, overlays
   captions and mixes the voice into an H.264/AAC MP4.

## Quick start

Requires Python 3.10+ and `ffmpeg` on your PATH.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# No API key needed: render the bundled example script
python -m content_pilot --script examples/emu_war.json

# Claude writes the script (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=...
python -m content_pilot --topic "The Great Emu War of 1932"
```

Output goes to `output/<slug>.mp4`, with `<slug>.json` holding the title, description
and hashtags, and `output/work_<slug>/` holding the script, voice and caption timings.

Options: `--voice en-US-AndrewNeural`, `--footage path/to/clips`, `--seed 7`,
`--out folder`. Put your own background clips in `assets/footage/` (see its README).

## Roadmap

- [x] Stage 1: one video end to end from a topic
- [ ] Stage 2: trend sourcing (Google Trends, Reddit hot, YouTube trending) ranked by Claude
- [ ] Stage 3: retention tuning (hook variants, pacing, progress bar, sound effects)
- [ ] Stage 4: YouTube upload

## Tests

```bash
python -m unittest discover -s tests -v
```
