import unittest
from src import units


# TODO: better tests


class TestUnitConversionFactor(unittest.TestCase):
    def test_conversion_factors(self):
        # assertAlmostEqual w/default precision for comparison of floating-point
        # values
        self.assertAlmostEqual(units.conversion_factor('inch', 'cm'), 2.54)
        self.assertAlmostEqual(units.conversion_factor('cm', 'inch'), 1.0 / 2.54)
        self.assertAlmostEqual(units.conversion_factor((123, 'inch'), 'cm'), 123.0 * 2.54)


class TestRefTime(unittest.TestCase):
    def get_test_date_strings(self, unit=None, time=None):
        strs = ['2020-05-25', '2000-01-01', '0001-01-01', '0000-01-01']
        if unit is None:
            unit = 'days'
        if time is None:
            return [f"{unit} since {s}" for s in strs]
        else:
            return [f"{unit} since {s} {time}" for s in strs]

    def get_test_reftimes(self, unit=None, time=None, calendar=None):
        return [units.Units(s, calendar=calendar)
                for s in self.get_test_date_strings(unit, time)]

    def test_isreftime(self):
        self.assertFalse(units.Units('days').isreftime)
        self.assertFalse(units.Units('years').isreftime)
        self.assertFalse(units.Units('kg').isreftime)

        for u in self.get_test_reftimes():
            with self.subTest(test_u=u):
                self.assertTrue(u.isreftime)

        for u in self.get_test_reftimes(calendar='julian'):
            with self.subTest(test_u=u):
                self.assertTrue(u.isreftime)

        for u in self.get_test_reftimes(time='12:34:56', calendar='noleap'):
            with self.subTest(test_u=u):
                self.assertTrue(u.isreftime)

        for u in self.get_test_reftimes(unit='minutes', time='12:34:56',
                                        calendar='proleptic_gregorian'):
            with self.subTest(test_u=u):
                self.assertTrue(u.isreftime)

    def multi_compare(self, list_1, list_2, compare_method, value):
        for ui in list_1:
            for uj in list_2:
                with self.subTest(ui=ui, uj=uj):
                    self.assertEqual(getattr(ui, compare_method)(uj), value)

    def multi_compare_id(self, list_1, compare_method):
        for i in range(len(list_1)):
            for j in range(len(list_1)):
                with self.subTest(ui=list_1[i], uj=list_1[j]):
                    # filter out cases that will compare dates that both
                    # have years = 0000 to avoid issue with cftime_dataparse
                    # being unable to compare dates that each have year 0000
                    # without has_year_zero=True. There is no way to pass this
                    # parameter to the cftime_dateparse method via this test,so
                    # this hack will have to do for now
                    if '0000' in list_1[i].units.split('-')[0] or \
                            '0000' in list_1[j].units.split('-')[0] or \
                            'days' not in list_1[i].units.split('-')[0] and \
                            'days' not in list_1[j].units.split('-')[0]:
                        #  print(str(list_1[i].units.split('-')[0]))
                        continue
                    elif i == j:
                        self.assertTrue(
                            getattr(list_1[i], compare_method)(list_1[j])
                        )
                    else:
                        self.assertFalse(
                            getattr(list_1[i], compare_method)(list_1[j])
                        )

    def test_equal(self):
        # equal if they're equivalent and the unit conversion is the identity
        us = self.get_test_reftimes() \
             + self.get_test_reftimes(calendar='julian') \
             + self.get_test_reftimes(unit='minutes', time='12:34:56',
                                      calendar='proleptic_gregorian') \
             + [units.Units('days'), units.Units('minutes')]

        self.multi_compare_id(us, 'equals')

    def test_equivalent(self):
        # equivalent if it's well-defined to do a unit conversion from one to the other
        us = self.get_test_reftimes()
        u_day = [units.Units('days')]

        self.multi_compare(us, us, 'equivalent', True)
        self.multi_compare(u_day, us, 'equivalent', False)
        self.multi_compare(us, u_day, 'equivalent', False)

        us_2 = self.get_test_reftimes(calendar='julian')
        self.multi_compare(us, us_2, 'equivalent', False)

        us_2 = self.get_test_reftimes(unit='minutes', time='12:34:56',
                                      calendar='proleptic_gregorian')
        self.multi_compare(us, us_2, 'equivalent', False)

    def test_reftime_base_eq(self):
        # true if base units are equal
        us = self.get_test_reftimes() \
             + self.get_test_reftimes(calendar='julian')
        u_day = [units.Units('days')]

        self.multi_compare_id(us, 'reftime_base_eq')
        self.multi_compare(u_day, us, 'reftime_base_eq', True)
        self.multi_compare(us, u_day, 'reftime_base_eq', True)

        us_2 = self.get_test_reftimes(unit='minutes', time='12:34:56',
                                      calendar='proleptic_gregorian')
        u_min = [units.Units('minutes')]

        self.multi_compare_id(us_2, 'reftime_base_eq')
        self.multi_compare(u_min, us_2, 'reftime_base_eq', True)
        self.multi_compare(us_2, u_min, 'reftime_base_eq', True)

        self.multi_compare(u_min, u_day, 'reftime_base_eq', False)
        self.multi_compare(u_min, us, 'reftime_base_eq', False)
        self.multi_compare(u_day, us_2, 'reftime_base_eq', False)
        self.multi_compare(us, us_2, 'reftime_base_eq', False)
