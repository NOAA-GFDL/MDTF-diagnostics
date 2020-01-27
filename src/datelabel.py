"""Classes and utility methods for dealing with dates as expressed in filenames 
and paths. Intended use case is, eg, determining if a file contains data for a
given year from the filename, without having to open it and parse the header.

Note:
    These classes should *not* be used for calendar math! We currently implement
    and test comparison logic only, not anything more (eg addition, subtraction).

Note: 
    These classes are based on the datetime standard library, and as such assume
    a proleptic Gregorian calendar for *all* dates.

Note: 
    Timezone support is not currently implemented.
"""
from __future__ import print_function
import re
import datetime
import operator as op

# ===============================================================
# following adapted from Alexandre Decan's python-intervals
# https://github.com/AlexandreDecan/python-intervals ; LGPLv3
# We neglect the case of noncontiguous or semi-infinite intervals here

class AtomicInterval(object):
    """
    This class represents an atomic interval.
    An atomic interval is a single interval, with a lower and upper bounds,
    and two (closed or open) boundaries.
    """
    __slots__ = ('_left', '_lower', '_upper', '_right')

    # Boundary types (True for inclusive, False for exclusive)
    CLOSED = True
    OPEN = False

    def __init__(self, left, lower, upper, right):
        """Create an atomic interval.
        If a bound is set to infinity (regardless of its sign), the 
        corresponding boundary will be exclusive.
        :param left: Boolean indicating if left boundary is inclusive (True) or 
            exclusive (False).
        :param lower: value of the lower bound.
        :param upper: value of the upper bound.
        :param right: Boolean indicating if right boundary is inclusive (True) 
            or exclusive (False).
        """
        self._left = bool(left)
        self._lower = lower
        self._upper = upper
        self._right = bool(right)

        if self.is_empty():
            raise ValueError('Malformed interval ({},{},{},{})'.format(
                left, lower, upper, right
            ))

    @property
    def left(self):
        """Boolean indicating whether the left boundary is inclusive (True) or 
        exclusive (False).
        """
        return self._left

    @property
    def lower(self):
        """Lower bound value.
        """
        return self._lower

    @property
    def upper(self):
        """Upper bound value.
        """
        return self._upper

    @property
    def right(self):
        """Boolean indicating whether the right boundary is inclusive (True) or 
        exclusive (False).
        """
        return self._right

    def is_empty(self):
        """Test interval emptiness.
        :return: True if interval is empty, False otherwise.
        """
        return (
            self._lower > self._upper or
            (self._lower == self._upper \
                and (self._left == self.OPEN or self._right == self.OPEN))
        )

    def replace(self, left=None, lower=None, upper=None, right=None, ignore_inf=True):
        """Create a new interval based on the current one and the provided values.
        Callable can be passed instead of values. In that case, it is called 
        with the current corresponding value except if ignore_inf if set 
        (default) and the corresponding bound is an infinity.
        :param left: (a function of) left boundary.
        :param lower: (a function of) value of the lower bound.
        :param upper: (a function of) value of the upper bound.
        :param right: (a function of) right boundary.
        :param ignore_inf: ignore infinities if functions are provided 
            (default is True).
        :return: an Interval instance
        """
        if callable(left):
            left = left(self._left)
        else:
            left = self._left if left is None else left

        if callable(lower):
            lower = self._lower if ignore_inf else lower(self._lower)
        else:
            lower = self._lower if lower is None else lower

        if callable(upper):
            upper = self._upper if ignore_inf else upper(self._upper)
        else:
            upper = self._upper if upper is None else upper

        if callable(right):
            right = right(self._right)
        else:
            right = self._right if right is None else right

        return type(self)(left, lower, upper, right)

    def overlaps(self, other, adjacent=False):
        """Test if intervals have any overlapping value.
        If 'adjacent' is set to True (default is False), then it returns True 
        for adjacent intervals as well (e.g., [1, 2) and [2, 3], but not 
        [1, 2) and (2, 3]).
        :param other: an atomic interval.
        :param adjacent: set to True to accept adjacent intervals as well.
        :return: True if intervals overlap, False otherwise.
        """
        if not isinstance(other, AtomicInterval):
            raise TypeError('Only AtomicInterval instances are supported.')

        if self._lower < other.lower or \
            (self._lower == other.lower and self._left == self.CLOSED):
            first, second = self, other
        else:
            first, second = other, self

        if first._upper == second._lower:
            if adjacent:
                return first._right == self.CLOSED or second._left == self.CLOSED
            else:
                return first._right == self.CLOSED and second._left == self.CLOSED

        return first._upper > second._lower

    def intersection(self, other):
        """
        Return the intersection of two intervals.
        :param other: an interval.
        :return: the intersection of the intervals.
        """
        return self & other

    def union(self, other):
        """Return the union of two intervals. If the union cannot be represented 
        using a single atomic interval, return an Interval instance (which 
        corresponds to an union of atomic intervals).
        :param other: an interval.
        :return: the union of the intervals.
        """
        return self | other

    def contains(self, item):
        """Test if given item is contained in this interval.
        This method accepts atomic intervals, intervals and arbitrary values.
        :param item: an atomic interval, an interval or any arbitrary value.
        :return: True if given item is contained, False otherwise.
        """
        return item in self

    def __and__(self, other):
        if isinstance(other, AtomicInterval):
            if self._lower == other._lower:
                lower = self._lower
                left = self._left if self._left == self.OPEN else other._left
            else:
                lower = max(self._lower, other._lower)
                left = self._left if lower == self._lower else other._left

            if self._upper == other._upper:
                upper = self._upper
                right = self._right if self._right == self.OPEN else other._right
            else:
                upper = min(self._upper, other._upper)
                right = self._right if upper == self._upper else other._right

            if lower <= upper:
                return AtomicInterval(left, lower, upper, right)
            else:
                # empty set
                return AtomicInterval(self.OPEN, lower, lower, self.OPEN)
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __or__(self, other):
        if isinstance(other, AtomicInterval):
            if self.overlaps(other, adjacent=True):
                if self._lower == other._lower:
                    lower = self._lower
                    left = self._left if self._left == self.CLOSED else other._left
                else:
                    lower = min(self._lower, other._lower)
                    left = self._left if lower == self._lower else other._left

                if self._upper == other._upper:
                    upper = self._upper
                    right = self._right if self._right == self.CLOSED else other._right
                else:
                    upper = max(self._upper, other._upper)
                    right = self._right if upper == self._upper else other._right

                return AtomicInterval(left, lower, upper, right)
            else:
                # return Interval(self, other)
                return ValueError("{} and {} have multi-component union.".format(
                    self, other))
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __contains__(self, item):
        if isinstance(item, AtomicInterval):
            left = item._lower > self._lower or (
                item._lower == self._lower \
                    and (item._left == self._left or self._left == self.CLOSED)
            )
            right = item._upper < self._upper or (
                item._upper == self._upper and \
                    (item._right == self._right or self._right == self.CLOSED)
            )
            return left and right
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __eq__(self, other):
        if isinstance(other, AtomicInterval):
            return (
                    self._left == other._left and
                    self._lower == other._lower and
                    self._upper == other._upper and
                    self._right == other._right
            )
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other  # Required for Python 2

    def __lt__(self, other):
        # true only if disjoint!
        if isinstance(other, AtomicInterval):
            if self._right == self.OPEN:
                return self._upper <= other._lower
            else:
                return self._upper < other._lower or \
                    (self._upper == other._lower and other._left == self.OPEN)
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __gt__(self, other):
        # true only if disjoint!
        if isinstance(other, AtomicInterval):
            if self._left == self.OPEN:
                return self._lower >= other._upper
            else:
                return self._lower > other._upper or \
                    (self._lower == other._upper and other._right == self.OPEN)
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __le__(self, other):
        if isinstance(other, AtomicInterval):
            if self._right == self.OPEN:
                return self._upper <= other._upper
            else:
                return self._upper < other._upper or \
                    (self._upper == other._upper and other._right == self.CLOSED)
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __ge__(self, other):
        if isinstance(other, AtomicInterval):
            if self._left == self.OPEN:
                return self._lower >= other._lower
            else:
                return self._lower > other._lower or \
                    (self._lower == other._lower and other._left == self.CLOSED)
        else:
            raise TypeError('Only AtomicInterval instances are supported.')

    def __hash__(self):
        try:
            return hash(self._lower)
        except TypeError:
            return 0

    def __repr__(self):
        if self.is_empty():
            return '()'
        elif self._lower == self._upper:
            return '[{}]'.format(repr(self._lower))
        else:
            return '{}{},{}{}'.format(
                '[' if self._left == self.CLOSED else '(',
                repr(self._lower),
                repr(self._upper),
                ']' if self._right == self.CLOSED else ')',
            )

    def adjoins_left(self, other):
        # self < other
        return self._right != other._left and self._upper == other._lower
    
    def adjoins_right(self, other):
        # other < self
        return self._left != other._right and self._lower == other._upper

    def adjoins(self, other):
        return self.adjoins_left(other) or self.adjoins_right(other)

    @classmethod
    def span(cls, *args):
        min_ = min(args, key=op.attrgetter('lower'))
        max_ = max(args, key=op.attrgetter('upper'))
        return AtomicInterval(min_.left, min_.lower, max_.upper, max_.right)

    @classmethod
    def contiguous_span(cls, *args):
        ints = sorted(args, key=op.attrgetter('lower'))
        for i in range(0, len(ints) - 1):
            if not ints[i].adjoins_left(ints[i+1]):
                raise ValueError(("Intervals {} and {} not contiguous and "
                    "nonoverlapping.").format(ints[i], ints[i+1]))
        return AtomicInterval(ints[0].left, ints[0].lower, 
            ints[-1].upper, ints[-1].right)

