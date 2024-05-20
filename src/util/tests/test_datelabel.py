import unittest
import datetime
from src.util.datelabel import Date as dt
from src.util.datelabel import DateRange as dt_range
from src.util.datelabel import DateFrequency as dt_freq
from src.util.datelabel import FXDateMin, FXDateMax, FXDateRange
from src.util.exceptions import FXDateException


class TestDate(unittest.TestCase):
    def test_init(self):
        self.assertEqual(dt(2019), datetime.datetime(2019, 1, 1))
        self.assertEqual(dt(2019).precision, 1)
        self.assertEqual(dt(2019, 9, 18), datetime.datetime(2019, 9, 18))
        self.assertEqual(dt(2019, 9, 18).precision, 3)

    def test_init_coerce(self):
        self.assertEqual(dt(datetime.datetime(2019, 1, 1), 1), dt(2019))
        self.assertEqual(dt(datetime.datetime(2019, 5, 1), 2), dt(2019, 5))
        self.assertEqual(dt(datetime.datetime(2019, 5, 18), 2), dt(2019, 5))

    def test_init_epoch(self):
        # Make sure we're not doing platform-dependent stuff that breaks
        # outside of 1970-2038
        self.assertEqual(dt(1850), datetime.datetime(1850, 1, 1))
        self.assertEqual(dt(1850).precision, 1)
        self.assertEqual(dt(2112, 9, 18), datetime.datetime(2112, 9, 18))
        self.assertEqual(dt(2112, 9, 18).precision, 3)
        self.assertEqual(dt(datetime.datetime(1850, 1, 1), 1), dt(1850))
        self.assertEqual(dt(datetime.datetime(1850, 5, 1), 2), dt(1850, 5))
        self.assertEqual(dt(datetime.datetime(1850, 5, 18), 2), dt(1850, 5))
        self.assertEqual(dt(datetime.datetime(2112, 1, 1), 1), dt(2112))
        self.assertEqual(dt(datetime.datetime(2112, 5, 1), 2), dt(2112, 5))
        self.assertEqual(dt(datetime.datetime(2112, 5, 18), 2), dt(2112, 5))

    def test_string_parsing(self):
        self.assertEqual(dt('2019'), datetime.datetime(2019, 1, 1))
        self.assertEqual(dt('2019').precision, 1)
        self.assertEqual(dt('2019091814'), datetime.datetime(2019, 9, 18, 14))
        self.assertEqual(dt('2019091814').precision, 4)
        self.assertEqual(dt('2019-09-18'), datetime.datetime(2019, 9, 18))
        self.assertEqual(dt('2019-09-18').precision, 3)

    def test_string_output(self):
        self.assertEqual('{}'.format(dt('2019')), '2019')
        self.assertEqual('{}'.format(dt('20190918')), '20190918')

    def test_string_output_pre1900(self):
        self.assertEqual('{}'.format(dt('1850')), '1850')
        self.assertEqual(dt('185009182359').format(precision=4), '1850091823')

    def test_string_output_iso(self):
        self.assertEqual(dt('1850').isoformat(), '1850-01-01 00:00:00')

    def test_comparisons_same(self):
        self.assertTrue(dt(2018) < dt(2019))
        self.assertTrue(dt(2019, 9) > dt(2018))
        self.assertTrue(dt(2019, 9) > dt(2019))
        self.assertTrue(dt(2019, 1) >= dt(2019))
        self.assertTrue(dt(2019, 1, 1, 12) <= dt(2019, 2))

    def test_comparisons_parent(self):
        self.assertTrue(dt(2018) < datetime.datetime(2019, 1, 1))
        self.assertTrue(dt(2019, 9) > datetime.datetime(2018, 12, 25, 23))

    def test_comparisons_coerce(self):
        self.assertTrue(dt(2018) <= datetime.date(2019, 1, 1))
        self.assertTrue(dt(2019, 9) >= datetime.date(2018, 12, 25))

    def test_minmax(self):
        test = [dt(2019, 2), dt(2019, 9), dt(2018),
                dt(2019), dt(2019, 1, 1, 12)]
        self.assertEqual(max(test), dt(2019, 9))
        self.assertEqual(min(test), dt(2018))

    def test_attributes(self):
        test = dt(2019)
        self.assertEqual(test.year, 2019)
        test = dt(2019, 9, 18, 23)
        self.assertEqual(test.year, 2019)
        self.assertEqual(test.month, 9)
        self.assertEqual(test.day, 18)
        self.assertEqual(test.hour, 23)

    def test_incr_decr(self):
        test = dt(2019)
        args = (test.lower, test.precision)
        self.assertEqual(test.increment(*args), datetime.datetime(2020, 1, 1))
        self.assertEqual(test.decrement(*args), datetime.datetime(2018, 1, 1))
        test = dt(2019, 1)
        args = (test.lower, test.precision)
        self.assertEqual(test.increment(*args), datetime.datetime(2019, 2, 1))
        self.assertEqual(test.decrement(*args), datetime.datetime(2018, 12, 1))
        # leap year
        test = dt(2020, 2, 28)
        args = (test.lower, test.precision)
        self.assertEqual(test.increment(*args), datetime.datetime(2020, 2, 29))
        test = dt(2020, 3, 1, 0)
        args = (test.lower, test.precision)
        self.assertEqual(test.decrement(*args), datetime.datetime(2020, 2, 29, 23))


