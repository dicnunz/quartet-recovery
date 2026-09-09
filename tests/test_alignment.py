"""Small alignment controls: gaps, multiplicity, and unchanged note denominators."""
import sys
import unittest
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from aligned_diagnostic import align_measures, diagnostic


class AlignmentChecks(unittest.TestCase):
    def test_missing_measure_preserves_later_pairs(self):
        path, cost = align_measures([Counter([60]), Counter([62]), Counter([64])],
                                    [Counter([60]), Counter([65]), Counter([62]), Counter([64])])
        self.assertEqual(path, [(0, 0), (None, 1), (1, 2), (2, 3)])
        self.assertAlmostEqual(cost, .6)

    def test_pitch_multiplicity_affects_cost(self):
        path, cost = align_measures([Counter([60, 60])], [Counter([60])])
        self.assertEqual(path, [(0, 0)])
        self.assertAlmostEqual(cost, 1 / 3)

    def test_gapped_notes_remain_in_denominator(self):
        def score(notes):
            return {'parts': [{'measures': [{} for _ in notes]}] + [{'measures': []} for _ in range(3)],
                    'events': [{'part': 0, 'measure': i, 'midi': pitch, 'onset': '0', 'duration': '1'}
                               for i, pitch in enumerate(notes)]}
        out = diagnostic(score([60, 62, 64]), score([60, 65, 62, 64]))
        self.assertEqual(out['pitch_onset_duration']['matches'], 3)
        self.assertEqual(out['pitch_onset_duration']['predicted'], 3)
        self.assertEqual(out['pitch_onset_duration']['reference'], 4)
        self.assertAlmostEqual(out['pitch_onset_duration']['f1'], 6 / 7)

    def test_alignment_does_not_warp_onsets(self):
        parts = [{'measures': [{}]}] + [{'measures': []} for _ in range(3)]
        left = {'parts': parts, 'events': [{'part': 0, 'measure': 0, 'midi': 60, 'onset': '0', 'duration': '1'}]}
        right = {'parts': parts, 'events': [{**left['events'][0], 'onset': '1/2'}]}
        out = diagnostic(left, right)
        self.assertEqual(out['parts'][0]['paired_measures'], 1)
        self.assertEqual(out['pitch_onset']['matches'], 0)


if __name__ == '__main__':
    unittest.main()
