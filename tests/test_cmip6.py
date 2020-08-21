import os
import unittest
import src.cmip6 as cmip6
from src.cmip6 import CMIP6DateFrequency as dt_freq
from tests.shared_test_utils import setUp_ConfigManager, tearDown_ConfigManager

# really incomplete! Do more systematically.
#@unittest.skipIf(True,
#    "Skipping TestCMIP6_CVs since we don't want to read in the json")
class TestCMIP6_CVs(unittest.TestCase):
    def setUp(self):
        setUp_ConfigManager()

    def tearDown(self):
        tearDown_ConfigManager()

    def test_is_in_cv(self):
        x = cmip6.CMIP6_CVs()
        self.assertTrue(x.is_in_cv('table_id', 'IyrGre'))

    def test_some_lookups(self):
        x = cmip6.CMIP6_CVs()
        self.assertEqual(
            'NCC',
            x.lookup('NorCPM1', 'source_id', 'institution_id')
        )
        self.assertCountEqual(
            ['NorCPM1', 'NorESM2-LMEC', 'NorESM2-HH', 'NorESM1-F', 
                'NorESM2-MH', 'NorESM2-LM', 'NorESM2-MM', 'NorESM2-LME'],
            x.lookup('NCC', 'institution_id', 'source_id')
        )

    @unittest.skip("")
    def test_table_id_lookup(self):
        x = cmip6.CMIP6_CVs()
        self.assertEqual(
            x.lookup('AERmon', 'table_id', 'date_freq'),
            set([dt_freq('mon')])
        )
        self.assertEqual(
            x.lookup('AERmon', 'table_id', 'table_freq'),
            set(['mon'])
        )
        self.assertEqual(
            x.lookup(dt_freq('mon'), 'date_freq', 'table_id'),
            set(['EmonZ', 'AERmon', 'SImon', 'Amon', 'CFmon', 'Omon', 
                'ImonGre', 'Emon', 'ImonAnt', 'Lmon', 'LImon', 'Oclim', 
                'AERmonZ'])
        )
        self.assertEqual(
            x.lookup('mon', 'table_freq', 'table_id'),
            set(['EmonZ', 'AERmon', 'SImon', 'Amon', 'CFmon', 'Omon', 
                'ImonGre', 'Emon', 'ImonAnt', 'Lmon', 'LImon', 'Oclim', 
                'AERmonZ'])
        )

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