class TestDateRange(unittest.TestCase):
    def test_string_parsing(self):
        self.assertEqual(dt_range('2010-2019'),
                         dt_range(dt(2010), dt(2019)))
        self.assertEqual(dt_range('20100201-20190918'),
                         dt_range(dt(2010, 2, 1), dt(2019, 9, 18)))

    def test_input_string_parsing(self):
        self.assertEqual(dt_range(2010, 2019),
                         dt_range(dt(2010), dt(2019)))
        self.assertEqual(dt_range('20100201', '20190918'),
                         dt_range(dt(2010, 2, 1), dt(2019, 9, 18)))

    def test_input_list_parsing(self):
        self.assertEqual(
            dt_range.from_date_span(dt(2015), dt(2010), dt(2019), dt(2017)),
            dt_range(2010, 2019))
        self.assertEqual(dt_range(['20100201', '20190918']),
                         dt_range('20100201', '20190918'))

    def test_input_range_parsing(self):
        dtr1 = dt_range('20190101', '20190131')
        dtr2 = dt_range('20190201', '20190228')
        dtr3 = dt_range('20190301', '20190331')
        self.assertEqual(
            dt_range.from_contiguous_span(dtr1, dtr2, dtr3),
            dt_range(dt(2019, 1, 1), dt(2019, 3, 31))
        )
        self.assertEqual(
            dt_range.from_contiguous_span(dtr3, dtr1, dtr2),
            dt_range(dt(2019, 1, 1), dt(2019, 3, 31))
        )
        with self.assertRaises(ValueError):
            _ = dt_range.from_contiguous_span(dtr3, dtr1)
        with self.assertRaises(ValueError):
            _ = dt_range.from_contiguous_span(dtr1, dt_range('20190214', '20190215'))
        with self.assertRaises(ValueError):
            _ = dt_range.from_contiguous_span(dtr1, dtr2, dtr3, dt_range('20190214', '20190215'))
        with self.assertRaises(ValueError):
            _ = dt_range.from_contiguous_span(dtr3, dtr1, dt_range('20181214', '20190215'), dtr2)

    def test_overlaps(self):
        r1 = dt_range(dt(2010), dt(2020))
        # move right endpoint, then left endpoint of test interval
        self.assertEqual(r1.overlaps(dt_range('2008-2009')), False)
        self.assertEqual(r1.overlaps(dt_range('2008-2010')), True)
        self.assertEqual(r1.overlaps(dt_range('2008-2019')), True)
        self.assertEqual(r1.overlaps(dt_range('2008-2020')), True)
        self.assertEqual(r1.overlaps(dt_range('2008-2022')), True)

        self.assertEqual(r1.overlaps(dt_range('2010-2019')), True)
        self.assertEqual(r1.overlaps(dt_range('2010-2020')), True)
        self.assertEqual(r1.overlaps(dt_range('2010-2022')), True)

        self.assertEqual(r1.overlaps(dt_range('2011-2019')), True)
        self.assertEqual(r1.overlaps(dt_range('2011-2020')), True)
        self.assertEqual(r1.overlaps(dt_range('2011-2022')), True)

        self.assertEqual(r1.overlaps(dt_range('2020-2022')), True)
        self.assertEqual(r1.overlaps(dt_range('2021-2022')), False)

    def test_contains(self):
        r1 = dt_range(dt(2010), dt(2020))
        # move right endpoint, then left endpoint of test interval
        self.assertEqual(r1.contains(dt_range('2008-2009')), False)
        self.assertEqual(r1.contains(dt_range('2008-2010')), False)
        self.assertEqual(r1.contains(dt_range('2008-2019')), False)
        self.assertEqual(r1.contains(dt_range('2008-2020')), False)
        self.assertEqual(r1.contains(dt_range('2008-2022')), False)

        self.assertEqual(r1.contains(dt_range('2010-2019')), True)
        self.assertEqual(r1.contains(dt_range('2010-2020')), True)
        self.assertEqual(r1.contains(dt_range('2010-2022')), False)

        self.assertEqual(r1.contains(dt_range('2011-2019')), True)
        self.assertEqual(r1.contains(dt_range('2011-2020')), True)
        self.assertEqual(r1.contains(dt_range('2011-2022')), False)

        self.assertEqual(r1.contains(dt_range('2020-2022')), False)
        self.assertEqual(r1.contains(dt_range('2021-2022')), False)

    def test_in_contains(self):
        r1 = dt_range(dt(2010), dt(2020))
        # move right endpoint, then left endpoint of test interval
        self.assertEqual(r1 in dt_range('2008-2009'), False)
        self.assertEqual(r1 in dt_range('2008-2010'), False)
        self.assertEqual(r1 in dt_range('2008-2019'), False)
        self.assertEqual(r1 in dt_range('2008-2020'), True)
        self.assertEqual(r1 in dt_range('2008-2022'), True)

        self.assertEqual(r1 in dt_range('2010-2019'), False)
        self.assertEqual(r1 in dt_range('2010-2020'), True)
        self.assertEqual(r1 in dt_range('2010-2022'), True)

        self.assertEqual(r1 in dt_range('2011-2019'), False)
        self.assertEqual(r1 in dt_range('2011-2020'), False)
        self.assertEqual(r1 in dt_range('2011-2022'), False)

        self.assertEqual(r1 in dt_range('2020-2022'), False)
        self.assertEqual(r1 in dt_range('2021-2022'), False)

    def test_intersect(self):
        r1 = dt_range('2000-2010')
        with self.assertRaises(ValueError):
            _ = r1.intersection(dt_range('1900-1990'))
        self.assertEqual(r1.intersection(dt_range('2002-2008')), dt_range('2002-2008'))
        self.assertEqual(r1.intersection(dt_range('1999-2018')), dt_range('2000-2010'))
        self.assertEqual(r1.intersection(dt_range('2002-2018')), dt_range('2002-2010'))
        self.assertEqual(r1.intersection(dt_range('1999-2008')), dt_range('2000-2008'))
        self.assertEqual(r1.intersection(dt_range('2000-2010')), dt_range('2000-2010'))

    def test_more_overlaps(self):
        # mixed precision
        rng1 = dt_range('1980-1990')
        rng2 = [
            (dt_range('19780501-19781225'), False, False, False, False),
            (dt_range('19780501-19800101'), True, True, False, False),
            (dt_range('19780501-19871225'), True, True, False, False),
            (dt_range('19780501-19901231'), True, True, True, False),
            (dt_range('19780501-19981225'), True, True, True, False),
            (dt_range('19800101-19871225'), True, True, False, True),
            (dt_range('19800101-19901231'), True, True, True, True),
            (dt_range('19800101-19981225'), True, True, True, False),
            (dt_range('19830501-19871225'), True, True, False, True),
            (dt_range('19830501-19901231'), True, True, False, True),
            (dt_range('19830501-19981225'), True, True, False, False),
            (dt_range('19901231-19981225'), True, True, False, False),
            (dt_range('19930501-19981225'), False, False, False, False)
        ]
        for d in rng2:
            self.assertTrue(rng1.overlaps(d[0]) == d[1])
            self.assertTrue(d[0].overlaps(rng1) == d[2])
            self.assertTrue(d[0].contains(rng1) == d[3])
            self.assertTrue(rng1.contains(d[0]) == d[4])

    def test_more_intersection(self):
        # mixed precision
        rng1 = dt_range('1980-1990')
        rng2 = [
            dt_range('19780501-19871225'),
            dt_range('19780501-19901231'),
            dt_range('19780501-19981225'),
            dt_range('19800101-19871225'),
            dt_range('19800101-19901231'),
            dt_range('19800101-19981225'),
            dt_range('19830501-19871225'),
            dt_range('19830501-19901231'),
            dt_range('19830501-19981225')
        ]
        for d in rng2:
            self.assertTrue(rng1.intersection(d) == d.intersection(rng1))

    def test_more_contains(self):
        # mixed precision
        self.assertTrue(dt_range('198001010130-199912312230').contains(dt_range('1992-1999')))
        self.assertTrue(dt_range('199201010130-199912312230').contains(dt_range('1992-1999')))
        self.assertTrue(dt_range('1980-1999').contains(dt_range('19800101-19991231')))

    def test_repr(self):
        globs = {'DateRange': dt_range, 'Date': dt}
        r1 = dt_range('2000-2010')
        self.assertEqual(r1, eval(repr(r1), globs))
        r1 = dt_range('199912-200001')
        self.assertEqual(r1, eval(repr(r1), globs))
        r1 = dt_range('20000101-20000201')
        self.assertEqual(r1, eval(repr(r1), globs))

    def test_start_end_properties(self):
        rng = dt_range('1980-1990')
        self.assertEqual(rng.start, dt('1980'))
        self.assertEqual(rng.end, dt('1990'))
        rng = dt_range('19800101-19871225')
        self.assertEqual(rng.start, dt('19800101'))
        self.assertEqual(rng.end, dt('19871225'))


