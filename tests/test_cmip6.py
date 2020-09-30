import os
import unittest
import src.cmip6 as cmip6
from src.cmip6 import CMIP6DateFrequency as dt_freq
import src.datelabel as dl
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
    all_freqs = ['fx', 'dec', 'yr', 'yrPt', 'mon', 'monC', 'day',
        '6hr', '6hrPt', '3hr', '3hrPt', '1hr', '1hrCM', '1hrPt', 
        'subhrPt']

    def test_string_output(self):
        for s in self.all_freqs:
            self.assertEqual(s, str(dt_freq(s)))

    def test_comparisons(self):
        for i in range(0, len(self.all_freqs) - 1):
            self.assertTrue(
                dt_freq(self.all_freqs[i]) >= dt_freq(self.all_freqs[i+1])
            )

    def test_is_static(self):
        self.assertTrue(dt_freq(self.all_freqs[0]).is_static)
        for i in range(1, len(self.all_freqs) - 1):
            self.assertFalse(dt_freq(self.all_freqs[i]).is_static)

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

class TestDRSFilename(unittest.TestCase):
    def test_all_attrs(self):
        file_ = 'prw_Amon_GFDL-ESM4_historical_r1i1p1f1_gr1_195001-201412.nc'
        d = cmip6.parse_DRS_filename(file_)
        self.assertEqual(d['variable_id'], 'prw')
        self.assertEqual(d['table_id'], 'Amon')
        self.assertEqual(d['source_id'], 'GFDL-ESM4')
        self.assertEqual(d['experiment_id'], 'historical')
        self.assertEqual(d['realization_code'], 'r1i1p1f1')
        self.assertEqual(d['grid_label'], 'gr1')
        self.assertEqual(d['start_date'], dl.Date(1950,1))
        self.assertEqual(d['end_date'], dl.Date(2014,12))
        self.assertEqual(d['date_range'], dl.DateRange('195001-201412'))

    def test_fx_attrs(self):
        file_ = 'areacello_Ofx_GFDL-ESM4_historical_r1i1p1f1_gn.nc'
        d = cmip6.parse_DRS_filename(file_)
        self.assertEqual(d['variable_id'], 'areacello')
        self.assertEqual(d['table_id'], 'Ofx')
        self.assertEqual(d['source_id'], 'GFDL-ESM4')
        self.assertEqual(d['experiment_id'], 'historical')
        self.assertEqual(d['realization_code'], 'r1i1p1f1')
        self.assertEqual(d['grid_label'], 'gn')
        self.assertEqual(d['start_date'], dl.FXDateMin)
        self.assertEqual(d['end_date'], dl.FXDateMax)
        self.assertEqual(d['date_range'], dl.FXDateRange)

    def test_fx_consistency_check(self):
        file_ = 'areacello_3hr_GFDL-ESM4_historical_r1i1p1f1_gn.nc'
        self.assertRaises(ValueError, cmip6.parse_DRS_filename, file_)
        file_ = 'prw_Ofx_GFDL-ESM4_historical_r1i1p1f1_gr1_195001-201412.nc'
        self.assertRaises(ValueError, cmip6.parse_DRS_filename, file_)


if __name__ == '__main__':
    unittest.main()