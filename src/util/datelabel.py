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
import abc
import copy
import enum
import re
import datetime
import operator as op
import warnings
from src import util

import logging
_log = logging.getLogger(__name__)

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

        Args:
            left: Boolean indicating if left boundary is inclusive (True) or
                exclusive (False).
            lower: value of the lower bound.
            upper: value of the upper bound.
            right: Boolean indicating if right boundary is inclusive (True)
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

        Args:
            left: (a function of) left boundary.
            lower: (a function of) value of the lower bound.
            upper: (a function of) value of the upper bound.
            right: (a function of) right boundary.
            ignore_inf: ignore infinities if functions are provided
                (default is True).

        Returns: an Interval instance
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
        for i in list(range(0, len(ints) - 1)):
            if not ints[i].adjoins_left(ints[i+1]):
                raise ValueError(("Intervals {} and {} not contiguous and "
                    "nonoverlapping.").format(ints[i], ints[i+1]))
        return AtomicInterval(ints[0].left, ints[0].lower,
            ints[-1].upper, ints[-1].right)

# ===============================================================

class DatePrecision(enum.IntEnum):
    """:py:class:`~enum.IntEnum` to encode the recognized levels of precision
    for date intervals. For example, Date('200012') has DatePrecision.MONTH since
    the length of the corresponding interval is a month.
    """
    STATIC = -1
    YEAR = 1
    MONTH = 2
    DAY = 3
    HOUR = 4
    MINUTE = 5
    SECOND = 6

class _DateMixin(object):
    """Utility methods for dealing with dates.
    """
    @staticmethod
    def date_format(dt, precision=None):
        """Print date in YYYYMMDDHHMMSS format, with length being set automatically
        from precision.

        Note:
            strftime() is broken for dates prior to 1900 in python < 3.3, see
            `<https://bugs.python.org/issue1777412>`__ and
            `<https://stackoverflow.com/q/10263956>`__.
            For this reason, the workaround implemented here should be used
            instead.
        """
        tup_ = dt.timetuple()
        str_ = '{0.tm_year:04}{0.tm_mon:02}{0.tm_mday:02}'.format(tup_)
        str_ = str_ + '{0.tm_hour:02}{0.tm_min:02}{0.tm_sec:02}'.format(tup_)
        if precision:
            return str_[:2*(precision + 1)]
        else:
            return str_

    @classmethod
    def increment(cls, dt, precision):
        """Return a copy of dt advanced by one time unit as specified by
        the `precision` attribute.
        """
        if precision == DatePrecision.MONTH: # can't handle this with timedeltas
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
        if precision == DatePrecision.MONTH: # can't handle this with timedeltas
            if dt.month == 1:
                return dt.replace(year=(dt.year - 1), month=12)
            else:
                return dt.replace(month=(dt.month - 1))
        else:
            return cls._inc_dec_common(dt, precision, -1)

    @staticmethod
    def _inc_dec_common(dt, precision, delta):
        if precision == DatePrecision.STATIC:
            if delta == 1:
                # assert dt == datetime.datetime.min
                return datetime.datetime.max
            elif delta == -1:
                # assert dt == datetime.datetime.max
                return datetime.datetime.min
        if precision == DatePrecision.YEAR:
            # nb: can't handle this with timedeltas
            return dt.replace(year=(dt.year + delta))
        elif precision == DatePrecision.DAY:
            td = datetime.timedelta(days = delta)
        elif precision == DatePrecision.HOUR:
            td = datetime.timedelta(hours = delta)
        elif precision == DatePrecision.MINUTE:
            td = datetime.timedelta(minutes = delta)
        elif precision == DatePrecision.SECOND:
            td = datetime.timedelta(seconds = delta)
        else:
            # prec == 2 case handled in calling logic
            raise ValueError(f"Malformed input: {repr(dt)} prec={precision} delta={delta}")
        return dt + td


