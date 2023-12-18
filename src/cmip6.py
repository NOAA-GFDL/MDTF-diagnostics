"""Code to parse CMIP6 controlled vocabularies and elements of the CMIP6 DRS.

Specifications for the above were taken from the CMIP6 `planning document
<http://goo.gl/v1drZl>`__. This was accessed at `<http://goo.gl/v1drZl>`__ -- we
aren't aware of a permanent URL for this information.

The CMIP6 controlled vocabularies (lists of registered MIPs, modeling centers, etc.)
are derived from data in the
`PCMDI/cmip6-cmor-tables <https://github.com/PCMDI/cmip6-cmor-tables>`__
repo, which is included as a git subtree under ``/data``.

.. warning::
   Functionality here has been added as needed for the project and is incomplete.
   For example, parsing subexperiments is not supported.
"""
import os
import re
import dataclasses as dc
from src import util

import logging
_log = logging.getLogger(__name__)


class CMIP6_CVs(metaclass=util.Singleton):
    """Interface for looking up information from the CMIP6 controlled vocabulary
    (CV) file.

    Lookups are implemented in an ad-hoc way with :class:`util.MultiMap`; a
    more robust solution would use :py:mod:`sqlite`.
    """
    def __init__(self, unittest=False):
        """Constructor. Only executed once, since this is a :class:`~src.util.Singleton`.
        Reads and parses data in CMIP6_CV.json.
        """
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            file_ = 'dummy_filename'
        else:
            paths = util.PathManager()
            file_ = os.path.join(paths.CODE_ROOT, 'data',
                                 'cmip6-cmor-tables', 'Tables', 'CMIP6_CV.json')
        self._contents = util.read_json(file_, log=_log)
        self._contents = self._contents['CV']
        for k in ['product', 'version_metadata', 'required_global_attributes',
                  'further_info_url', 'Conventions', 'license']:
            # remove unnecessary information
            del self._contents[k]

        # munge table_ids
        self._contents['table_id'] = dict.fromkeys(self._contents['table_id'])
        for tbl in self._contents['table_id']:
            self._contents['table_id'][tbl] = dc.asdict(CMIP6_MIPTable(tbl))

        self.cv = dict()
        self._lookups = dict()

    def _make_cv(self):
        """Populate the *cv* attribute of :class:`CMIP6_CVs` with the tables
        read in during __init__().

        Do this on-demand rather than in __init__, in case this information isn't
        needed for this run of the framework.
        """
        if self.cv:
            return
        for k in self._contents:
            self.cv[k] = util.to_iter(self._contents[k])

    def is_in_cv(self, category, items):
        """Determine if *items* take values that are valid for the CV category
        *category*.

        Args:
            category (str): The CV category to use to validate values.
            items (str or list of str): Entries whose validity we'd like to
                check.

        Returns:
            Boolean or list of booleans, corresponding to the validity of
            the entries in *items*.
        """
        self._make_cv()
        if category not in self.cv:
            raise KeyError(f"Unrecognized CMIP6 CV category {category}.")
        if util.is_iterable(items):
            return [(item in self.cv[category]) for item in items]
        else:
            return items in self.cv[category]

    def get_lookup(self, source, dest):
        """Find the appropriate lookup table to convert values in *source* (keys)
        to values in *dest* (values), generating it if necessary.

        Args:
            source (str): The CV category to use for the keys.
            dest (str): The CV category to use for the values.

        Returns:
            :class:`util.MultiMap` providing a dict-like lookup interface,
            ie dest_value = d[source_key].
        """
        if (source, dest) in self._lookups:
            return self._lookups[(source, dest)]
        elif (dest, source) in self._lookups:
            return self._lookups[(dest, source)].inverse()
        elif source in self._contents:
            k = list(self._contents[source])[0]
            if dest not in self._contents[source][k]:
                raise KeyError(f"Can't find {dest} in attributes for {source}.")
            mm = util.MultiMap()
            for k in self._contents[source]:
                mm[k].update(
                    util.to_iter(self._contents[source][k][dest], set)
                )
            self._lookups[(source, dest)] = mm
            return mm
        elif dest in self._contents:
            return self._lookups[(dest, source)].inverse()
        else:
            raise KeyError(f"Neither {source} or {dest} in CV table list.")

    def lookup(self, source_items, source, dest):
        """Look up the corresponding *dest* values for *source_items* (keys).

        Args:
            source_items (str or list): One or more keys.
            source (str): The CV category that the items in *source_items*
                belong to.
            dest (str): The CV category we'd like the corresponding values for.

        Returns:
            List of *dest* values corresponding to each entry in *source_items*.
        """
        _lookup = self.get_lookup(source, dest)
        if util.is_iterable(source_items):
            return [util.from_iter(_lookup[item]) for item in source_items]
        else:
            return util.from_iter(_lookup[source_items])

    def lookup_single(self, source_item, source, dest):
        """The same as :meth:`lookup`, but perform lookup for a single
        *source_item*, and raise KeyError if the number of values returned is
        != 1.
        """
        _lookup = self.get_lookup(source, dest)
        dest_items = _lookup[source_item]
        if len(dest_items) != 1:
            raise KeyError(f"Non-unique lookup for {dest} from {source}='{source_item}'.")
        return dest_items.pop()

    # TODO: Represent contents as pandas DataFrame, allow pseudo-SQL multi-column
    # lookups

    # ----------------------------------

    def table_id_from_freq(self, frequency):
        """Specialized lookup to determine which MIP tables use data at the
        requested *frequency*.

        Should really be handled as a special case of :meth:`lookup`.

        Args:
            frequency (:class:`CMIP6DateFrequency`): DateFrequency

        Returns:
            List of MIP table ``table_id`` names, if any, that use data at
            the given *frequency*.
        """
        self._make_cv()
        assert 'table_id' in self.cv
        d = self.cv['table_id'] # abbreviate
        return [tbl for tbl, tbl_d in d.items()
                if tbl_d.get('frequency', None) == frequency]


