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
pip install -e .            # pipeline only
pip install -e '.[agent]'   # plus the producer agent

# No API key needed: render the bundled example script
content-pilot --script examples/scripts/emu_war.json

# Claude writes the script (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=...
content-pilot --topic "The Great Emu War of 1932"
```

Output goes to `output/<slug>.mp4`, with `<slug>.json` holding the title, description
and hashtags, and `output/work_<slug>/` holding the script, voice and caption timings.

Options: `--voice en-US-AndrewNeural`, `--footage path/to/clips`, `--seed 7`,
`--out folder`. Put your own background clips in `assets/footage/` (see its README).

## Producer agent

A [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) harness that runs
the whole job from a loose idea: it plans, sends a `researcher` subagent to find sourced facts
on the web, writes the script with the `shorts-script` skill, checks it, has a `critic` subagent
punch up the hook and loop, then renders once you approve.

```bash
export ANTHROPIC_API_KEY=...
content-pilot-agent "a short about the dancing plague of 1518"
```

Rendering pauses for your approval: approve, reject with feedback (the producer revises),
or edit the arguments (voice, seed). The agent works inside `studio/`:
`studio/AGENTS.md` is the channel memory loaded on every run, `studio/skills/` holds skills,
and research notes and scripts land in `studio/research/` and `studio/scripts/`.
The code is in `src/content_pilot/agent/` (`harness.py` builds the agent, `prompts.py` holds
the producer and subagent prompts, `tools.py` holds `check_script`, `render_video` and `list_videos`).

## Project layout

```
src/content_pilot/
  cli.py              content-pilot command
  config.py           settings and project paths (env overrides)
  pipeline/           one module per stage of making a video
    script.py         Claude writes the script (Script model)
    voice.py          Edge TTS voiceover with word timings
    captions.py       word-by-word caption frames
    footage.py        background clip selection
    render.py         ffmpeg composition
    run.py            make_video(): runs the stages in order
  agent/              Deep Agents producer (content-pilot-agent)
    harness.py        build_agent()
    prompts.py        producer, researcher and critic prompts
    tools.py          check_script, render_video, list_videos
    cli.py            interactive chat with approval prompts
studio/               the agent's workspace: AGENTS.md memory, skills/, research/, scripts/
assets/footage/       your background clips (git-ignored)
examples/scripts/     ready-made scripts to render without an API key
tests/                mirrors src: tests/pipeline, tests/agent
output/               rendered videos (git-ignored)
```

## Roadmap

- [x] Stage 1: one video end to end from a topic
- [ ] Stage 2: trend sourcing (Google Trends, Reddit hot, YouTube trending) ranked by Claude
- [ ] Stage 3: retention tuning (hook variants, pacing, progress bar, sound effects)
- [ ] Stage 4: YouTube upload

## Tests

```bash
python -m unittest discover -s tests -t . -v
```