class DateRange(AtomicInterval, _DateMixin):
    """Class representing a range of variable-precision dates.

    Note:
        This is defined as a *closed* interval (containing both endpoints).
        Eg, DateRange('1990-1999') starts at 0:00 on 1 Jan 1990 and
        ends at 23:59 on 31 Dec 1999.
    """
    _range_sep = '-'

    def __init__(self, start, end=None, precision=None, log=_log):
        "Init method for DateRange."
        if not end:
            if isinstance(start, str):
                (start, end) = start.split(self._range_sep)
            elif len(start) == 2:
                (start, end) = start
            else:
                raise ValueError('Bad input ({},{})'.format(start, end))

        dt0, prec0 = self._coerce_to_datetime(start, is_lower=True)
        dt1, prec1 = self._coerce_to_datetime(end, is_lower=False)
        if not (dt0 < dt1):
            log.warning('Args to DateRange out of order (%s >= %s)',
                start, end)
            dt0, prec0 = self._coerce_to_datetime(end, is_lower=True)
            dt1, prec1 = self._coerce_to_datetime(start, is_lower=False)
        # call AtomicInterval's init
        super(DateRange, self).__init__(self.CLOSED, dt0, dt1, self.OPEN)
        if precision is not None:
            if not isinstance(precision, DatePrecision):
                precision = (DatePrecision)
            if precision > prec0 or precision > prec1:
                raise util.MixedDatePrecisionException((
                    "Attempted to init DateRange with manual prec {}, but date "
                    "arguments have precs {}, {}").format(precision, prec0, prec1)
                )
            self.precision = precision
        else:
            self.precision, _ = self._precision_check(prec0, prec1)

    @property
    def is_static(self):
        """Property indicating time-independent data (eg, 'fx' in CMIP6 DRS.)
        """
        return False

    @staticmethod
    def _precision_check(*args):
        min_ = min(args)
        max_ = max(args)
        if min_ == DatePrecision.STATIC:
            raise util.FXDateException(
                func_name='_precision_check', msg='Recieved {}'.format(args)
            )
        if min_ != max_:
            warnings.warn('Expected precisions {} to be identical'.format(
                args
            ))
        return (min_, max_)

    @staticmethod
    def _coerce_to_datetime(dt, is_lower):
        if isinstance(dt, datetime.datetime):
            # datetime specifies time to within second
            return (dt, DatePrecision.SECOND)
        if isinstance(dt, datetime.date):
            # date specifies time to within day
            return (
                datetime.datetime.combine(dt, datetime.datetime.min.time()),
                DatePrecision.DAY
            )
        else:
            tmp = Date._coerce_to_self(dt)
            if is_lower:
                return (tmp.lower, tmp.precision)
            else:
                return (tmp.upper, tmp.precision)

    @classmethod
    def _coerce_to_self(cls, item, precision=None):
        # hacky; should to be a better way to write this
        if isinstance(item, cls) or getattr(item, 'is_static', False):
            if precision is not None:
                item.precision = precision
            return item
        else:
            try:
                if precision is not None:
                    return cls(item, precision=precision)
                else:
                    return cls(item)
            except Exception:
                raise TypeError((f"Comparison not supported between {cls.__name__} "
                    f"and {type(item).__name__} ({repr(item)})."))

    @property
    def start_datetime(self):
        return self.lower

    @property
    def start(self):
        assert self.precision
        return Date(self.start_datetime, precision=self.precision)

    @property
    def end_datetime(self):
        # don't decrement here, even though interval is closed, because of how
        # adjoins_left and adjoins_right are implemented
        return self.upper

    @property
    def end(self):
        # need to decrement because interval is closed, but Date() assumes its
        # input is the start of the interval (set by precision)
        assert self.precision
        return Date(
            self.decrement(self.end_datetime, self.precision + 1),
            precision=self.precision
        )

    @classmethod
    def from_contiguous_span(cls, *args):
        """Given multiple DateRanges, return interval containing them
        ONLY IF ranges are continguous and nonoverlapping.
        """
        if len(args) == 1 and isinstance(args[0], DateRange):
            return args[0]
        dt_args = [DateRange._coerce_to_self(arg) for arg in args]
        prec, _ = cls._precision_check(*[dtr.precision for dtr in dt_args])
        interval = cls.contiguous_span(*dt_args)
        return DateRange(interval.lower, interval.upper, precision=prec)

    @classmethod
    def from_date_span(cls, *args):
        """Return a DateRange coresponding to the interval containing a set of
        Dates. Differs from :meth:`from_contiguous_span` in that we don't expect
        intervals to be contiguous.
        """
        dt_args = [Date._coerce_to_self(arg) for arg in args]
        prec, _ = cls._precision_check(*[dtr.precision for dtr in dt_args])
        interval = cls.span(*dt_args)
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
        """Override :meth:`AtomicInterval.__contains__` to handle differences
        in datelabel precision. Finite precision means that the interval endpoints
        are ranges, not points (which is why :class:`Date` inherits from
        :class:`DateRange` and not vice-versa). We replace strict equality of
        endpoints (==) with appropriate conditions on the overlap of these
        ranges.
        """
        item = self._coerce_to_self(item)
        left_gt = item._lower > self._lower
        left_eq = self.start.overlaps(item.start) \
            and (item._left == self._left or self._left == self.CLOSED)
        right_lt = item._upper < self._upper
        right_eq = self.end.overlaps(item.end) \
            and (item._right == self._right or self._right == self.CLOSED)
        return (left_gt or left_eq) and (right_lt or right_eq)
    contains = __contains__

    def overlaps(self, item):
        item = self._coerce_to_self(item)
        return super(DateRange, self).overlaps(item, adjacent=False)

    def intersection(self, item, precision=None):
        item = self._coerce_to_self(item)
        if not self.overlaps(item):
            raise ValueError("{} and {} have empty intersection".format(self, item))
        interval = super(DateRange, self).intersection(item)
        if not precision:
            _, precision = self._precision_check(self.precision, item.precision)
        return DateRange(interval.lower, interval.upper, precision=precision)

    # for comparsions, coerce to DateRange first & use inherited interval math
    def _date_range_compare_common(self, other, func_name):
        if self.is_static or getattr(other, 'is_static', False):
            raise util.FXDateException(func_name='_date_range_compare_common')
        _other = self._coerce_to_self(other)
        _meth = getattr(super(DateRange, self), func_name)
        return _meth(_other)

    def __lt__(self, other):
        return self._date_range_compare_common(other, '__lt__')
    def __le__(self, other):
        return self._date_range_compare_common(other, '__le__')
    def __gt__(self, other):
        return self._date_range_compare_common(other, '__gt__')
    def __ge__(self, other):
        return self._date_range_compare_common(other, '__ge__')
    def __eq__(self, other):
        # Don't want check for static date in this case
        try:
            other = self._coerce_to_self(other)
        except TypeError:
            return False
        prec_other = getattr(other, 'precision', -1)
        return (super(DateRange, self).__eq__(other)) \
            and (self.precision == prec_other)

    def __hash__(self):
        return hash((self.__class__, self.lower, self.upper, self.precision))

