import os
import unittest
import datetime
from src.datelabel import Date as dt
from src.datelabel import DateRange as dt_range
from src.datelabel import DateFrequency as dt_freq

class TestDate(unittest.TestCase):
    def test_init(self):
        self.assertEqual(dt(2019), datetime.datetime(2019,1,1))
        self.assertEqual(dt(2019).precision, 1)
        self.assertEqual(dt(2019,9,18), datetime.datetime(2019,9,18))
        self.assertEqual(dt(2019,9,18).precision, 3)

    def test_string_parsing(self):
        self.assertEqual(dt('2019'), datetime.datetime(2019,1,1))
        self.assertEqual(dt('2019').precision, 1)
        self.assertEqual(dt('2019091814'), datetime.datetime(2019,9,18,14))
        self.assertEqual(dt('2019091814').precision, 4)

    def test_string_output(self):
        self.assertEqual('{}'.format(dt('2019')), '2019')
        self.assertEqual('{}'.format(dt('20190918')), '20190918')

    def test_comparisons_same(self):
        self.assertTrue(dt(2018) < dt(2019))
        self.assertTrue(dt(2019,9) > dt(2018))
        self.assertTrue(dt(2019,9) > dt(2019))
        self.assertTrue(dt(2019,1) >= dt(2019))
        self.assertTrue(dt(2019,1,1,12) <= dt(2019,2))

    def test_comparisons_parent(self):
        self.assertTrue(dt(2018) < datetime.datetime(2019,1,1))
        self.assertTrue(dt(2019,9) > datetime.datetime(2018,12,25,23))

    def test_comparisons_coerce(self):
        self.assertTrue(dt(2018) <= datetime.date(2019,1,1))
        self.assertTrue(dt(2019,9) >= datetime.date(2018,12,25))

    def test_minmax(self):
        test = [dt(2019,2), dt(2019,9), dt(2018), 
            dt(2019), dt(2019,1,1,12)]
        self.assertEqual(max(test), dt(2019,9))
        self.assertEqual(min(test), dt(2018))

class TestDateRange(unittest.TestCase):
    def test_string_parsing(self):
        self.assertEqual(dt_range('2010-2019'), 
            dt_range(dt(2010), dt(2019)))
        self.assertEqual(dt_range('20100201-20190918'), 
            dt_range(dt(2010,2,1), dt(2019,9,18)))

    def test_input_parsing(self):
        self.assertEqual(dt_range(2010, 2019), 
            dt_range(dt(2010), dt(2019)))
        self.assertEqual(dt_range('20100201', '20190918'), 
            dt_range(dt(2010,2,1), dt(2019,9,18)))

    def test_overlaps(self):
        r1 = dt_range(dt(2010), dt(2019))
        self.assertFalse(r1.overlaps(dt_range('2007-2009')))
        self.assertTrue(r1.overlaps(dt_range('2009-2011')))
        self.assertTrue(r1.overlaps(dt_range('2011-2018')))
        self.assertTrue(r1.overlaps(dt_range('2011-2019')))
        self.assertTrue(r1.overlaps(dt_range('2009-2021')))
        self.assertTrue(r1.overlaps(dt_range('2015-2021')))
        self.assertFalse(r1.overlaps(dt_range('2020-2021')))

        self.assertFalse(r1 in dt_range('2007-2009'))
        self.assertTrue(r1 in dt_range('2009-2011'))
        self.assertTrue(r1 in dt_range('2011-2019'))

    def test_contains(self):
        r1 = dt_range(dt(2010), dt(2019))
        self.assertFalse(r1.contains(dt_range('2007-2009')))
        self.assertFalse(r1.contains(dt_range('2009-2011')))
        self.assertTrue(r1.contains(dt_range('2011-2018')))
        self.assertTrue(r1.contains(dt_range('2011-2019')))
        self.assertFalse(r1.contains(dt_range('2009-2021')))
        self.assertFalse(r1.contains(dt_range('2015-2021')))
        self.assertFalse(r1.contains(dt_range('2020-2021')))

class TestDateFrequency(unittest.TestCase):
    def test_string_parsing(self):
        self.assertEqual(dt_freq('1hr'), dt_freq(1, 'hr'))
        self.assertEqual(dt_freq('5yr'), dt_freq(5, 'yr'))
        self.assertEqual(dt_freq('monthly'), dt_freq(1, 'mo'))
        self.assertEqual(dt_freq('daily'), dt_freq(1, 'dy'))
        self.assertEqual(dt_freq('120hr'), dt_freq(120, 'hr'))
        self.assertEqual(dt_freq('2 weeks'), dt_freq(2, 'wk'))
    
    def test_comparisons_same_unit(self):
        self.assertTrue(dt_freq(1,'hr') < dt_freq(2,'hr'))
        self.assertTrue(dt_freq(5,'yr') > dt_freq(2,'yr'))
        self.assertTrue(dt_freq(1,'se') <= dt_freq(1,'se'))
        self.assertTrue(dt_freq(2,'mo') >= dt_freq(2,'mo'))
        self.assertTrue(dt_freq(1,'hr') <= dt_freq(2,'hr'))
    
    def test_comparisons_different_unit(self):
        self.assertTrue(dt_freq(3,'hr') < dt_freq(2,'dy'))
        self.assertTrue(dt_freq(2,'yr') > dt_freq(6,'mo'))
        self.assertTrue(dt_freq(7,'dy') <= dt_freq(1,'wk'))
        self.assertTrue(dt_freq(24,'hr') >= dt_freq(1,'dy'))
        self.assertTrue(dt_freq(1,'hr') <= dt_freq(2,'yr'))

    def test_minmax_same_unit(self):
        test = [dt_freq(n,'hr') for n in [6, 1, 12, 36, 3]]
        self.assertEqual(max(test), dt_freq(36, 'hr'))
        self.assertEqual(min(test), dt_freq(1, 'hr'))

    def test_minmax_different_unit(self):
        test = [dt_freq(n,'dy') for n in [2, 7, 1]]
        test = test + [dt_freq(n,'hr') for n in [12, 36, 3]]
        test = test + [dt_freq(n,'wk') for n in [3, 1]]
        self.assertEqual(max(test), dt_freq(3, 'wk'))
        self.assertEqual(min(test), dt_freq(3, 'hr'))

if __name__ == '__main__':
    unittest.main()