# ===============================================================

class _DateMixin(object):
    """Utility methods for dealing with dates.
    """
    @staticmethod
    def date_format(dt, precision=None):
        """Print date in YYYYMMDDHHMMSS format, with length being set automatically
        from precision. 
        
        Note:
            strftime() is broken for dates prior to 1900 in python < 3.3, see
            https://bugs.python.org/issue1777412 and https://stackoverflow.com/q/10263956.
            For this reason, the workaround implemented here should be used 
            instead.
        """
        tup_ = dt.timetuple()
        str_ = '{0.tm_year:04}{0.tm_mon:02}{0.tm_mday:02}'.format(tup_)
        str_ = str_ + '{0.tm_hour:02}{0.tm_min:02}{0.tm_sec:02}'.format(tup_)
        if precision:
            assert precision > 0 and precision <= 6
            return str_[:2*(precision + 1)]
        else:
            return str_

    @classmethod
    def increment(cls, dt, precision):
        """Return a copy of dt advanced by one time unit as specified by
        the `precision` attribute.
        """
        if precision == 2: # nb: can't handle this with timedeltas
            if dt.month == 12:
                return dt.replace(year=(dt.year + 1), month=1)
            else:
                return dt.replace(month=(dt.month + 1))
        else:
            return cls._inc_dec_common(dt, precision, 1)

    @classmethod
    def decrement(cls, dt, precision):
        """Return a copy of Date moved back by one time unit as specified by
        the `precision` attribute.
        """
        if precision == 2: # nb: can't handle this with timedeltas
            if dt.month == 1:
                return dt.replace(year=(dt.year - 1), month=12)
            else:
                return dt.replace(month=(dt.month - 1))
        else:
            return cls._inc_dec_common(dt, precision, -1)

    @staticmethod
    def _inc_dec_common(dt, precision, delta):
        if precision == 1:
            # nb: can't handle this with timedeltas
            return dt.replace(year=(dt.year + delta)) 
        elif precision == 3:
            td = datetime.timedelta(days = delta)
        elif precision == 4:
            td = datetime.timedelta(hours = delta)
        elif precision == 5:
            td = datetime.timedelta(minutes = delta)
        elif precision == 6:
            td = datetime.timedelta(seconds = delta)
        else:
            # prec == 2 case handled in calling logic
            raise ValueError("Malformed input")
        return dt + td