class Date(DateRange):
    """Define a date with variable level precision.

    Note:
        Date objects are mapped to datetimes representing the start of the
        interval implied by their precision, eg. DateTime('2000-05') maps to
        0:00 on 1 May 2000.
    """

    _datetime_attrs = ('year','month','day','hour','minute','second')

    def __init__(self, *args, **kwargs):
        "Init method for Date."
        if isinstance(args[0], (datetime.date, datetime.datetime)):
            dt_args = self._parse_datetime(args[0])
            single_arg_flag = True
        elif isinstance(args[0], str):
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
        if prec is not None and not isinstance(prec, DatePrecision):
            prec = DatePrecision(prec)

        assert prec <= 6 # other values not supported
        for i in list(range(prec)):
            setattr(self, self._datetime_attrs[i], dt_args[i])
        if prec == 1:
            dt_args = (dt_args[0], 1, 1) # missing month & day
        elif prec == 2:
            dt_args = (dt_args[0], dt_args[1], 1) # missing day

        dt = datetime.datetime(*dt_args)
        # call DateRange's init
        super(Date, self).__init__(dt, self.increment(dt, prec), precision=prec)

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
        for i in list(range(4, len(s), 2)):
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
        if self.is_static or getattr(other, 'is_static', False):
            if func == op.eq:
                # True only if both values are FXDates
                return (self.is_static and getattr(other, 'is_static', False))
            else:
                raise util.FXDateException(func_name='_tuple_compare')
        if not isinstance(other, self.__class__):
            other = self.__class__._coerce_to_self(other, precision=self.precision)
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
        try:
            return self._tuple_compare(other, op.eq)
        except TypeError:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

    def __hash__(self):
        return hash((self.__class__, self.lower, self.upper, self.precision))

class StaticTimeDependenceBase(object):
    """Dummy class to label sentinel objects for use in describing static data
    with no time dependence.
    """
    @property
    def is_static(self):
        """Property indicating time-independent data (eg, 'fx' in CMIP6 DRS.)
        """
        return True

    @classmethod
    def _coerce_to_self(cls, item):
        # got to be a better way to write this
        return item

    def format(self, precision=None):
        return "<N/A>"
    isoformat = format
    __str__ = format

    @staticmethod
    def date_format(dt, precision=None):
        return "<N/A>"

class _FXDateMin(StaticTimeDependenceBase, Date):
    def __init__(self):
        # call DateRange's init
        super(_FXDateMin, self).__init__(
            datetime.datetime.min, precision=DatePrecision.STATIC
        )
        self.precision = DatePrecision.STATIC

    def __repr__(self):
        return "_FXDate()"

    @property
    def start(self):
        return self.lower

    @property
    def end(self):
        return self.lower
FXDateMin = _FXDateMin()

class _FXDateMax(StaticTimeDependenceBase, Date):
    def __init__(self):
        # call DateRange's init
        super(_FXDateMax, self).__init__(
            datetime.datetime.max, precision=DatePrecision.STATIC
        )
        self.precision = DatePrecision.STATIC

    def __repr__(self):
        return "_FXDateMax()"

    @property
    def start(self):
        return self.upper

    @property
    def end(self):
        return self.upper
FXDateMax = _FXDateMax()

