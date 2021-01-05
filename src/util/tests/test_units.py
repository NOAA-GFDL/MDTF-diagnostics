import unittest
import unittest.mock as mock
from src.util import units as util
from src.util import exceptions

# TODO: better tests

class TestUnitConversionFactor(unittest.TestCase):
    def test_conversion_factors(self):
        # assertAlmostEqual w/default precision for comparison of floating-point
        # values
        self.assertAlmostEqual(util.conversion_factor('inch', 'cm'), 2.54)
        self.assertAlmostEqual(util.conversion_factor('cm', 'inch'), 1.0/2.54)
        self.assertAlmostEqual(util.conversion_factor((123, 'inch'), 'cm'), 123.0 * 2.54)

    def test_h2o_conversion(self):
        self.assertFalse(util.units_equal('kg m-1 s-1', 'mm day-1'))
        self.assertFalse(util.units_equivalent('kg m-1 s-1', 'mm day-1'))
        self.assertTrue(util.units_equivalent('kg m-1 s-1', 'mm day-1', allow_h2o=True))
        with self.assertRaises(TypeError):
            _ = util.conversion_factor('m s-1', 'kg m-2 s-1')
        self.assertAlmostEqual(util.conversion_factor('m s-1', 'kg m-2 s-1', allow_h2o=True), 1000.0)
