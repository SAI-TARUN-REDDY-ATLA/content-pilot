# youtube_kit

The six stdlib-only analysis scripts from
[Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill)
(commit a2feb21, MIT, see LICENSE), vendored unchanged. The folder layout is kept because the
scripts find each other by relative path (`chapters.py` imports `yt-edit/deadair.py`, `swipe.py`
reads `yt-script/hooks.json`).

The producer agent calls them through the wrappers in `../youtube_tools.py`. They live here, in
the package, rather than in `studio/` so agents can't rewrite their own scoring tools.
The matching SKILL.md files, adapted to the harness, are in `studio/skills/`.