class CMIP6DateFrequency(util.DateFrequency):
    """Subclass of :class:`~src.util.datelabel.DateFrequency` to parse data frequency
    information as encoded in MIP tables, DRS filenames, etc.

    Extends DateFrequency in that this records if the data is a climatological
    average, although this information is not currently used.

    Reference: CMIP6 `planning document <http://goo.gl/v1drZl>`__ page 16.
    """
    _precision_lookup = {
        'fx': 0, 'yr': 1, 'mo': 2, 'day': 3,
        'hr': 5,  # includes minutes
        'min': 6,  # = subhr, minutes and seconds
        }
    _regex = re.compile(r"""
        ^
        (?P<quantity>(1|3|6)?)
        (?P<unit>[a-z]*?)
        (?P<avg>(C|CM|Pt)?)
        $
    """, re.VERBOSE)

    @classmethod
    def _parse_input_string(cls, quantity, unit):
        if not quantity:
            match = re.match(cls._regex, unit)
        else:
            match = re.match(cls._regex, str(quantity)+unit)
        if match:
            md = match.groupdict()
            if md['unit'] == 'dec':
                md['quantity'] = 10
                md['unit'] = 'yr'
            elif md['unit'] == 'mon':
                md['unit'] = 'mo'
            elif md['unit'] == 'subhr':
                # questionable assumption
                md['quantity'] = 15
                md['unit'] = 'min'
            elif md['unit'] == 'fx':
                md['quantity'] = 0
                md['unit'] = 'fx'

            if md['quantity'] == '' or md['quantity'] is None:
                md['quantity'] = 1
            else:
                md['quantity'] = int(md['quantity'])

            if not md['avg']:
                md['avg'] = 'Mean'
            elif md['avg'] in ['C', 'CM']:
                md['avg'] = 'Clim'

            md['precision'] = cls._precision_lookup[md['unit']]
            return cls._get_timedelta_kwargs(md['quantity'], md['unit']), md
        else:
            raise ValueError("Malformed input {} {}".format(quantity, unit))

    def format(self):
        """Return string representation of the object, as used in the
        CMIP6 DRS.
        """
        # pylint: disable=maybe-no-member
        if self.unit == 'fx':
            return 'fx'
        elif self.unit == 'yr' and self.quantity == 10:
            return 'dec'
        elif self.unit == 'mo':
            s = 'mon'
        elif self.unit == 'hr':
            s = str(self.quantity) + self.unit
        elif self.unit == 'min':
            s = 'subhr'
        else:
            s = self.unit
        if self.avg == 'Mean':
            return s
        elif self.avg == 'Pt':
            return s + self.avg
        elif self.avg == 'Clim':
            if self.unit == 'hr':
                return s + 'CM'
            else:
                return s + 'C'
        else:
            raise ValueError("Malformed data {} {}".format(self.quantity, self.unit))
    __str__ = format

    def __copy__(self):
        return self.__class__(self.format())

    def __deepcopy__(self, memo):
        return self.__class__(self.format())

