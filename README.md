# content-pilot

AI guided YouTube Shorts channel: every night it picks a personality-development topic,
writes and renders a 30-45 second 9:16 Short, uploads it and archives everything. Each video has a hard-hitting hook, a fast neural
voiceover and word-by-word pop captions over looping background footage.

## How a video is made

1. **Script**: Gemini (`gemini-3.7-flash` by default) writes a hook, short escalating lines and a
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
pip install -e '.[agent,youtube]'
cp .env.example .env        # then put your Gemini key in GOOGLE_API_KEY
```

Get a Gemini key at [Google AI Studio](https://aistudio.google.com/apikey). `.env` is
git-ignored and loaded automatically; real environment variables take priority over it.

```bash
content-pilot               # agents research a topic themselves, write it, render it
content-pilot --upload      # same, then upload to YouTube
```

With no arguments nothing asks you for a topic: the trend-scout finds what is working in the
niche, the team researches and writes it, and the video is saved to
`library/<date>_<slug>/video.mp4` with everything that made it.

Other modes:

```bash
content-pilot --topic "the spotlight effect"            # one model call, no agents
content-pilot --script examples/scripts/emu_war.json    # render a script, no API key
```

These two write to `output/<slug>.mp4`. Options for all modes: `--voice en-US-AndrewNeural`,
`--footage path/to/clips`, `--seed 7`, `--model google_genai:gemini-3.1-pro-preview`.
Put your own background clips in `assets/footage/` (see its README).

## Producer agent

A [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) harness: a producer
that runs a team of specialists and owns the result. Each specialist gets only the tools and
skills its job needs. The YouTube skills and analysis scripts come from
[youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT).

| Agent | Does | Skills | Tools |
| --- | --- | --- | --- |
| producer | plans, briefs the team, renders | yt-plan | check_script, render_video, list_videos |
| trend-scout | what is working in the niche, by outlier multiple | yt-viral | google_search, rank_outliers |
| researcher | sourced facts on a topic | - | google_search |
| scriptwriter | five hooks scored, script written and validated | shorts-script, yt-script | score_hooks, check_script |
| critic | independent retention review | shorts-script, yt-script | score_hooks |
| packager | title + thumbnail pairing, description, hashtags | yt-package, yt-seo | lint_title, check_script |
| repurposer | Shorts, chapters and edit lists from a long video | yt-shorts, yt-chapters, yt-edit, writing | score_hooks, check_script, make_chapters, find_dead_air |
| analyst | retention exports and channel audits, one fix | yt-retention, yt-audit | read_retention, lint_title, score_hooks, list_videos |
| community | comment triage and replies | yt-comment | - |

```bash
content-pilot-agent             # picks its own topic, asks you before rendering
content-pilot-agent "a short about the spotlight effect"
content-pilot-agent "cut three shorts and chapters from /inputs/episode-12.srt"
content-pilot-agent "why is retention bad on this one? /inputs/retention.csv"
```

Rendering pauses for your approval: approve, reject with feedback (the producer routes the fix
to the right specialist), or edit the arguments (voice, seed). Nothing is ever published.

Everything happens inside `studio/`:

- `AGENTS.md` channel memory and `voice.md` your voice profile, loaded on every run. Fill in
  `voice.md`; every writing agent reads it.
- `skills/<group>/` skills, grouped by which agents load them (see `agent/team.py`)
- `inputs/` put transcripts, retention CSVs, comments and channel data here
- `research/`, `scripts/`, `packages/`, `reports/`, `plans/` what the team writes

## Daily automation

Every night at 12:00 am IST a GitHub Actions workflow
([daily-short.yml](.github/workflows/daily-short.yml)) runs `content-pilot-daily`:

1. **Learn**: pulls views and % watched for the last 60 days of uploads from YouTube Analytics
   into `library/<video>/stats.json`. The team reads them through `list_videos` and writes what
   it learns into `studio/AGENTS.md`.
2. **Make**: the producer's team runs unattended: trend-scout picks a topic, then research,
   five scored hooks, script, critique, packaging. No approval step; nobody is watching.
3. **Check**: code, not the model, requires `check_script` to pass (two repair rounds).
4. **Render and upload**: renders the Short and uploads it to YouTube as public.
5. **Archive**: everything lands in `library/<date>_<slug>/` and is committed back to `main`;
   the MP4 goes to a GitHub release `video-<date>_<slug>` and a 90-day workflow artifact.

```
library/
  index.jsonl                       one line per video: date, topic, title, status, YouTube URL
  2026-10-12_why-you-freeze/
    metadata.json                   topic, title, hook + score, YouTube id/URL, release, run link
    script.json  research.md  package.md  captions.json  stats.json
    video.mp4  voice.mp3            git-ignored; kept in the release
```

Run the same thing locally: `content-pilot` (add `--upload` to publish).

### One-time setup

1. **Google Cloud**: create a project, enable *YouTube Data API v3* and *YouTube Analytics
   API*, create an OAuth client of type *Desktop app*, and download its `client_secret.json`.
   On the OAuth consent screen add yourself as a user and set the status to **In production**.
   In *Testing*, Google expires the refresh token after 7 days and uploads start failing.
2. **Sign in once** on your machine:
   ```bash
   pip install -e '.[agent,youtube]'
   content-pilot-auth path/to/client_secret.json
   ```
3. **GitHub secrets** (Settings > Secrets and variables > Actions): `GOOGLE_API_KEY`,
   `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`, and optionally
   `FOOTAGE_URL`, a direct link to a .zip of background clips. Without it videos render over a
   placeholder gradient. Optional variables: `CONTENT_PILOT_MODEL`, `CONTENT_PILOT_PRIVACY`.
4. **Merge to `main`**: GitHub only runs schedules from the default branch. Then try it from the
   Actions tab with *Run workflow* and *Upload* unticked.

**Public uploads need YouTube's API audit.** Videos uploaded through the API by a project that
hasn't passed the [YouTube API compliance audit](https://support.google.com/youtube/contact/yt_api_form)
are locked to private. Until it passes, uploads succeed but stay private, and the run log says so.

## Project layout

```
src/content_pilot/
  cli.py              content-pilot command
  config.py           settings and project paths (env overrides)
  pipeline/           one module per stage of making a video
    script.py         the model writes the script (Script model)
    voice.py          Edge TTS voiceover with word timings
    captions.py       word-by-word caption frames
    footage.py        background clip selection
    render.py         ffmpeg composition
    run.py            make_video(): runs the stages in order
  daily.py            content-pilot-daily: the nightly learn, make, upload, archive job
  library.py          the video archive (library/)
  youtube/            OAuth (content-pilot-auth), upload, analytics
  agent/              Deep Agents producer and team (content-pilot-agent)
    harness.py        build_agent(): the producer
    team.py           the specialists: tools and skill groups per agent
    prompts.py        system prompts for every agent
    tools.py          check_script, render_video, list_videos
    youtube_tools.py  score_hooks, lint_title, find_dead_air, make_chapters, ...
    youtube_kit/      vendored youtube-agent-skill scripts (MIT)
    cli.py            interactive chat with approval prompts
studio/               the agents' workspace: memory, voice, skills, inputs and drafts
library/              every published video and everything that made it
assets/footage/       your background clips (git-ignored)
examples/scripts/     ready-made scripts to render without an API key
tests/                mirrors src: tests/pipeline, tests/agent, plus fixtures/
output/               rendered videos (git-ignored)
```

## Roadmap

- [x] Stage 1: one video end to end from a topic
- [x] Stage 2: trend sourcing by the trend-scout agent, ranked by outlier multiple
- [ ] Stage 3: retention tuning in the render (progress bar, pacing, sound effects); the
      script side and the Analytics feedback loop are done
- [x] Stage 4: nightly YouTube upload with an archived library

## Tests

```bash
python -m unittest discover -s tests -t . -v
```