class TestFXDates(unittest.TestCase):
    def test_compare(self):
        dtr = dt_range('19800101-19901231')
        dt0 = dt('2019-09-18')
        with self.assertRaises(FXDateException):
            _ = (dt0 > FXDateMin)
        with self.assertRaises(FXDateException):
            _ = (dt0 <= FXDateMax)
        with self.assertRaises(FXDateException):
            _ = (dtr > FXDateMin)
        with self.assertRaises(FXDateException):
            _ = (dtr <= FXDateMax)
        with self.assertRaises(FXDateException):
            _ = (FXDateMin <= FXDateMax)
        with self.assertRaises(FXDateException):
            _ = (dtr <= FXDateRange)
        self.assertTrue(dtr != FXDateRange)
        self.assertTrue(dt0 != FXDateMax)

    def test_contain(self):
        dtr = dt_range('19800101-19901231')
        dt0 = dt('2019-09-18')
        self.assertTrue(dtr in FXDateRange)
        self.assertTrue(dt0 in FXDateRange)
        self.assertTrue(FXDateRange.contains(dtr))
        self.assertTrue(FXDateRange.contains(dt0))
        self.assertTrue(FXDateRange.overlaps(dtr))
        self.assertTrue(FXDateRange.overlaps(dt0))
        self.assertFalse(dtr.contains(FXDateRange))
        self.assertTrue(dtr.overlaps(FXDateRange))
        with self.assertRaises(FXDateException):
            _ = (dtr.intersection(FXDateRange))
        with self.assertRaises(FXDateException):
            _ = (FXDateRange.intersection(dtr))

    def test_is_static(self):
        dtr = dt_range('19800101-19901231')
        dt0 = dt('2019-09-18')
        self.assertTrue(FXDateMin.is_static)
        self.assertTrue(FXDateMax.is_static)
        self.assertTrue(FXDateRange.is_static)
        self.assertFalse(dt0.is_static)
        self.assertFalse(dtr.is_static)

    def test_span(self):
        dtr1 = dt_range('20190101', '20190131')
        dtr2 = dt_range('20190201', '20190228')
        dt0 = dt('2019-09-18')
        self.assertEqual(dt_range.from_contiguous_span(FXDateRange), FXDateRange)
        with self.assertRaises(FXDateException):
            _ = dt_range.from_contiguous_span(FXDateRange, FXDateRange)
        with self.assertRaises(FXDateException):
            _ = dt_range.from_contiguous_span(dtr1, FXDateRange, dtr2)
        with self.assertRaises(FXDateException):
            _ = dt_range.from_contiguous_span(dtr1, dtr2, FXDateRange)
        with self.assertRaises(FXDateException):
            _ = dt_range.from_date_span(FXDateMin, FXDateMax)
        with self.assertRaises(FXDateException):
            _ = dt_range.from_date_span(dt0, FXDateMax)

    def test_format(self):
        self.assertEqual(str(FXDateMin), "<N/A>")
        self.assertEqual(str(FXDateMax), "<N/A>")
        self.assertEqual(str(FXDateRange), "<N/A>")