# ===========================================================================


variant_label_regex = util.RegexPattern(r"""
        (r(?P<realization_index>\d+))?    # (optional) int prefixed with 'r'
        (i(?P<initialization_index>\d+))? # (optional) int prefixed with 'i'
        (p(?P<physics_index>\d+))?        # (optional) int prefixed with 'p'
        (f(?P<forcing_index>\d+))?        # (optional) int prefixed with 'f'
    """,
                                        input_field="variant_label"
                                        )


@util.regex_dataclass(variant_label_regex)
class CMIP6_VariantLabel:
    """:class:`~src.util.regex_dataclass` which represents and parses the CMIP6
    DRS variant label identifier string (e.g., ``r1i1p1f1``.)

    References: `<https://earthsystemcog.org/projects/wip/mip_table_about>`__,
    although this doesn't document all cases used in CMIP6. See also note 8 on
    page 9 of the CMIP6 `planning document <http://goo.gl/v1drZl>`__.
    """
    variant_label: str = util.MANDATORY
    """Input to :meth:`~CMIP6_VariantLabel.from_string`. Complete variant label
    identifier string (e.g., 'r1i1p1f1'.)"""
    realization_index: int = None
    """Realization index (integer following the letter ``r``.)"""
    initialization_index: int = None
    """Initialization index (integer following the letter ``i``.)"""
    physics_index: int = None
    """Physics index (integer following the letter ``p``.)"""
    forcing_index: int = None
    """Forcing index (integer following the letter ``f``.)"""


mip_table_regex = util.RegexPattern(r"""
        # ^ # start of line
        (?P<table_prefix>(A|CF|E|I|AER|O|L|LI|SI)?)
        # maybe a digit, followed by as few lowercase letters as possible:
        (?P<table_freq>\d?[a-z]*?)
        (?P<table_suffix>(ClimMon|Lev|Plev|Ant|Gre)?)
        (?P<table_qualifier>(Pt|Z|Off)?)
        # $ # end of line - necessary for lazy capture to work
    """,
                                    input_field="table_id"
                                    )


@util.regex_dataclass(mip_table_regex)
class CMIP6_MIPTable:
    """:class:`~src.util.regex_dataclass` which represents and parses the MIP
    table identifier string.

    Reference: `<https://earthsystemcog.org/projects/wip/mip_table_about>`__,
    although this doesn't document all cases used in CMIP6.
    """
    table_id: str = util.MANDATORY
    """Input to :meth:`~CMIP6_MIPTable.from_string`. ``table_id`` string as used
    in the DRS."""
    table_prefix: str = ""
    """Substring of ``table_id`` specifying modeling realm."""
    table_freq: dc.InitVar = ""
    """Substring of ``table_id`` specifying sampling frequency."""
    table_suffix: str = ""
    """Substring of ``table_id`` specifying sampling/averaging methods."""
    table_qualifier: str = ""
    """Substring of ``table_id`` specifying sampling/averaging methods."""
    frequency: CMIP6DateFrequency = dc.field(init=False)
    """Frequency at which data for the table is sampled. From ``table_freq``."""
    spatial_avg: str = dc.field(init=False)
    """Method used for spatial averaging, from ``table_qualifier``. Either
    'zonal_mean' or None."""
    temporal_avg: str = dc.field(init=False)
    """Method used for time averaging, from ``table_qualifier``. Either 'point'
    or 'interval'."""
    region: str = dc.field(init=False)
    """Geographic region described by the table, from ``table_suffix``. Either
    'Antarctica', 'Greenland' or None."""

    def __post_init__(self, table_freq=None):
        """Logic to populate all object attributes, based on substrings of
        ``table_id`` captured by regex.
        """
        if table_freq is None:
            raise ValueError()
        elif table_freq == 'clim':
            self.frequency = CMIP6DateFrequency('mon')
        else:
            self.frequency = CMIP6DateFrequency(table_freq)
        if self.table_qualifier == 'Z':
            self.spatial_avg = 'zonal_mean'
        else:
            self.spatial_avg = None
        if self.table_qualifier == 'Pt':
            self.temporal_avg = 'point'
        else:
            self.temporal_avg = 'interval'
        if self.table_suffix == 'a':
            self.region = 'Antarctica'
        elif self.table_suffix == 'g':
            self.region = 'Greenland'
        else:
            self.region = None


