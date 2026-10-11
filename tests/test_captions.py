import unittest

from content_pilot.captions import align
from content_pilot.script import Script, emphasized_words
from content_pilot.voice import Word


class AlignTest(unittest.TestCase):
    def test_exact_match_uses_spoken_times(self):
        tokens = ["Hello,", "*big*", "world."]
        spoken = [Word("Hello", 0.0, 0.3), Word("big", 0.35, 0.6), Word("world", 0.65, 1.0)]
        cues = align(tokens, spoken, [False, True, False])
        self.assertEqual([c.text for c in cues], ["Hello", "big", "world"])
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


class EmphasisTest(unittest.TestCase):
    def test_multi_word_emphasis(self):
        s = Script(title="t", hook="They had *machine guns*, and lost.", lines=[], loop_line="*Wrong.*",
                   description="d", hashtags=[])
        self.assertEqual(emphasized_words(s), [False, False, True, True, False, False, True])
        self.assertNotIn("*", s.narration())


if __name__ == "__main__":
    unittest.main()