class DateRange(AtomicInterval, _DateMixin):
    """Class representing a range of variable-precision dates. 

    Note:
        This is defined as a *closed* interval (containing both endpoints). 
        Eg, DateRange('1990-1999') starts at 0:00 on 1 Jan 1990 and 
        ends at 23:59 on 31 Dec 1999.
    """

    _range_sep = '-'

    def __init__(self, start, end=None, precision=None):
        if not end:
            if type(start) is str:
                (start, end) = start.split(self._range_sep)
            elif len(start) == 2:
                (start, end) = start
            else:
                raise ValueError('Bad input ({},{})'.format(start, end))

        dt0, prec0 = self._coerce_to_datetime(start, is_lower=True)
        dt1, prec1 = self._coerce_to_datetime(end, is_lower=False)
        if not (dt0 < dt1):
            print('\tWarning: args to DateRange out of order ({} >= {})'.format(
                start, end
            ))
            dt0, prec0 = self._coerce_to_datetime(end, is_lower=True)
            dt1, prec1 = self._coerce_to_datetime(start, is_lower=False)
        self._left = self.CLOSED
        self._lower = dt0
        self._upper = dt1
        self._right = self.OPEN
        if precision:
            assert precision > 0 and precision <= 6
            self.precision = precision
        else:
            self.precision, _ = self._warning_minmax(prec0, prec1)

    @staticmethod
    def _warning_minmax(*args):
        min_ = min(args)
        max_ = max(args)
        if min_ != max_:
            print('\tWarning: expected precisions {} to be identical'.format(
                args
            ))
        return (min_, max_)

    @staticmethod
    def _coerce_to_datetime(dt, is_lower):
        if isinstance(dt, datetime.datetime):
            return (dt, 6)
        if isinstance(dt, datetime.date):
            return (datetime.datetime.combine(dt, datetime.datetime.min.time()), 3)
        else:
            tmp = Date._coerce_to_self(dt)
            if is_lower:
                return (tmp.lower, tmp.precision)
            else:
                return (tmp.upper, tmp.precision)

    @classmethod
    def _coerce_to_self(cls, item):
        # got to be a better way to write this
        if isinstance(item, cls):
            return item
        else:
            return cls(item)

    @property
    def start(self):
        assert self.precision
        return Date(self.lower, precision=self.precision)

    @property
    def end(self):
        # raise warning?
        assert self.precision
        return Date(self.upper, precision=self.precision)

    @classmethod
    def from_contiguous_span(cls, *args):
        # given a bunch of DateRanges, return interval containing them
        # ONLY IF ranges are continguous and nonoverlapping
        dt_args = [DateRange._coerce_to_self(arg) for arg in args]
        interval = cls.contiguous_span(*dt_args)
        prec, _ = cls._warning_minmax(
            *[dtr.precision for dtr in dt_args]
        )
        return DateRange(interval.lower, interval.upper, precision=prec)

    @classmethod
    def from_date_span(cls, *args):
        # return interval spanning dates
        dt_args = [Date._coerce_to_self(arg) for arg in args]
        interval = cls.span(*dt_args)
        prec, _ = cls._warning_minmax(
            *[dtr.precision for dtr in dt_args]
        )
        return DateRange(interval.lower, interval.upper, precision=prec)

    def format(self, precision=None):
        if not precision:
            precision = self.precision
        # need to decrement upper bound because interval is open there
        return self.date_format(self.lower, precision) + self._range_sep \
            + self.date_format(self.decrement(self.upper, precision), precision)
    __str__ = format

    def __repr__(self):
        if self.precision:
            return "DateRange('{}')".format(self)
        else:
            return "DateRange('{}', precision=None)".format(self)

    def __contains__(self, item):
        """Comparison returning `True` if `item` has any overlap at all with the
        date range.

        This method overrides the `__contains__` method, so, e.g., 
        datetime.date('2019-09-18') in DateRange('2018-2019') will give
        `True`.
        """
        item = self._coerce_to_self(item)
        return super(DateRange, self).overlaps(item, adjacent=False)

    def overlaps(self, item):
        item = self._coerce_to_self(item)
        return super(DateRange, self).overlaps(item, adjacent=False)

    def contains(self, item):
        # strict containments
        item = self._coerce_to_self(item)
        return super(DateRange, self).__contains__(item)
    
    def intersection(self, item, precision=None):
        item = self._coerce_to_self(item)
        if not self.overlaps(item):
            raise ValueError("{} and {} have empty intersection".format(self, item))
        interval = super(DateRange, self).intersection(item)
        if not precision:
            _, precision = self._warning_minmax(self.precision, item.precision)
        return DateRange(interval.lower, interval.upper, precision=precision)

    # for comparsions, coerce to DateRange first & use inherited interval math
    def __lt__(self, other): 
        other = self._coerce_to_self(other)
        return super(DateRange, self).__lt__(other)
    def __le__(self, other):
        other = self._coerce_to_self(other)
        return super(DateRange, self).__le__(other)
    def __gt__(self, other):
        other = self._coerce_to_self(other)
        return super(DateRange, self).__gt__(other)
    def __ge__(self, other):
        other = self._coerce_to_self(other)
        return super(DateRange, self).__ge__(other)


