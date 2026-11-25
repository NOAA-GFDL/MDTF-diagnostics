import types
import unittest
from unittest import mock

import numpy as np
import xarray as xr

from src import preprocessor


def _bare_preprocessor():
    # skip __init__, which needs a model path manager and parsed config;
    # the methods tested here use neither
    return object.__new__(preprocessor.NullPreprocessor)


class TestNCLOutputFlag(unittest.TestCase):
    # pod_reqs is the merged settings.jsonc "runtime_requirements" of all PODs,
    # keyed by language, with the libraries each language needs as values

    def test_ncl_key_sets_flag(self):
        pp = _bare_preprocessor()
        pp.write_ds({}, {}, {'python3': ['numpy', 'xarray'],
                             'ncl': ['contributed', 'gsn_code']})
        self.assertTrue(pp.output_to_ncl)

    def test_ncl_key_without_libraries_sets_flag(self):
        pp = _bare_preprocessor()
        pp.write_ds({}, {}, {'python3': [], 'ncl': []})
        self.assertTrue(pp.output_to_ncl)

    def test_no_ncl_key_leaves_flag_unset(self):
        pp = _bare_preprocessor()
        pp.write_ds({}, {}, {'python3': ['numpy', 'xarray']})
        self.assertFalse(pp.output_to_ncl)


class TestCleanFillValue(unittest.TestCase):
    def setUp(self):
        self.var = types.SimpleNamespace(
            log=mock.MagicMock(),
            translation=types.SimpleNamespace(name='rlut')
        )

    NCL_FILL = np.float32(9.969209968386869e+36)  # NCL's default float _FillValue

    def _clean(self, fill_value, output_to_ncl, dtype='f4', name='rlut'):
        pp = _bare_preprocessor()
        pp.output_to_ncl = output_to_ncl
        da = xr.DataArray(np.zeros(3, dtype=dtype), dims='time', name=name)
        da.encoding['_FillValue'] = fill_value
        pp.clean_nc_var_encoding(self.var, name, da)
        return da

    def test_nan_fill_replaced_for_ncl(self):
        # NCL does not treat NaN as missing: missing data is written with NCL's default fill instead
        da = self._clean(np.float32(np.nan), output_to_ncl=True)
        self.assertEqual(da.encoding['_FillValue'], self.NCL_FILL)
        self.assertEqual(da.encoding['_FillValue'].dtype, np.float32)
        self.assertNotIn('_FillValue', da.attrs)

    def test_nan_fill_kept_without_ncl(self):
        da = self._clean(np.float32(np.nan), output_to_ncl=False)
        self.assertTrue(np.isnan(da.encoding['_FillValue']))

    def test_numeric_fill_kept_for_ncl(self):
        da = self._clean(np.float32(1.0e20), output_to_ncl=True)
        self.assertEqual(da.encoding['_FillValue'], np.float32(1.0e20))

    def test_none_fill_for_ncl(self):
        # an already-unset _FillValue used to raise TypeError in np.isnan; it now gets NCL's fill, since
        # xarray would otherwise write missing float data as NaN
        da = self._clean(None, output_to_ncl=True)
        self.assertEqual(da.encoding['_FillValue'], self.NCL_FILL)

    def test_none_fill_for_ncl_integer_var(self):
        # integer variables get no float fill value
        da = self._clean(None, output_to_ncl=True, dtype='i4')
        self.assertIsNone(da.encoding['_FillValue'])

    def test_coordinate_fill_removed(self):
        # variables other than the POD's variable (coordinates, bounds) still have their fill dropped
        da = self._clean(np.float32(np.nan), output_to_ncl=True, name='lat')
        self.assertIsNone(da.encoding['_FillValue'])


if __name__ == '__main__':
    unittest.main()
