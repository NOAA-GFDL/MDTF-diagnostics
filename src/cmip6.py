import os
import re
import datelabel

# see https://earthsystemcog.org/projects/wip/mip_table_about
# (which doesn't cover all cases)
mip_table_regex = re.compile(r"""
    ^ # start of line
    (?P<prefix>(A|CF|E|I|AER|O|L|LI|SI)?)
    (?P<freq>\d?[a-z]*?)    # maybe a digit, followed by as few lowercase letters as possible
    (?P<suffix>(ClimMon|Lev|Plev|Ant|Gre)?)
    (?P<qualifier>(Pt|Z|Off)?)
    $ # end of line - necessary for lazy capture to work
""", re.VERBOSE)

def parse_mip_table(mip_table):
    match = re.match(mip_table_regex, mip_table)
    if match:
        md = match.groupdict()
        if md['freq'] == 'clim':
            md['freq'] == 'mon'
        md['freq'] = datelabel.DateFrequency(md['freq'])
        return md
    else:
        raise ValueError("Can't parse {}.".format(mip_table))

drs_directory_regex = re.compile(r"""
    /?                      # maybe initial separator
    CMIP6/
    (?P<activity_id>\w+)/
    (?P<institution_id>\w+)/
    (?P<source_id>\w+)/
    (?P<experiment_id>\w+)/
    (?P<member_id>\w+)/
    (?P<table_id>\w+)/
    (?P<variable_id>\w+)/
    (?P<grid_label>\w+)/
    v(?P<version_date>\d+)/
    /?                      # maybe final separator
""", re.VERBOSE)

def parse_DRS_directory(dir_):
    match = re.match(drs_directory_regex, dir_)
    if match:
        md = match.groupdict()
        md['version_date'] = datelabel.Date(md['version_date'])
        return md
    else:
        raise ValueError("Can't parse {}.".format(dir_))

drs_filename_regex = re.compile(r"""
    (?P<variable_id>\w+)_       # field name
    (?P<table_id>\w+)_       # field name
    (?P<source_id>\w+)_       # field name
    (?P<experiment_id>\w+)_       # field name
    (?P<realization_code>\w+)_       # field name
    (?P<grid_label>\w+)_       # field name
    (?P<start_date>\d+)-(?P<end_date>\d+)\.   # file's date range
    nc                      # netCDF file extension
""", re.VERBOSE)

def parse_DRS_filename(file_):
    match = re.match(drs_filename_regex, file_)
    if match:
        md = match.groupdict()
        md['start_date'] = datelabel.Date(md['start_date'])
        md['end_date'] = datelabel.Date(md['end_date'])
        md['date_range'] = datelabel.DateRange(md['start_date'], md['end_date'])
        return md
    else:
        raise ValueError("Can't parse {}.".format(file_))

def parse_DRS_path(path):
    dir_, file_ = os.path.split(path)
    d1 = parse_DRS_directory(dir_)
    d2 = parse_DRS_filename(file_)
    common_keys = set(d1.keys())
    common_keys = common_keys.intersection(d2.keys())
    for key in common_keys:
        if d1['key'] != d2['key']:
            raise ValueError("{} fields inconsistent in parsing {}".format(
                key, path))
    return d1.update(d2)