class TestDateFrequency(unittest.TestCase):
    def test_string_parsing(self):
        self.assertEqual(dt_freq('1hr'), dt_freq(1, 'hr'))
        self.assertEqual(dt_freq('5yr'), dt_freq(5, 'yr'))
        self.assertEqual(dt_freq('monthly'), dt_freq(1, 'mo'))
        self.assertEqual(dt_freq('daily'), dt_freq(1, 'dy'))
        self.assertEqual(dt_freq('120hr'), dt_freq(120, 'hr'))
        self.assertEqual(dt_freq('2 weeks'), dt_freq(2, 'wk'))

    def test_from_struct(self):
        self.assertEqual(dt_freq.from_struct('1hr'), dt_freq(1, 'hr'))
        self.assertEqual(dt_freq.from_struct('5yr'), dt_freq(5, 'yr'))
        self.assertEqual(dt_freq.from_struct('monthly'), dt_freq(1, 'mo'))
        self.assertEqual(dt_freq.from_struct('daily'), dt_freq(1, 'dy'))
        self.assertEqual(dt_freq.from_struct('120hr'), dt_freq(120, 'hr'))
        self.assertEqual(dt_freq.from_struct('2 weeks'), dt_freq(2, 'wk'))

    def test_comparisons_same_unit(self):
        self.assertTrue(dt_freq(1, 'hr') < dt_freq(2, 'hr'))
        self.assertTrue(dt_freq(5, 'yr') > dt_freq(2, 'yr'))
        self.assertTrue(dt_freq(1, 'se') <= dt_freq(1, 'se'))
        self.assertTrue(dt_freq(2, 'mo') >= dt_freq(2, 'mo'))
        self.assertTrue(dt_freq(1, 'hr') <= dt_freq(2, 'hr'))

    def test_comparisons_different_unit(self):
        self.assertTrue(dt_freq(3, 'hr') < dt_freq(2, 'dy'))
        self.assertTrue(dt_freq(2, 'yr') > dt_freq(6, 'mo'))
        self.assertTrue(dt_freq(7, 'dy') <= dt_freq(1, 'wk'))
        self.assertTrue(dt_freq(24, 'hr') >= dt_freq(1, 'dy'))
        self.assertTrue(dt_freq(1, 'hr') <= dt_freq(2, 'yr'))

    def test_minmax_same_unit(self):
        test = [dt_freq(n, 'hr') for n in [6, 1, 12, 36, 3]]
        self.assertEqual(max(test), dt_freq(36, 'hr'))
        self.assertEqual(min(test), dt_freq(1, 'hr'))

    def test_minmax_different_unit(self):
        test = [dt_freq(n, 'dy') for n in [2, 7, 1]]
        test = test + [dt_freq(n, 'hr') for n in [12, 36, 3]]
        test = test + [dt_freq(n, 'wk') for n in [3, 1]]
        self.assertEqual(max(test), dt_freq(3, 'wk'))
        self.assertEqual(min(test), dt_freq(3, 'hr'))

    def test_fx_parsing(self):
        self.assertEqual(dt_freq('fx'), dt_freq('static'))
        self.assertEqual(dt_freq('fx'), dt_freq(0, 'fx'))
        self.assertEqual(dt_freq('fx'), dt_freq(1, 'fx'))
        self.assertEqual(dt_freq('fx').format(), 'fx')

    def test_fx_comparisons(self):
        self.assertTrue(dt_freq('fx') > dt_freq(2000, 'yr'))
        self.assertTrue(dt_freq('fx') > dt_freq(6, 'dy'))
        self.assertTrue(dt_freq('fx') > dt_freq(1, 'wk'))

    def test_is_static(self):
        self.assertTrue(dt_freq('fx').is_static)
        self.assertFalse(dt_freq(2000, 'yr').is_static)
        self.assertFalse(dt_freq(6, 'dy').is_static)
        self.assertFalse(dt_freq(1, 'hr').is_static)


if __name__ == '__main__':
    unittest.main()
