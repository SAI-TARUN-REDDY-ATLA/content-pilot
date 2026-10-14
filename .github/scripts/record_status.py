"""Write the outcome of a Daily Short run to status/, so the monitor can read it from the repo.

The repo is public: this records only structured outcomes, never log text or secret values.
Failure details for runs that got as far as the library live in library/<entry>/metadata.json.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

now = datetime.now(timezone.utc)
status = {
    "finished_utc": now.isoformat(timespec="seconds"),
    "date_ist": (now + timedelta(hours=5, minutes=30)).date().isoformat(),
    "event": os.getenv("GITHUB_EVENT_NAME"),
    "run_url": f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}",
    "job_status": os.getenv("JOB_STATUS"),
    "steps": {name: os.getenv(f"OUTCOME_{name.upper()}") or "not reached"
              for name in ("install", "footage", "daily", "release")},
    "entry": os.getenv("ENTRY") or None,
    "secrets_set": {name: os.getenv(f"HAS_{name}") == "true"
                    for name in ("GOOGLE_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
                                 "YOUTUBE_REFRESH_TOKEN", "FOOTAGE_URL")},
}
out = Path("status")
out.mkdir(exist_ok=True)
(out / "last-run.json").write_text(json.dumps(status, indent=2) + "\n")
with open(out / "runs.jsonl", "a") as f:
    f.write(json.dumps(status) + "\n")
print(json.dumps(status, indent=2))
