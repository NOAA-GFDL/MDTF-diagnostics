import unittest
import unittest.mock as mock
from src import units as util
from src.util import exceptions

# TODO: better tests

class TestUnitConversionFactor(unittest.TestCase):
    def test_conversion_factors(self):
        # assertAlmostEqual w/default precision for comparison of floating-point
        # values
        self.assertAlmostEqual(util.conversion_factor('inch', 'cm'), 2.54)
        self.assertAlmostEqual(util.conversion_factor('cm', 'inch'), 1.0/2.54)
        self.assertAlmostEqual(util.conversion_factor((123, 'inch'), 'cm'), 123.0 * 2.54)

