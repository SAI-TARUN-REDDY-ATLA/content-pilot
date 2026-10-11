"""The video library: one folder per video holding everything that made it, plus an index.

    library/
      index.jsonl                      one line per video, newest last
      2026-10-12_why-you-procrastinate/
        script.json  research.md  package.md  captions.json  metadata.json  stats.json
        video.mp4  voice.mp3           large files: git-ignored, kept in the GitHub release

metadata.json is the record of the run: topic, title, YouTube id and URL, release URL, timings,
check results. stats.json is refreshed from YouTube Analytics on later runs.
"""

import json
import shutil
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from .config import LIBRARY_DIR


@dataclass
class Entry:
    path: Path

    @property
    def id(self) -> str:
        return self.path.name

    @property
    def metadata(self) -> dict:
        f = self.path / "metadata.json"
        return json.loads(f.read_text()) if f.exists() else {}

    @property
    def stats(self) -> dict:
        f = self.path / "stats.json"
        return json.loads(f.read_text()) if f.exists() else {}

    def update(self, **fields) -> dict:
        meta = {**self.metadata, **fields}
        (self.path / "metadata.json").write_text(json.dumps(meta, indent=2, default=str))
        return meta

    def save_stats(self, stats: dict) -> None:
        stats = {**stats, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (self.path / "stats.json").write_text(json.dumps(stats, indent=2))

    def add(self, src: Path, name: str | None = None) -> Path | None:
        """Copy an artifact into the entry; quietly skip ones the run didn't produce."""
        if not src or not Path(src).exists():
            return None
        dest = self.path / (name or Path(src).name)
        shutil.copy2(src, dest)
        return dest


class Library:
    def __init__(self, root: Path = LIBRARY_DIR):
        self.root = root
        self.index = root / "index.jsonl"

    def create(self, slug: str, day: date | None = None) -> Entry:
        day = day or date.today()
        path = self.root / f"{day.isoformat()}_{slug}"
        n = 2
        while path.exists():
            path = self.root / f"{day.isoformat()}_{slug}-{n}"
            n += 1
        path.mkdir(parents=True)
        return Entry(path)

    def entries(self) -> list[Entry]:
        if not self.root.exists():
            return []
        return sorted((Entry(p) for p in self.root.iterdir() if p.is_dir() and not p.name.startswith(".")),
                      key=lambda e: e.id)

    def get(self, entry_id: str) -> Entry:
        return Entry(self.root / entry_id)

    def record(self, entry: Entry) -> None:
        """Append the entry's summary to index.jsonl once it is finished."""
        meta = entry.metadata
        row = {k: meta.get(k) for k in ("date", "topic", "title", "status", "youtube_id", "youtube_url",
                                        "release_url", "duration")}
        self.root.mkdir(parents=True, exist_ok=True)
        with self.index.open("a") as f:
            f.write(json.dumps({"id": entry.id, **row}) + "\n")

    def uploaded(self) -> list[Entry]:
        return [e for e in self.entries() if e.metadata.get("youtube_id")]