grid_label_regex = util.RegexPattern(r"""
        g
        (?P<global_mean>m?)
        (?P<regrid>n|r?)
        (?P<grid_number>\d?)
        (?P<region>a|g?)
        (?P<zonal_mean>z?)
    """,
                                     input_field="grid_label"
                                     )


@util.regex_dataclass(grid_label_regex)
class CMIP6_GridLabel:
    """:class:`~src.util.regex_dataclass` which represents and parses the CMIP6
    DRS grid label identifier string.

    Reference: CMIP6 `planning document <http://goo.gl/v1drZl>`__, note 11 on
    page 11.
    """
    grid_label: str = util.MANDATORY
    """Input to :meth:`~CMIP6_GridLabel.from_string`. ``grid_label`` string as
    used in the DRS."""
    global_mean: dc.InitVar = ""
    """Substring of ``grid_label`` for globally-averaged data."""
    regrid: str = ""
    """Substring of ``grid_label`` for regridded data."""
    grid_number: int = 0
    """Regridding method used (0 if native grid). As per CMIP6 spec, meaning of
    each integer is not specified and left to individual modeling centers."""
    region: str = ""
    """Geographic region described by the grid. Either 'Antarctica', 'Greenland'
    or None."""
    zonal_mean: dc.InitVar = ""
    """Substring of ``grid_label`` for zonal mean averaging."""
    spatial_avg: str = dc.field(init=False)
    """Method used for spatial averaging. Either 'global_mean', 'zonal_mean' or
    None."""
    native_grid: bool = dc.field(init=False)
    """Boolean, True if data is on model's native grid."""

    def __post_init__(self, global_mean=None, zonal_mean=None):
        """Logic to populate all object attributes, based on substrings of
        ``grid_label`` captured by regex.
        """
        if not self.grid_number:
            self.grid_number = 0
        if global_mean:
            self.spatial_avg = 'global_mean'
        elif zonal_mean:
            self.spatial_avg = 'zonal_mean'
        else:
            self.spatial_avg = None
        self.native_grid = not (self.regrid == 'r')
        if self.region == 'a':
            self.region = 'Antarctica'
        elif self.region == 'g':
            self.region = 'Greenland'
        else:
            self.region = None


drs_directory_regex = util.RegexPattern(r"""
        /?                      # maybe initial separator
        (CMIP6/)?
        (?P<activity_id>\w+)/
        (?P<institution_id>[a-zA-Z0-9_-]+)/
        (?P<source_id>[a-zA-Z0-9_-]+)/
        (?P<experiment_id>[a-zA-Z0-9_-]+)/
        (?P<variant_label>\w+)/
        (?P<table_id>\w+)/
        (?P<variable_id>\w+)/
        (?P<grid_label>\w+)/
        v(?P<version_date>\d+)
        /? # maybe final separator
    """,
                                        input_field="directory"
                                        )


@util.regex_dataclass(drs_directory_regex)
class CMIP6_DRSDirectory(CMIP6_VariantLabel, CMIP6_MIPTable, CMIP6_GridLabel):
    """:class:`~src.util.regex_dataclass` which represents and parses the DRS
    directory path.

    Reference: CMIP6 `planning document <http://goo.gl/v1drZl>`__, page 17.

    .. warning::
       This regex will fail on paths involving subexperiments.
    """
    directory: str = util.MANDATORY
    """Input to :meth:`~CMIP6_DRSDirectory.from_string`. Directory path
    string (excluding filename) as used in the DRS."""
    activity_id: str = ""
    """Activity ID (MIP) of data, as parsed from ``directory``."""
    institution_id: str = ""
    """Institution ID of data, as parsed from ``directory``."""
    source_id: str = ""
    """Source ID (model name) of data, as parsed from ``directory``."""
    experiment_id: str = ""
    """Experiment ID of data, as parsed from ``directory``."""
    variant_label: CMIP6_VariantLabel = ""
    """Variant label of data, as parsed from ``directory``."""
    table_id: CMIP6_MIPTable = ""
    """MIP table of data, as parsed from ``directory``."""
    grid_label: CMIP6_GridLabel = ""
    """Grid label of data, as parsed from ``directory``."""
    version_date: util.Date = None
    """Revision date of data, as parsed from ``directory``."""


