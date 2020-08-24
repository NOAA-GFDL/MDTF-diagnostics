"""Code to parse CMIP6 controlled vocabularies and elements of the CMIP6 DRS.

Specifications for the above were taken from the planning document 
`<http://goo.gl/v1drZl>`__, which doesn't seem to have a permanent link. The 
CMIP6 controlled vocabularies (lists of registered MIPs, modeling centers, etc.)
are derived from data in the 
`PCMDI/cmip6-cmor-tables <https://github.com/PCMDI/cmip6-cmor-tables>`__ 
repo, which is included as a submodule.

.. warning::
   Functionality here has been added as needed for the project and is incomplete,
   for example parsing subexperiments is not supported.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
import re
from src import datelabel
from src import util
from src import util_mdtf

class CMIP6_CVs(util.Singleton):
    """Interface for looking up information from the CMIP6 CV file.

    .. note::
       Lookups are implemented in an ad-hoc way with :class:`util.MultiMap`; a 
       more robust solution would use sqlite.
    """
    def __init__(self, unittest=False):
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            file_ = 'dummy_filename'
        else:
            config = util_mdtf.ConfigManager()
            file_ = os.path.join(config.paths.CODE_ROOT, 'src', 
                'cmip6-cmor-tables','Tables','CMIP6_CV.json')
        self._contents = util.read_json(file_)
        self._contents = self._contents['CV']
        for k in ['product','version_metadata','required_global_attributes',
            'further_info_url','Conventions','license']:
            # remove unecessary information
            del self._contents[k]

        # munge table_ids
        self._contents['table_id'] = dict.fromkeys(self._contents['table_id'])
        for tbl in self._contents['table_id']:
            self._contents['table_id'][tbl] = parse_mip_table_id(tbl)

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
            self.cv[k] = util.coerce_to_iter(self._contents[k])

    def is_in_cv(self, category, items):
        """Determine if *items* take values that are valid for the CV category
        *category*.

        Args:
            category (str): the CV category to use to validate values.
            items (str or list of str): Entries whose validity we'd like to 
                check.

        Returns: boolean or list of booleans, corresponding to the validity of 
            the entries in *items*.
        """
        self._make_cv()
        assert category in self.cv
        if util.is_iterable(items):
            return [(item in self.cv[category]) for item in items]
        else:
            return (items in self.cv[category])

    def get_lookup(self, source, dest):
        """Find the appropriate lookup table to convert values in *source* (keys)
        to values in *dest* (values), generating it if necessary.

        Args:
            source (str): the CV category to use for the keys.
            dest (str): the CV category to use for the values.

        Returns: :class:`util.MultiMap` providing a dict-like lookup interface,
            ie dest_value = d[source_key].
        """
        if (source, dest) in self._lookups:
            return self._lookups[(source, dest)]
        elif (dest, source) in self._lookups:
            return self._lookups[(dest, source)].inverse()
        elif source in self._contents:
            k = list(self._contents[source])[0]
            if dest not in self._contents[source][k]:
                raise KeyError(
                    "Can't find {} in attributes for {}.".format(dest, source))
            mm = util.MultiMap()
            for k in self._contents[source]:
                mm[k].update(
                    util.coerce_to_iter(self._contents[source][k][dest], set)
                )
            self._lookups[(source, dest)] = mm
            return mm
        elif dest in self._contents:
            return self._lookups[(dest, source)].inverse()
        else:
            raise KeyError('Neither {} or {} in CV table list.'.format(source, dest))

    def lookup(self, source_items, source, dest):
        """Lookup the corresponding *dest* values for *source_items* (keys).

        Args:
            source_items (str or list): one or more keys 
            source (str): the CV category that the items in *source_items*
                belong to.
            dest (str): the CV category we'd like the corresponding values for.

        Returns: list of *dest* values corresponding to each entry in *source_items*.
        """
        _lookup = self.get_lookup(source, dest)
        if util.is_iterable(source_items):
            return [util.coerce_from_iter(_lookup[item]) for item in source_items]
        else:
            return util.coerce_from_iter(_lookup[source_items])

    # ----------------------------------

    def table_id_from_freq(self, date_freq):
        """Specialized lookup to determine which MIP tables use data at the 
        requested *date_freq*.

        Should really be handled as a special case of :meth:`lookup`.

        Args:
            date_freq (:class:`CMIP6DateFrequency`): DateFrequency 

        Returns: list of MIP table ``table_id`` names, if any, that use data at 
            the given *date_freq*.
        """
        self._make_cv()
        assert 'table_id' in self.cv
        return [tbl for tbl in self.cv['table_id'] \
            if (parse_mip_table_id(tbl)['date_freq'] == date_freq)]


@six.python_2_unicode_compatible
class CMIP6DateFrequency(datelabel.DateFrequency):
    """Subclass of :class:`datelabel.DateFrequency` to parse data frequency
    information as encoded in MIP tables, DRS filenames, etc.

    Extends DateFrequency in that this records if the data is a climatological
    average, although this information is not currently used.

    Reference: `<http://goo.gl/v1drZl>`__, page 16.
    """
    _precision_lookup = {
        'fx': 0, 'yr': 1, 'mo': 2, 'day': 3,
        'hr': 5, # includes minutes
        'min': 6, # = subhr, minutes and seconds
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

            if not md['quantity']:
                md['quantity'] = 1
            else:
                md['quantity'] = int(md['quantity'])
            
            if not md['avg']:
                md['avg'] = 'Mean'
            elif md['avg'] in ['C', 'CM']:
                md['avg'] = 'Clim'

            md['precision'] = cls._precision_lookup[md['unit']]
            return (cls._get_timedelta_kwargs(md['quantity'], md['unit']), md)
        else:
            raise ValueError("Malformed input {} {}".format(quantity, unit))

    def format(self):
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

# --------------------------------------

mip_table_regex = re.compile(r"""
    ^ # start of line
    (?P<table_prefix>(A|CF|E|I|AER|O|L|LI|SI)?)
    # maybe a digit, followed by as few lowercase letters as possible:
    (?P<table_freq>\d?[a-z]*?)
    (?P<table_suffix>(ClimMon|Lev|Plev|Ant|Gre)?)
    (?P<table_qualifier>(Pt|Z|Off)?)
    $ # end of line - necessary for lazy capture to work
