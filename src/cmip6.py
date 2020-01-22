from __future__ import print_function
import os
import re
import datelabel
import util

class CMIP6_CVs(util.Singleton):
    def __init__(self, unittest_flag=False):
        # pylint: disable=maybe-no-member
        if unittest_flag:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            file_ = 'dummy_filename'
        else:
            paths = util.PathManager()
            file_ = os.path.join(paths.CODE_ROOT, 'src', 
                'cmip6-cmor-tables','Tables','CMIP6_CV.json')
        self._contents = util.read_json(file_)
        self._contents = self._contents['CV']
        for k in ['product','version_metadata','required_global_attributes',
            'further_info_url','Conventions','license']:
            del self._contents[k]

        # munge table_ids
        self._contents['table_id'] = dict.fromkeys(self._contents['table_id'])
        for tbl in self._contents['table_id']:
            self._contents['table_id'][tbl] = parse_mip_table_id(tbl)

        self.cv = dict()
        self._lookups = dict()

    def _make_cv(self):
        # make on-demand
        if self.cv:
            return
        for k in self._contents:
            self.cv[k] = util.coerce_to_iter(self._contents[k], list)

    def is_in_cv(self, category, items):
        self._make_cv()
        assert category in self.cv
        if hasattr(items, '__iter__'):
            return [(item in self.cv[category]) for item in items]
        else:
            return (items in self.cv[category])

    def get_lookup(self, source, dest):
        if (source, dest) in self._lookups:
            return self._lookups[(source, dest)]
        elif (dest, source) in self._lookups:
            return self._lookups[(dest, source)].inverse()
        elif source in self._contents:
            k = self._contents[source].keys()[0]
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
        _lookup = self.get_lookup(source, dest)
        if hasattr(source_items, '__iter__'):
            return [util.coerce_from_iter(_lookup[item]) for item in source_items]
        else:
            return util.coerce_from_iter(_lookup[source_items])

    # ----------------------------------

    def table_id_from_freq(self, date_freq):
        self._make_cv()
        assert 'table_id' in self.cv
        return [tbl for tbl in self.cv['table_id'] \
            if (parse_mip_table_id(tbl)['date_freq'] == date_freq)]


class CMIP6DateFrequency(datelabel.DateFrequency):
    # http://goo.gl/v1drZl, page 16
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

# see https://earthsystemcog.org/projects/wip/mip_table_about
# (which doesn't cover all cases)
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
    if len(args) == 1:
        dir_, file_ = os.path.split(args[0])
    elif len(args) == 2:
        dir_, file_ = args
    else:
        raise ValueError()
    d1 = parse_DRS_directory(dir_)
    d2 = parse_DRS_filename(file_)
    common_keys = set(d1.keys())
    common_keys = common_keys.intersection(d2.keys())
    for key in common_keys:
        if d1[key] != d2[key]:
            raise ValueError("{} fields inconsistent in parsing {}".format(
                key, args))
    d1.update(d2)
    return d1
    