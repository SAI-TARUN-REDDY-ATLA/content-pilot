import re
import unittest

from content_pilot.config import STUDIO_DIR
from content_pilot.agent.team import TEAM


class TeamTest(unittest.TestCase):
    def test_skill_sources_exist_and_names_match_folders(self):
        for agent in TEAM:
            for source in agent.get("skills", []):
                folder = STUDIO_DIR / source.strip("/")
                self.assertTrue(folder.is_dir(), f"{agent['name']}: {source} missing")
                for skill in folder.iterdir():
                    if skill.is_dir():
                        head = (skill / "SKILL.md").read_text()
                        self.assertEqual(re.search(r"^name: (.+)$", head, re.M).group(1), skill.name)

    def test_specialists_never_get_render_video(self):
        for agent in TEAM:
            # A spec without "tools" inherits the producer's, render_video included.
            self.assertIn("tools", agent, agent["name"])
            names = [getattr(t, "name", t.get("name") if isinstance(t, dict) else t) for t in agent["tools"]]
            self.assertNotIn("render_video", names, agent["name"])


if __name__ == "__main__":
    unittest.main()
