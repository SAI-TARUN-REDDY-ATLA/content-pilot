import sys
import unittest
from pathlib import Path
from unittest import mock

from content_pilot import cli
from content_pilot.pipeline import script as script_mod


def run_cli(*args):
    with mock.patch.object(sys, "argv", ["content-pilot", *args]):
        cli.main()


class CliTest(unittest.TestCase):
    def test_no_arguments_researches_its_own_topic(self):
        with mock.patch("content_pilot.daily.run", return_value=mock.Mock(path=Path("/lib/x"))) as run:
            run_cli()
        self.assertFalse(run.call_args.kwargs["upload"])

    def test_upload_flag(self):
        with mock.patch("content_pilot.daily.run", return_value=mock.Mock(path=Path("/lib/x"))) as run:
            run_cli("--upload", "--model", "google_genai:gemini-3.1-pro-preview")
        self.assertTrue(run.call_args.kwargs["upload"])
        self.assertEqual(run.call_args.kwargs["settings"].model, "google_genai:gemini-3.1-pro-preview")

    def test_topic_skips_the_agents(self):
        with mock.patch("content_pilot.pipeline.make_video") as make, mock.patch("content_pilot.daily.run") as run:
            run_cli("--topic", "the spotlight effect")
        self.assertEqual(make.call_args.args[0], "the spotlight effect")
        run.assert_not_called()


class WriteScriptTest(unittest.TestCase):
    def test_uses_configured_model_with_structured_output(self):
        fake = script_mod.Script(title="t", hook="h", lines=["l"], loop_line="x", description="d", hashtags=["a"])
        with mock.patch("langchain.chat_models.init_chat_model") as init:
            init.return_value.with_structured_output.return_value.invoke.return_value = fake
            out = script_mod.write_script("focus", "google_genai:gemini-3.7-flash")
        init.assert_called_once_with("google_genai:gemini-3.7-flash")
        init.return_value.with_structured_output.assert_called_once_with(script_mod.Script)
        self.assertIs(out, fake)


if __name__ == "__main__":
    unittest.main()
