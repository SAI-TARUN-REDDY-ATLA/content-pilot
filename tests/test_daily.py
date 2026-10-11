import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from content_pilot import daily
from content_pilot.agent import tools
from content_pilot.agent.harness import DailyResult
from content_pilot.library import Library

EXAMPLE = Path(__file__).resolve().parents[1] / "studio/skills/writing/shorts-script/example.json"


def fake_make_video(topic, out_dir, settings, script_path, seed):
    work = out_dir / "work_x"
    work.mkdir(parents=True)
    (work / "voice.mp3").write_bytes(b"mp3")
    (work / "captions.json").write_text("[]")
    video = out_dir / "x.mp4"
    video.write_bytes(b"mp4")
    video.with_suffix(".json").write_text(json.dumps({"duration": 41.2, "background": "clip.mp4"}))
    return video


class DailyRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        studio = self.tmp / "studio"
        (studio / "scripts").mkdir(parents=True)
        shutil.copy(EXAMPLE, studio / "scripts/emus.json")
        (studio / "research").mkdir()
        (studio / "research/emus.md").write_text("- facts")
        self.result = DailyResult(topic="emu war", slug="emus", script_path="/scripts/emus.json",
                                  research_path="/research/emus.md", package_path="/packages/missing.md",
                                  thumbnail_text="EMUS WON", why="because")
        self.patches = [
            mock.patch.object(tools, "STUDIO_DIR", studio),
            mock.patch.object(daily, "Library", lambda: Library(self.tmp / "library")),
            mock.patch.object(daily, "produce", return_value=(self.result, "x\nOK")),
            mock.patch("content_pilot.pipeline.make_video", fake_make_video),
            mock.patch.object(daily, "refresh_stats"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp)

    def test_archives_every_artifact_and_uploads(self):
        up = {"id": "abc123", "url": "https://youtube.com/shorts/abc123", "privacy": "public"}
        with mock.patch("content_pilot.youtube.upload.upload", return_value=up) as yt:
            entry = daily.run(upload=True)
        self.assertEqual(yt.call_args.args[1], "Australia Declared War on Birds. The Birds Won.")
        files = sorted(p.name for p in entry.path.iterdir())
        self.assertEqual(files, ["captions.json", "metadata.json", "research.md", "script.json", "video.mp4", "voice.mp3"])
        meta = entry.metadata
        self.assertEqual((meta["status"], meta["youtube_id"], meta["duration"]), ("uploaded", "abc123", 41.2))
        self.assertIsInstance(meta["hook_score"], int)
        index = [json.loads(l) for l in (self.tmp / "library/index.jsonl").read_text().splitlines()]
        self.assertEqual(index[-1]["youtube_url"], up["url"])

    def test_failed_upload_is_recorded(self):
        with mock.patch("content_pilot.youtube.upload.upload", side_effect=RuntimeError("quota")):
            with self.assertRaises(RuntimeError):
                daily.run(upload=True)
        entry = Library(self.tmp / "library").entries()[-1]
        self.assertEqual(entry.metadata["status"], "failed")
        self.assertIn("quota", entry.metadata["error"])
        self.assertTrue((entry.path / "video.mp4").exists())

    def test_no_upload_stops_after_render(self):
        entry = daily.run(upload=False)
        self.assertEqual(entry.metadata["status"], "rendered")
        self.assertNotIn("youtube_id", entry.metadata)


class UploadBodyTest(unittest.TestCase):
    def test_shorts_metadata(self):
        from content_pilot.youtube.upload import build_body

        body = build_body("Why you freeze when you speak", "One fix.", ["confidence", "#psychology"])
        self.assertEqual(body["snippet"]["title"], "Why you freeze when you speak #Shorts")
        self.assertEqual(body["snippet"]["tags"], ["confidence", "psychology"])
        self.assertIn("#confidence #psychology #Shorts", body["snippet"]["description"])
        self.assertEqual(body["status"]["privacyStatus"], "public")
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])


if __name__ == "__main__":
    unittest.main()