""", re.VERBOSE)

def parse_mip_table_id(mip_table):
    """Function to parse MIP table identifier string.

    Reference: `https://earthsystemcog.org/projects/wip/mip_table_about`__,
    although this doesn't document all cases used in CMIP6.

    Args:
        mip_table (str): MIP table name.

    Returns:
        dict of MIP attributes determined by the DRS naming convention.
    """
    match = re.match(mip_table_regex, mip_table)
    if match:
        md = match.groupdict()
        md['table_id'] = mip_table
        if md['table_freq'] == 'clim':
            md['date_freq'] = CMIP6DateFrequency('mon')
        else:
            md['date_freq'] = CMIP6DateFrequency(md['table_freq'])
        if md['table_qualifier'] == 'Z':
            md['spatial_avg'] = 'zonal_mean'
        else:
            md['spatial_avg'] = None
        if md['table_qualifier'] == 'Pt':
            md['temporal_avg'] = 'point'
        else:
            md['temporal_avg'] = 'interval'
        if md['table_suffix'] == 'a':
            md['region'] = 'Antarctica'
        elif md['table_suffix'] == 'g':
            md['region'] = 'Greenland'
        else:
            md['region'] = None
        return md
    else:
        raise ValueError("Can't parse table {}.".format(mip_table))

grid_label_regex = re.compile(r"""
    g
    (?P<global_mean>m?)
    (?P<regrid>n|r?)
    (?P<num>\d?)
    (?P<region>a|g?)
    (?P<zonal_mean>z?)
