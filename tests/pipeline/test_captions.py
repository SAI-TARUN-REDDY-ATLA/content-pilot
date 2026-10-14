import unittest

from content_pilot.pipeline.captions import Cue, align, phrases
from content_pilot.pipeline.render import scene_frames
from content_pilot.pipeline.run import chapter_list, scene_starts
from content_pilot.pipeline.script import Chapter, Scene, Script, emphasized_words, word_range
from content_pilot.pipeline.voice import Word


class AlignTest(unittest.TestCase):
    def test_exact_match_uses_spoken_times(self):
        tokens = ["Hello,", "*big*", "world."]
        spoken = [Word("Hello", 0.0, 0.3), Word("big", 0.35, 0.6), Word("world", 0.65, 1.0)]
        cues = align(tokens, spoken, [False, True, False])
        self.assertEqual([c.text for c in cues], ["Hello,", "big", "world."])
        self.assertEqual(cues[1].start, 0.35)
        self.assertTrue(cues[1].emphasis)
        # Short gaps are bridged so captions don't flicker.
        self.assertEqual(cues[0].end, 0.35)

    def test_split_number_still_timed(self):
        tokens = ["In", "1932,", "chaos."]
        spoken = [Word("In", 0.0, 0.1), Word("nineteen", 0.1, 0.4), Word("thirty-two", 0.4, 0.8), Word("chaos", 0.9, 1.2)]
        cues = align(tokens, spoken)
        self.assertEqual(len(cues), 3)
        self.assertAlmostEqual(cues[1].start, 0.1)
        self.assertAlmostEqual(cues[2].start, 0.9)
        for a, b in zip(cues, cues[1:]):
            self.assertLessEqual(a.start, b.start)


def make_script(*chapters: list[str]) -> Script:
    return Script(title="t", description="d", hashtags=[], thumbnail_text="x", thumbnail_image="y",
                  chapters=[Chapter(title=f"c{i}", scenes=[Scene(narration=n, image="img") for n in c])
                            for i, c in enumerate(chapters)])


class EmphasisTest(unittest.TestCase):
    def test_multi_word_emphasis(self):
        s = make_script(["They had *machine guns*, and lost.", "*Wrong.*"])
        self.assertEqual(emphasized_words(s), [False, False, True, True, False, False, True])
        self.assertNotIn("*", s.narration())
        self.assertEqual(s.hook, "They had *machine guns*, and lost.")


class PhraseTest(unittest.TestCase):
    def cues(self, text: str, gap_after: int | None = None) -> list[Cue]:
        out, t = [], 0.0
        for i, token in enumerate(text.split()):
            out.append(Cue(token, t, t + 0.3, raw=token))
            t += 1.5 if i == gap_after else 0.3
        return out

    def test_breaks_after_punctuation_and_when_full(self):
        lines = phrases(self.cues("The army came back. This time it went better, sort of, they said loudly today"))
        texts = [" ".join(c.text for c in line) for line in lines]
        self.assertEqual(texts[0], "The army came back.")
        self.assertTrue(all(len(line) <= 7 for line in lines))

    def test_breaks_on_long_pause(self):
        lines = phrases(self.cues("one two three four", gap_after=1))
        self.assertEqual([len(line) for line in lines], [2, 2])


class TimingTest(unittest.TestCase):
    def test_scene_frames_add_up_to_the_video(self):
        frames = scene_frames([0.0, 3.33, 7.01], 10.0, 30)
        self.assertEqual(sum(frames), 300)
        self.assertEqual(frames[0], 100)

    def test_scene_starts_follow_the_words(self):
        s = make_script(["One two three.", "Four *five*."], ["Six seven."])
        cues = [Cue(w, i * 1.0, i * 1.0 + 0.5) for i, w in enumerate("One two three. Four five. Six seven.".split())]
        self.assertEqual(scene_starts(s, cues), [0.0, 3.0, 5.0])

    def test_chapters_start_at_zero(self):
        self.assertEqual(chapter_list([("Cold Open", 0.4), ("Act Two", 75.2), ("End", 3725)]),
                         "0:00 Cold Open\n1:15 Act Two\n1:02:05 End")

    def test_word_range_scales_with_minutes(self):
        lo5, hi5 = word_range(5)
        lo10, _ = word_range(10)
        self.assertTrue(lo5 < 850 < hi5)
        self.assertEqual(lo10, 2 * lo5)


if __name__ == "__main__":
    unittest.main()
