import os
import unittest
import src.cmip6 as cmip6
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

class TestMIPTableParsing(unittest.TestCase):
    test_freqs = {
        'fx': ['fx', 'Ofx', 'IfxAnt'],
        '1hr': ['E1hrClimMon', 'E1hr'],
        'mon': ['Oclim', 'SImon', 'AERmonZ'],
        '3hr': ['3hr', 'E3hrPt']
    }

    def test_datefreq(self):
        for k in self.test_freqs:
            for tbl in self.test_freqs[k]:
                d = cmip6.parse_mip_table_id(tbl)
                self.assertEqual(dt_freq(k), d['date_freq'])


if __name__ == '__main__':
    unittest.main()