_drs_dates_filename_regex = util.RegexPattern(r"""
        (?P<variable_id>\w+)_       # field name
        (?P<table_id>\w+)_       # field name
        (?P<source_id>[a-zA-Z0-9_-]+)_       # field name
        (?P<experiment_id>[a-zA-Z0-9_-]+)_       # field name
        (?P<variant_label>\w+)_       # field name
        (?P<grid_label>\w+)_       # field name
        (?P<start_date>\d+)-(?P<end_date>\d+)   # file's date range
        \.nc                      # netCDF file extension
    """
    )

_drs_static_filename_regex = util.RegexPattern(r"""
        (?P<variable_id>\w+)_       # field name
        (?P<table_id>\w+)_       # field name
        (?P<source_id>[a-zA-Z0-9_-]+)_       # field name
        (?P<experiment_id>[a-zA-Z0-9_-]+)_       # field name
        (?P<variant_label>\w+)_       # field name
        (?P<grid_label>\w+)
        \.nc                      # netCDF file extension, no dates
    """,
                                               defaults={'start_date': util.FXDateMin, 'end_date': util.FXDateMax},
                                               )

drs_filename_regex = util.ChainedRegexPattern(
    # try the first regex, and if no match, try second
    _drs_dates_filename_regex, _drs_static_filename_regex,
    input_field="filename"
)


@util.regex_dataclass(drs_filename_regex)
class CMIP6_DRSFilename(CMIP6_VariantLabel, CMIP6_MIPTable, CMIP6_GridLabel):
    """:class:`~src.util.regex_dataclass` which represents and parses the DRS
    filename.

    Reference: CMIP6 `planning document <http://goo.gl/v1drZl>`__, page 14-15.
    """
    filename: str = util.MANDATORY
    """Input to :meth:`~CMIP6_DRSFilename.from_string`. Filename as used in the
    DRS."""
    variable_id: str = ""
    """Variable name, as parsed from ``filename``."""
    table_id: CMIP6_MIPTable = ""
    """MIP table of data, as parsed from ``filename``."""
    source_id: str = ""
    """Source ID (model name) of data, as parsed from ``filename``."""
    experiment_id: str = ""
    """Experiment ID of data, as parsed from ``filename``."""
    variant_label: CMIP6_VariantLabel = ""
    """Variant label of data, as parsed from ``filename``."""
    grid_label: CMIP6_GridLabel = ""
    """Grid label of data, as parsed from ``filename``."""
    start_date: util.Date = None
    """Start date of data, as parsed from ``filename``."""
    end_date: util.Date = None
    """End date of data, as parsed from ``filename``."""
    date_range: util.DateRange = dc.field(init=False)
    """Start and end dates combined into a :class:`~src.util.datelable.DateRange`
    object."""

    def __post_init__(self, *args):
        if self.start_date == util.FXDateMin \
                and self.end_date == util.FXDateMax:
            # Assume we're dealing with static/fx-frequency data, so use special
            # placeholder values
            self.date_range = util.FXDateRange
            if not self.frequency.is_static:  # frequency inferred from table_id
                raise util.DataclassParseError(("Inconsistent filename parse: "
                                                f"cannot determine if '{self.filename}' represents static data."))
        else:
            self.date_range = util.DateRange(self.start_date, self.end_date)
            if self.frequency.is_static:  # frequency inferred from table_id
                raise util.DataclassParseError(("Inconsistent filename parse: "
                                                f"cannot determine if '{self.filename}' represents static data."))


drs_path_regex = util.RegexPattern(r"""
    (?P<directory>\S+)/   # any non-whitespace
    (?P<filename>[^/\s]+) # nonwhitespace and not directory separator
    """,
                                   input_field="path"
                                   )


@util.regex_dataclass(drs_path_regex)
class CMIP6_DRSPath(CMIP6_DRSDirectory, CMIP6_DRSFilename):
    """:class:`~src.util.regex_dataclass` which represents and parses a full
    CMIP6 DRS path.
    """
    path: str = util.MANDATORY
    """Input to :meth:`~CMIP6_DRSPath.from_string`. Full path to data file as
    used in the DRS."""
    directory: CMIP6_DRSDirectory = ""
    filename: CMIP6_DRSFilename = ""

