import os
import unittest
from src.cmip6 import CMIP6DateFrequency as dt_freq

class TestCMIP6DateFrequency(unittest.TestCase):
    all_freqs = ['dec', 'yr', 'yrPt', 'mon', 'monC', 'day',
        '6hr', '6hrPt', '3hr', '3hrPt', '1hr', '1hrCM', '1hrPt', 
        'subhrPt', 'fx']

    def test_string_output(self):
        for s in self.all_freqs:
            self.assertEqual(s, str(dt_freq(s)))

    def test_comparisons(self):
        for i in range(0, len(self.all_freqs) - 1):
            self.assertTrue(
                dt_freq(self.all_freqs[i]) >= dt_freq(self.all_freqs[i+1])
            )

if __name__ == '__main__':
    unittest.main()