class _FXDateRange(StaticTimeDependenceBase, DateRange):
    """Singleton placeholder/sentinel object for use in describing static data
    with no time dependence.
    """
    def __init__(self):
        # call DateRange's init
        super(_FXDateRange, self).__init__(datetime.datetime.min, datetime.datetime.max)
        self.precision = DatePrecision.STATIC

    def __repr__(self):
        return "_FXDateRange()"

    @property
    def start(self):
        return FXDateMin

    @property
    def end(self):
        return FXDateMax
FXDateRange = _FXDateRange()

class DateFrequency(datetime.timedelta):
    """Class representing a date frequency or period.

    .. warning::
       Period lengths are *not* defined accurately, eg. a year is taken as
       365 days and a month is taken as 30 days.
    """
    # define __new__, not __init__, because timedelta is immutable
    def __new__(cls, quantity, unit=None):
        if isinstance(quantity, str) and (unit is None):
            (kwargs, attrs) = cls._parse_input_string(None, quantity)
        elif not isinstance(quantity, int) or not isinstance(unit, str):
            raise ValueError(f"Malformed input: '{quantity}' '{unit}'")
        else:
            (kwargs, attrs) = cls._parse_input_string(quantity, unit)
        obj = super(DateFrequency, cls).__new__(cls, **kwargs)
        obj.quantity = None
        obj.unit = None
        # actually set attributes, as well as any others child classes may add
        for key, val in attrs.items():
            obj.__setattr__(key, val)
        return obj

    @property
    def is_static(self):
        """Property indicating time-independent data (eg, 'fx' in CMIP6 DRS.)
        """
        return (self.quantity == 0 and self.unit == "fx")

    @classmethod
    def from_struct(cls, str_):
        """Workaround for object creation, using the method mdtf_dataclass is
        looking for.
        """
        return cls.__new__(cls, str_, None)

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
            # internally set to maximum representable timedelta, for purposes of comparison
            tmp = datetime.timedelta.max
            return {'days': tmp.days, 'seconds': tmp.seconds,
                'microseconds': tmp.microseconds
            }
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
        # conversion? only hr and yr used
        if self.unit == 'fx':
            return 'fx'
        else:
            return "{}{}".format(self.quantity, self.unit)
    __str__ = format

    def format_local(self):
        """Format frequency as used in framework's local directory hierarchy
        (defined in :meth:`src.data_manager.DataManager.dest_path`.)
        """
        if self.quantity == 1:
            if self.unit == 'mo':
                return 'mon'
            elif self.unit == 'day':
                return 'day'
            else:
                return self.format()
        else:
            return self.format()

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self)

    def __eq__(self, other):
        # Note: only want to match labels, don't want '24hr' == '1day'
        if isinstance(other, DateFrequency):
            return (self.quantity == other.quantity) and (self.unit == other.unit)
        else:
            return super(DateFrequency, self).__eq__(other)

    def __ne__(self, other):
        return (not self.__eq__(other)) # more foolproof

    def __copy__(self):
        return self.__class__.__new__(self.__class__, self.quantity, unit=self.unit)

    def __deepcopy__(self, memo):
        return self.__class__.__new__(self.__class__,
            copy.deepcopy(self.quantity, memo), unit=copy.deepcopy(self.unit, memo)
        )

    def __hash__(self):
        return hash((self.__class__, self.quantity, self.unit))

class _FXDateFrequency(DateFrequency, StaticTimeDependenceBase):
    """Singleton placeholder/sentinel object for use in describing static data
    with no time dependence.
    """
    # define __new__, not __init__, because timedelta is immutable
    def __new__(cls):
        return super(_FXDateFrequency, cls).__new__(cls, 'static')

    @property
    def is_static(self):
        return True

    def __copy__(self):
        return self.__class__.__new__(self.__class__)

    def __deepcopy__(self, memo):
        return self.__class__.__new__(self.__class__)

FXDateFrequency = _FXDateFrequency()

class AbstractDateRange(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMDimension` objects.
    """
    pass

class AbstractDate(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMDimension` objects.
    """
    pass

class AbstractDateFrequency(abc.ABC):
    """Defines interface (set of attributes) for :class:`DMDimension` objects.
    """
    pass


# Use the "register" method, instead of inheritance, to identify the
# DM*Dimension classes as implementations of AbstractDMDimension, because
# Python dataclass fields aren't recognized as implementing an abc.abstractmethod.
AbstractDateRange.register(DateRange)
AbstractDateRange.register(_FXDateRange)
AbstractDate.register(Date)
AbstractDate.register(_FXDateMin)
AbstractDate.register(_FXDateMax)
AbstractDateFrequency.register(DateFrequency)
AbstractDateFrequency.register(_FXDateFrequency)
