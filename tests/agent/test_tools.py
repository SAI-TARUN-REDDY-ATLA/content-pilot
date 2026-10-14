import unittest

from content_pilot.agent.tools import check_script


class CheckScriptTest(unittest.TestCase):
    def test_bundled_example_passes(self):
        result = check_script.invoke({"path": "/skills/writing/history-script/example.json"})
        self.assertTrue(result.endswith("OK"), result)

    def test_refuses_paths_outside_studio(self):
        result = check_script.invoke({"path": "/../README.md"})
        self.assertIn("outside the studio", result)


if __name__ == "__main__":
    unittest.main()
