import unittest
from pathlib import Path
from unittest import mock

from content_pilot.agent import tools, youtube_tools as yt

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@mock.patch.object(tools, "STUDIO_DIR", FIXTURES)
class YoutubeToolsTest(unittest.TestCase):
    def test_score_hooks_ranks_and_names_formula(self):
        out = yt.score_hooks.invoke({"hooks": ["You would lose a war to 20,000 emus.", "Birds are interesting."]})
        self.assertIn("VERDICT", out)
        self.assertLess(out.index("20,000 emus"), out.index("Birds are interesting"))

    def test_lint_title_flags_thumbnail_duplication(self):
        out = yt.lint_title.invoke({"titles": ["The 1932 War Australia Lost to 20,000 Emus"], "thumbnail": "EMUS WON"})
        self.assertIn("duplicate", out)

    def test_find_dead_air(self):
        out = yt.find_dead_air.invoke({"transcript_path": "/long_video.srt"})
        for kind in ("DEAD", "FILLER", "REPEAT"):
            self.assertIn(kind, out)

    def test_make_chapters_starts_at_zero(self):
        out = yt.make_chapters.invoke({"transcript_path": "/long_video.srt", "target": 3})
        self.assertIn("0:00", out)

    def test_read_retention_finds_hook_leak(self):
        out = yt.read_retention.invoke({"csv_path": "/retention.csv", "duration": 600})
        self.assertIn("HOOK LEAK", out)

    def test_rank_outliers(self):
        out = yt.rank_outliers.invoke({"data_path": "/collected.json"})
        self.assertIn("The 1932 War Australia Lost to 20,000 Birds", out)

    def test_missing_input_is_reported(self):
        with self.assertRaises(FileNotFoundError):
            yt.find_dead_air.invoke({"transcript_path": "/nope.srt"})

    def test_paths_cannot_escape_the_studio(self):
        with self.assertRaises(ValueError):
            yt.find_dead_air.invoke({"transcript_path": "/../../README.md"})


if __name__ == "__main__":
    unittest.main()