class Date(DateRange):
    """Define a date with variable level precision.

    Note: 
        Date objects are mapped to datetimes representing the start of the 
        interval implied by their precision, eg. DateTime('2000-05') maps to 
        0:00 on 1 May 2000.
    """

    _datetime_attrs = ('year','month','day','hour','minute','second')

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], (datetime.date, datetime.datetime)):
            dt_args = self._parse_datetime(args[0])
            single_arg_flag = True
        elif type(args[0]) is str:
            dt_args = self._parse_input_string(args[0])
            single_arg_flag = True
        else:
            dt_args = tuple(args)
            single_arg_flag = False

        if 'precision' in kwargs:
            prec = kwargs['precision']
        elif len(args) == 2 and single_arg_flag:
            prec = args[1]
        else:
            prec = len(dt_args)

        assert prec <= 6 # other values not supported
        for i in range(prec):
            setattr(self, self._datetime_attrs[i], dt_args[i])
        if prec == 1:
            dt_args = (dt_args[0], 1, 1) # missing month & day
        elif prec == 2:
            dt_args = (dt_args[0], dt_args[1], 1) # missing day

        dt = datetime.datetime(*dt_args) 
        self._left = self.CLOSED
        self._lower = dt
        self._upper = self.increment(dt, prec)
        self._right = self.OPEN
        self.precision = prec

    @classmethod
    def _parse_datetime(cls, dt):
        # new obj from coercing a datetime.date or datetime.datetime.
        # A bit hacky, but no other portable way to copy the input datetime 
        # using one of its class methods in py2.7.
        ans = []
        for attr in cls._datetime_attrs:
            if hasattr(dt, attr):
                ans.append(getattr(dt, attr))
            else:
                break
        return tuple(ans)

    @classmethod
    def _parse_input_string(cls, s):
        """Parse date strings in `YYYY-MM-DD` or `YYYYMMDDHH` formats.
        """
        if '-' in s:
            return tuple([int(ss) for ss in s.split('-')])
        ans = [int(s[0:4])]
        for i in range(4, len(s), 2):
            ans.append(int(s[i:(i+2)]))
        return tuple(ans)
    
    def format(self, precision=None):
        if precision:
            return self.date_format(self.lower, precision)
        else:
            return self.date_format(self.lower, self.precision)
    __str__ = format

    def __repr__(self):
        return "Date('{}')".format(self)

    def isoformat(self):
        # same remarks on strftime/timetuple apply here
        tup_ = self.lower.timetuple()
        str_ = '{0.tm_year:04}-{0.tm_mon:02}-{0.tm_mday:02} '.format(tup_)
        return str_ + '{0.tm_hour:02}:{0.tm_min:02}:{0.tm_sec:02}'.format(tup_)

    def _tuple_compare(self, other, func):
        if not isinstance(other, Date):
            other = Date(other, precision=self.precision)
        # only compare most signifcant fields of tuple representation
        return func(
            self.lower.timetuple()[:self.precision],
            other.lower.timetuple()[:self.precision]
        )
   
    def __lt__(self, other): 
        return self._tuple_compare(other, op.lt)

    def __gt__(self, other):
        return self._tuple_compare(other, op.gt)

    def __le__(self, other):
        return self._tuple_compare(other, op.le)

    def __ge__(self, other):
        return self._tuple_compare(other, op.ge)

    def __eq__(self, other):
        """Overload datetime.datetime's __eq__. Require precision to match as
        well as date, but *only up to stated precision*, eg Date(2019,5) will == 
        datetime.datetime(2019,05,18).
        """
        return self._tuple_compare(other, op.eq)

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof


