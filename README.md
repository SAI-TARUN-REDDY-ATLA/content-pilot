# content-pilot

An AI-run cartoon history channel on YouTube. Every other day it picks a true story from history,
researches it, writes it as a funny, story-driven script, draws one cartoon per scene, narrates
it, renders a ~5 minute 16:9 video with chapters and a thumbnail, uploads it and archives
everything.

## How a video is made

1. **Script**: Gemini (`gemini-3.7-flash` by default) writes the story as chapters of scenes:
   each scene is a few narrated sentences plus a description of the cartoon frame shown during
   them, with recurring characters given a fixed look. The length follows `CONTENT_PILOT_MINUTES`
   (default 5; about 170 spoken words a minute).
2. **Art**: a Gemini image model (`gemini-2.5-flash-image` by default) draws every scene, and the
   thumbnail, in one flat cartoon style (`CONTENT_PILOT_ART_STYLE`). Image models have no free
   tier: the key's Google Cloud project needs billing. Roughly 45-50 images per 5-minute video.
3. **Voice**: free Microsoft Edge neural TTS (`en-US-AndrewNeural`) reads it and reports each
   word's timing, which sets when every scene cuts.
4. **Subtitles**: phrase by phrase at the bottom, key words in yellow. Drawn with Pillow, so any
   ffmpeg build works.
5. **Render**: every scene becomes a clip with a slow zoom or pan; ffmpeg joins them, overlays
   the subtitles and mixes the voice with optional background music from `assets/music/`.
6. **Package**: YouTube chapters from the scene timings, and a 1280x720 thumbnail with the
   thumbnail words stamped on it.

## Quick start

Requires Python 3.10+ and `ffmpeg` on your PATH.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[agent,youtube]'
cp .env.example .env        # then put your Gemini key in GOOGLE_API_KEY
```

Get a Gemini key at [Google AI Studio](https://aistudio.google.com/apikey) and enable billing on
its project (needed for the image model). `.env` is git-ignored and loaded automatically; real
environment variables take priority over it.

```bash
content-pilot               # agents pick a story themselves, research, write and render it
content-pilot --upload      # same, then upload to YouTube
```

With no arguments nothing asks you for a topic: the trend-scout finds what is working in
animated history, the team researches and writes it, and the video is saved to
`library/<date>_<slug>/video.mp4` with everything that made it.

Other modes:

```bash
content-pilot --topic "the dancing plague of 1518"                      # one model call, no agents
content-pilot --script examples/scripts/emu_war.json --placeholder-art  # free preview, no API key
```

These two write to `output/<slug>.mp4`. `--placeholder-art` draws plain cards with each scene's
description instead of generating images, for checking timing and pacing for free. Other options:
`--minutes 8`, `--voice en-US-GuyNeural`, `--music path/to/tracks`, `--seed 7`,
`--model google_genai:gemini-3.1-pro-preview`.

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
| scriptwriter | five hooks scored, script (chapters, scenes, image descriptions) written and validated | history-script, yt-script | score_hooks, check_script |
| critic | independent retention and fact review | history-script, yt-script | score_hooks |
| packager | title + thumbnail pairing, description, hashtags | yt-package, yt-seo | lint_title, check_script |
| repurposer | Short-worthy moments, chapters and edit lists from a long video | yt-shorts, yt-chapters, yt-edit, writing | score_hooks, check_script, make_chapters, find_dead_air |
| analyst | retention exports and channel audits, one fix | yt-retention, yt-audit | read_retention, lint_title, score_hooks, list_videos |
| community | comment triage and replies | yt-comment | - |

```bash
content-pilot-agent             # picks its own topic, asks you before rendering
content-pilot-agent "a video about the Pig War of 1859"
content-pilot-agent "find three Short-worthy moments and chapters in /inputs/episode-12.srt"
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

## Scheduled automation

Every other day at 12:00 am IST a GitHub Actions workflow
([daily-short.yml](.github/workflows/daily-short.yml), *Publish Video*) runs `content-pilot-daily`:

1. **Learn**: pulls views and % watched for the last 60 days of uploads from YouTube Analytics
   into `library/<video>/stats.json`. The team reads them through `list_videos` and writes what
   it learns into `studio/AGENTS.md`.
2. **Make**: the producer's team runs unattended: trend-scout picks a topic, then research,
   five scored hooks, script, critique, packaging. No approval step; nobody is watching.
3. **Check**: code, not the model, requires `check_script` to pass (two repair rounds).
4. **Render and upload**: generates the art, renders the video and uploads it to YouTube as public,
   with chapters in the description and the thumbnail. A video with placeholder art is never
   uploaded.
5. **Archive**: everything lands in `library/<date>_<slug>/` and is committed back to `main`;
   the MP4 goes to a GitHub release `video-<date>_<slug>` and a 90-day workflow artifact.

```
library/
  index.jsonl                       one line per video: date, topic, title, status, YouTube URL
  2026-10-15_great-emu-war/
    metadata.json                   topic, title, hook + score, YouTube id/URL, release, run link
    script.json  research.md  package.md  captions.json  scenes.json  thumbnail.jpg  stats.json
    video.mp4  voice.mp3            git-ignored; kept in the release
```

Run the same thing locally: `content-pilot` (add `--upload` to publish).

Every run, pass or fail, also writes `status/last-run.json` and appends to `status/runs.jsonl`
(step outcomes and which secrets are set, never their values). A Claude cloud routine reads them
every morning at 08:00 IST and follows [MAINTAINER.md](MAINTAINER.md): it reports how last night
went and how recent videos are doing, and opens a `maintain/...` pull request when something in
the code needs fixing.

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
   `MUSIC_URL`, a direct link to a .zip of royalty-free tracks (or commit them to `assets/music/`).
   Optional variables: `CONTENT_PILOT_MINUTES` (raise it to make longer videos),
   `CONTENT_PILOT_MODEL`, `CONTENT_PILOT_IMAGE_MODEL`, `CONTENT_PILOT_PRIVACY`.
   Custom thumbnails need a phone-verified YouTube channel; until then the upload works and the
   thumbnail step is skipped.
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
    images.py         Gemini cartoon art per scene and the thumbnail
    captions.py       phrase subtitle frames
    media.py          probing and background music
    render.py         zoom/pan clip per scene, joined with subtitles, voice and music
    run.py            make_video(): runs the stages in order
  daily.py            content-pilot-daily: the scheduled learn, make, upload, archive job
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
assets/music/         royalty-free background tracks (optional)
examples/scripts/     ready-made scripts to render without an API key
tests/                mirrors src: tests/pipeline, tests/agent, plus fixtures/
output/               rendered videos (git-ignored)
```

## Roadmap

- [x] Stage 1: one video end to end from a topic
- [x] Stage 2: trend sourcing by the trend-scout agent, ranked by outlier multiple
- [ ] Stage 3: retention tuning in the render (sound effects, character animation); the
      script side and the Analytics feedback loop are done
- [x] Stage 4: scheduled YouTube upload with an archived library
- [x] Stage 5: long-form cartoon history (16:9, ~5 minutes, generated scene art, chapters, thumbnail)
- [ ] Stage 6: longer videos (raise `CONTENT_PILOT_MINUTES`) and Shorts cut from each video

## Tests

```bash
python -m unittest discover -s tests -t . -v
```