""", re.VERBOSE)

def parse_grid_label(grid_label):
    """Function to parse CMIP6 DRS grid label identifier string.

    Reference: `<http://goo.gl/v1drZl>`__, note 11 on page 11.

    Args:
        grid_label (str): grid label string.

    Returns:
        dict of grid attributes determined by the DRS naming convention.
    """
    match = re.match(grid_label_regex, grid_label)
    if match:
        md = match.groupdict()
        ans = dict()
        ans['grid_label'] = grid_label
        if md['global_mean']:
            ans['spatial_avg'] = 'global_mean'
        elif md['zonal_mean']:
            ans['spatial_avg'] = 'zonal_mean'
        else:
            ans['spatial_avg'] = None
        ans['native_grid'] = not (md['regrid'] == 'r')
        if not md['num']:
            ans['grid_number'] = 0
        else:
            ans['grid_number'] = md['num']
        if md['region'] == 'a':
            ans['region'] = 'Antarctica'
        elif md['region'] == 'g':
            ans['region'] = 'Greenland'
        else:
            ans['region'] = None
        return ans
    else:
        raise ValueError("Can't parse grid {}.".format(grid_label))

drs_directory_regex = re.compile(r"""
    /?                      # maybe initial separator
    (CMIP6/)?
    (?P<activity_id>\w+)/
    (?P<institution_id>[a-zA-Z0-9_-]+)/
    (?P<source_id>[a-zA-Z0-9_-]+)/
    (?P<experiment_id>[a-zA-Z0-9_-]+)/
    (?P<member_id>\w+)/
    (?P<table_id>\w+)/
    (?P<variable_id>\w+)/
    (?P<grid_label>\w+)/
    v(?P<version_date>\d+)
    /?                      # maybe final separator
""", re.VERBOSE)

# TODO: parse subexperiments!
def parse_DRS_directory(dir_):
    """Function to parse DRS directory, using regex defined above.

    Reference: `<http://goo.gl/v1drZl>`__, page 17.

    Args:
        dir_ (str): directory path to be parsed.

    Returns:
        dict of directory attributes determined by the DRS naming convention.
    """
    match = re.match(drs_directory_regex, dir_)
    if match:
        md = match.groupdict()
        md['version_date'] = datelabel.Date(md['version_date'])
        md.update(parse_mip_table_id(md['table_id']))
        return md
    else:
        raise ValueError("Can't parse dir {}.".format(dir_))

drs_filename_regex = re.compile(r"""
    (?P<variable_id>\w+)_       # field name
    (?P<table_id>\w+)_       # field name
    (?P<source_id>[a-zA-Z0-9_-]+)_       # field name
    (?P<experiment_id>[a-zA-Z0-9_-]+)_       # field name
    (?P<realization_code>\w+)_       # field name
    (?P<grid_label>\w+)_       # field name
    (?P<start_date>\d+)-(?P<end_date>\d+)   # file's date range
    \.nc                      # netCDF file extension
""", re.VERBOSE)

def parse_DRS_filename(file_):
    """Function to parse DRS filename, using regex defined above.

    Reference: `<http://goo.gl/v1drZl>`__, page 14-15.

    Args:
        file_ (str): filename to be parsed.

    Returns:
        dict of file attributes determined by the DRS naming convention.
    """
    match = re.match(drs_filename_regex, file_)
    if match:
        md = match.groupdict()
        md['start_date'] = datelabel.Date(md['start_date'])
        md['end_date'] = datelabel.Date(md['end_date'])
        md['date_range'] = datelabel.DateRange(md['start_date'], md['end_date'])
        md.update(parse_mip_table_id(md['table_id']))
        return md
    else:
        raise ValueError("Can't parse file {}.".format(file_))

def parse_DRS_path(*args):
    """Function to parse complete DRS path.

    Calls :func:`parse_DRS_directory` and :func:`parse_DRS_filename`, and 
    ensures that data specified in both functions is consistent.

    Args:
        Either a (str) containing the complete path to be parsed, or two (str)s
            consisting of the directory and filename.

    Returns:
        dict of file attributes determined by the DRS naming convention.
    """
    if len(args) == 1:
        dir_, file_ = os.path.split(args[0])
    elif len(args) == 2:
        dir_, file_ = args
    else:
        raise ValueError()
    d1 = parse_DRS_directory(dir_)
    d2 = parse_DRS_filename(file_)
    common_keys = set(d1)
    common_keys = common_keys.intersection(list(d2))
    for key in common_keys:
        if d1[key] != d2[key]:
            raise ValueError("{} fields inconsistent in parsing {}".format(
                key, args))
    d1.update(d2)
    return d1
    