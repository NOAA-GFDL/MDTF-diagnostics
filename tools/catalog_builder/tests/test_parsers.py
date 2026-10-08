"""Tests for parse_nc_file in tools/catalog_builder/parsers.py.

Each test writes a small synthetic netCDF file to a temporary directory and
parses it, so no model output on disk is needed.
"""
import pathlib
import tempfile
import unittest

import numpy as np
import xarray as xr

from tools.catalog_builder import parsers


class ParseNcFileTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _parse(self, ds, file_name, variable_id=""):
        path = self.tmp_dir / file_name
        ds.to_netcdf(path, engine="netcdf4")
        catalog_info = parsers.setup_catalog()
        catalog_info['variable_id'] = variable_id
        return parsers.parse_nc_file(path, catalog_info)


def _time_ds(values, units, calendar):
    time = xr.DataArray(np.asarray(values, dtype='f8'), dims='time',
                        attrs={'units': units, 'calendar': calendar})
    ds = xr.Dataset(coords={'time': time})
    ds['FLUT'] = xr.DataArray(np.zeros(len(values), dtype='f4'), dims='time',
                              attrs={'long_name': 'Upwelling longwave flux at top of model',
                                     'units': 'W/m2'})
    return ds


class TestTimeRange(ParseNcFileTestCase):
    def test_noleap_end_date(self):
        # 20 noleap years of daily data; decoding the last step with the
        # standard calendar lands 5 days early (leap days 1996-2012)
        ds = _time_ds([0, 20 * 365 - 1], 'days since 1995-01-01 00:00:00', 'noleap')
        info = self._parse(ds, 'case.cam.h1.FLUT.19950101-20141231.nc')
        self.assertEqual(info['time_range'], '19950101:000000-20141231:000000')

    def test_year_zero_reference(self):
        # POP output uses "days since 0000-01-01" with a noleap calendar;
        # cftime rejects year 0 unless the calendar is passed
        ds = _time_ds([365, 2 * 365], 'days since 0000-01-01 00:00:00', 'noleap')
        info = self._parse(ds, 'case.pop.h.FLUT.000101-000112.nc')
        self.assertEqual(info['time_range'], '00010101:000000-00020101:000000')


def _cesm_ts_ds():
    # a CESM timeseries file: one data variable plus auxiliary variables that
    # also have long_name attributes, written before and after the main one
    ds = _time_ds([0, 1], 'days since 1995-01-01 00:00:00', 'noleap')
    flut = ds['FLUT']
    ds = ds.drop_vars('FLUT')
    ds['P0'] = xr.DataArray(np.float64(1.0e5),
                            attrs={'long_name': 'reference pressure', 'units': 'Pa'})
    ds['FLUT'] = flut
    ds['datesec'] = xr.DataArray(np.zeros(2, dtype='i4'), dims='time',
                                 attrs={'long_name': 'current seconds of current date'})
    ds['time_bounds'] = xr.DataArray(np.zeros((2, 2)), dims=('time', 'nbnd'),
                                     attrs={'long_name': 'time interval endpoints'})
    return ds


class TestMainVariable(ParseNcFileTestCase):
    def _assert_flut(self, info):
        self.assertEqual(info['variable_id'], 'FLUT')
        self.assertEqual(info['long_name'], 'Upwelling longwave flux at top of model')
        self.assertEqual(info['units'], 'W/m2')

    def test_variable_from_file_name(self):
        info = self._parse(_cesm_ts_ds(), 'case.cam.h1.FLUT.19950101-19950102.nc')
        self._assert_flut(info)

    def test_variable_from_caller(self):
        # the GFDL parsers set variable_id from the path before parsing
        info = self._parse(_cesm_ts_ds(), 'atmos.19950101-19950102.nc',
                           variable_id='FLUT')
        self._assert_flut(info)

    def test_fallback_to_first_variable(self):
        # no file name part names a variable: the first variable with a
        # long_name or standard_name is used, as before
        info = self._parse(_cesm_ts_ds(), 'case.cam.h1.19950101-19950102.nc')
        self.assertEqual(info['variable_id'], 'P0')
        self.assertEqual(info['long_name'], 'reference pressure')
        self.assertEqual(info['units'], 'Pa')


if __name__ == '__main__':
    unittest.main()