class DateFrequency(datetime.timedelta):
    """Class representing a date frequency or period.

    Note:
        Period lengths are *not* defined accurately, eg. a year is taken as
        365 days and a month is taken as 30 days. 
    """
    # define __new__, not __init__, because timedelta is immutable
    def __new__(cls, quantity, unit=None):
        if isinstance(quantity, str) and (unit is None):
            (kwargs, attrs) = cls._parse_input_string(None, quantity)
        elif (type(quantity) is not int) or not isinstance(unit, str):
            raise ValueError("Malformed input")
        else:
            (kwargs, attrs) = cls._parse_input_string(quantity, unit)
        obj = super(DateFrequency, cls).__new__(cls, **kwargs)
        for key, val in attrs.iteritems():
            obj.__setattr__(key, val)
        return obj

    @classmethod
    def _parse_input_string(cls, quantity, unit):
        # don't overwrite input
        q = quantity
        s = unit.lower()
        if q is None:
            match = re.match(r"(?P<quantity>\d+)[ _]*(?P<unit>[a-zA-Z]+)", s)
            if match:
                q = int(match.group('quantity'))
                s = match.group('unit')
            else:
                q = 1
        
        if s in ['fx', 'static']:
            q = 0
            s = 'fx'
        elif s in ['yearly', 'year', 'years', 'yr', 'y', 'annually', 'annual', 'ann']:
            s = 'yr'
        elif s in ['seasonally', 'seasonal', 'seasons', 'season', 'se']:      
            s = 'season'
        elif s in ['monthly', 'month', 'months', 'mon', 'mo']:      
            s = 'mo'
        elif s in ['weekly', 'weeks', 'week', 'wk', 'w']:
            s = 'wk'
        elif s in ['daily', 'day', 'days', 'dy', 'd', 'diurnal', 'diurnally']:
            s = 'day'
        elif s in ['hourly', 'hour', 'hours', 'hr', 'h']:
            s = 'hr'
        elif s in ['minutes', 'minute', 'min']:
            s = 'min'
        else:
            raise ValueError("Malformed input {} {}".format(quantity, unit))
        return (cls._get_timedelta_kwargs(q, s), {'quantity': q, 'unit': s})

    @classmethod
    def _get_timedelta_kwargs(cls, q, s):
        if s == 'fx':
            return {'seconds': 0}
        elif s == 'yr':
            return {'days': 365 * q}
        elif s == 'season':
            return {'days': 91 * q}
        elif s == 'mo':
            return {'days': 30 * q}
        elif s == 'wk':
            return {'weeks': q}
        elif s == 'day':
            return {'days': q}
        elif s == 'hr':
            return {'hours': q}
        elif s == 'min':
            return {'minutes': q}
        else:
            raise ValueError("Malformed input {} {}".format(q, s))

    def format(self):
        # pylint: disable=maybe-no-member
        # conversion? only hr and yr used
        return "{}{}".format(self.quantity, self.unit)
    __str__ = format

    def format_local(self):
        # pylint: disable=maybe-no-member
        if self.unit == 'hr':
            return self.format()
        else:
            assert self.quantity == 1
            _local_dict = {
                'mo': 'mon',
                'day': 'day',
            }
            return _local_dict[self.unit]

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self)

    def __eq__(self, other):
        # pylint: disable=maybe-no-member
        # Note: only want to match labels, don't want '24hr' == '1day'
        if isinstance(other, DateFrequency):
            return (self.quantity == other.quantity) and (self.unit == other.unit)
        else:
            return super(DateFrequency, self).__eq__(other)

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof
