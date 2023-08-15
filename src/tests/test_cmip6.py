import os
import unittest
from src.util import exceptions
import src.cmip6 as cmip6
from src.cmip6 import CMIP6DateFrequency as dt_freq
from src.util import datelabel as dl
from src.tests.shared_test_utils import setUp_config_singletons, tearDown_config_singletons


# really incomplete! Do more systematically.
class TestCMIP6_CVs(unittest.TestCase):
    def setUp(self):
        setUp_config_singletons()

    def tearDown(self):
        tearDown_config_singletons()

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
            ['NorCPM1',  'NorESM1-F', 'NorESM2-LM', 'NorESM2-MM'],
            x.lookup('NCC', 'institution_id', 'source_id')
        )

    @unittest.skip("")
    def test_table_id_lookup(self):
        x = cmip6.CMIP6_CVs()
        self.assertEqual(
            x.lookup('AERmon', 'table_id', 'frequency'),
            set([dt_freq('mon')])
        )
        self.assertEqual(
            x.lookup('AERmon', 'table_id', 'table_freq'),
            set(['mon'])
        )
        self.assertEqual(
            x.lookup(dt_freq('mon'), 'frequency', 'table_id'),
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
                d = cmip6.CMIP6_MIPTable(tbl)
                self.assertEqual(dt_freq(k), d.frequency)


class TestDRSFilename(unittest.TestCase):
    def test_all_attrs(self):
        file_ = 'prw_Amon_GFDL-ESM4_historical_r1i1p1f1_gr1_195001-201412.nc'
        d = cmip6.CMIP6_DRSFilename(file_)
        self.assertEqual(d.variable_id, 'prw')
        self.assertEqual(d.table_id, 'Amon')
        self.assertEqual(d.source_id, 'GFDL-ESM4')
        self.assertEqual(d.experiment_id, 'historical')
        self.assertEqual(d.variant_label, 'r1i1p1f1')
        self.assertEqual(d.grid_label, 'gr1')
        self.assertEqual(d.grid_number, 1)
        self.assertEqual(d.start_date, dl.Date(1950,1))
        self.assertEqual(d.end_date, dl.Date(2014,12))
        self.assertEqual(d.date_range, dl.DateRange('195001-201412'))

    def test_fx_attrs(self):
        file_ = 'areacello_Ofx_GFDL-ESM4_historical_r1i1p1f1_gn.nc'
        d = cmip6.CMIP6_DRSFilename(file_)
        self.assertEqual(d.variable_id, 'areacello')
        self.assertEqual(d.table_id, 'Ofx')
        self.assertEqual(d.source_id, 'GFDL-ESM4')
        self.assertEqual(d.experiment_id, 'historical')
        self.assertEqual(d.variant_label, 'r1i1p1f1')
        self.assertEqual(d.grid_label, 'gn')
        self.assertEqual(d.grid_number, 0)
        self.assertEqual(d.start_date, dl.FXDateMin)
        self.assertEqual(d.end_date, dl.FXDateMax)
        self.assertEqual(d.date_range, dl.FXDateRange)

    def test_fx_consistency_check(self):
        file_ = 'areacello_3hr_GFDL-ESM4_historical_r1i1p1f1_gn.nc'
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSFilename(file_)
        file_ = 'prw_Ofx_GFDL-ESM4_historical_r1i1p1f1_gr1_195001-201412.nc'
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSFilename(file_)

class TestDRSPath(unittest.TestCase):
    def test_path_examples(self):
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Omon/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        d = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        self.assertEqual(d.activity_id, 'CMIP')
        self.assertEqual(d.institution_id, 'E3SM-Project')
        self.assertEqual(d.source_id, 'E3SM-1-1')
        self.assertEqual(d.experiment_id, 'hist-bgc')
        self.assertEqual(d.variant_label, 'r1i1p1f1')
        self.assertEqual(d.table_id, 'Omon')
        self.assertEqual(d.variable_id, 'so')
        self.assertEqual(d.grid_label, 'gr')
        self.assertEqual(d.version_date, dl.Date('2019-11-12'))
        self.assertEqual(d.frequency, cmip6.CMIP6DateFrequency('mon'))
        self.assertEqual(d.start_date, dl.Date(1975, 1))
        self.assertEqual(d.end_date, dl.Date(1979, 12))

    def test_path_derived_fields(self):
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Omon/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        d = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        self.assertEqual(d.realization_index, 1)
        self.assertEqual(d.initialization_index, 1)
        self.assertEqual(d.physics_index, 1)
        self.assertEqual(d.forcing_index, 1)
        self.assertEqual(d.native_grid, False)
        self.assertEqual(d.temporal_avg, 'interval')
        self.assertEqual(d.spatial_avg, None)
        self.assertEqual(d.region, None)
        self.assertEqual(d.date_range, dl.DateRange('197501-197912'))

    def test_path_consistency(self):
        # inconsistent table_ids
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Oday/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        # inconsistent table_ids
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Emon/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        # inconsistent table_ids, static filename
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Oday/so/gr/v20191112"
        file_ = "so_Ofx_E3SM-1-1_hist-bgc_r1i1p1f1_gr.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        # inconsistent grid_labels
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Omon/so/gn/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))

    def test_consistency_derived_fields(self):
        # inconsistent realization_index
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r9i1p1f1/Omon/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        # inconsistent spatial_avg
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/Omon/so/gmr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))
        # inconsistent spatial_avg
        dir_ = "CMIP6/CMIP/E3SM-Project/E3SM-1-1/hist-bgc/r1i1p1f1/OmonZ/so/gr/v20191112"
        file_ = "so_Omon_E3SM-1-1_hist-bgc_r1i1p1f1_gr_197501-197912.nc"
        with self.assertRaises(exceptions.DataclassParseError):
            _ = cmip6.CMIP6_DRSPath(os.path.join(dir_, file_))


if __name__ == '__main__':
    unittest.main()