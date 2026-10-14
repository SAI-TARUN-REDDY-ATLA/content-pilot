# Maintainer runbook

A Claude cloud routine follows this every morning at 08:00 IST. The *Publish Video* workflow
makes and uploads a ~5 minute cartoon history video every other day at 00:00 IST (odd days of
the month). Edit this file to change what it does.

## Inputs

- `status/last-run.json`, `status/runs.jsonl`: one record per publish run, written by the
  workflow: job status, outcome of each step, which secrets are set (true/false), library entry.
- `library/index.jsonl`, `library/<entry>/metadata.json`: every video, its status and, when it
  failed, the error. `library/<entry>/stats.json`: views and % watched from YouTube Analytics.
- `studio/AGENTS.md`: channel memory; `## Lessons learned` is where evidence-backed lessons go.

## 1. Did the last scheduled run happen?

Runs are expected on odd days of the month (the 1st, 3rd, ... 31st). On an even day with no new
run, that is normal: report the last run instead and say no run was scheduled.

Today's date in IST is `TZ=Asia/Kolkata date +%F`. Look for a record in `status/runs.jsonl`
with that `date_ist` (a run finishing just before midnight UTC can carry yesterday's date;
treat a record from the last 12 hours as last night's run).

- **No record on a run day**: the job never started or could not commit. Likely causes, in
  order: GitHub Actions billing or spending limit, the workflow disabled (GitHub turns off schedules after 60
  days without repo activity), the workflow file broken. Report it as **DOWN**. Check
  `.github/workflows/daily-short.yml` for a syntax problem and fix it if there is one.
- **`job_status: success`** and the entry's `metadata.json` says `uploaded`: **OK**. Note the
  YouTube URL and privacy. If privacy is `private`, remind that the API audit is still pending.
- **Failure**: find the first step whose outcome is `failure`.
  - Any `secrets_set` value is false → **NEEDS YOU**: list exactly which secret to add in repo
    Settings > Secrets and variables > Actions. Don't change code for this.
  - `install` failed → a dependency broke. Reproduce with `pip install -e '.[agent,youtube]'`,
    pin or fix in `pyproject.toml`.
  - `daily` failed → read `error` in that entry's `metadata.json` (if there is no entry, the
    failure came before archiving: producer, model or credentials). Classify:
    - credential/auth (`invalid_grant`, 401/403, API key invalid, quota) → **NEEDS YOU**, explain
      the fix (e.g. re-run `content-pilot-auth`, consent screen must be *In production*).
    - "Gemini image quota exhausted" or "placeholder art" → **NEEDS YOU**: image generation needs
      billing enabled on the GOOGLE_API_KEY project, or the daily image quota ran out.
    - Edge TTS failures (403, timeouts) → usually Microsoft rotated the endpoint: try upgrading
      `edge-tts` in `pyproject.toml`; that is a code fix.
    - model/API outage or rate limit → transient; report, no change.
    - a bug in our code → **FIXED (PR)**: fix it as below.

## 2. How did the videos do?

From the `stats.json` files of the last 30 days, report a small table: date, title, views,
% watched, average view duration. Name the best and the worst and one concrete reason grounded
in the scripts (cold open, story choice, length, thumbnail text). Only when the evidence is
clear (at least 4 videos with stats), add **one** line to `## Lessons learned` in `studio/AGENTS.md`: what worked or failed, with the
video dates and numbers. Never invent numbers.

## 3. Housekeeping (Mondays only)

Run `python -m unittest discover -s tests -t .`. Look for deprecation warnings or failing
tests and fix them. Check that `.github/workflows/daily-short.yml` actions are not deprecated.

## Making changes

- Never push to `main`. Work on a branch `maintain/<YYYY-MM-DD>-<short-slug>`, run the tests,
  push it and open a pull request (`gh pr create`) describing the evidence and the fix. If `gh`
  is unavailable, push the branch and give the compare URL.
- At most one PR per day. First check `gh pr list --search "head:maintain/"`: if a maintenance
  PR is already open, add to that branch instead of opening another.
- Never touch secrets, billing, repo settings or YouTube videos; never upload, delete or
  re-run anything; never delete library entries; never commit log output or credentials (the
  repo is public).

## Report

End with this, short enough to read on a phone:

```
content-pilot · <date>
Last run: OK | FAILED | DOWN | NEEDS YOU | NO RUN DUE — <one line>
Video: <title> — <YouTube URL> (<privacy>)
Last 30 days: <n> videos, best <title> (<% watched>), worst <title> (<% watched>)
Action for you: <exact steps, or "none">
PR: <url or "none">
```
