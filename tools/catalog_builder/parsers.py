import xarray as xr
import traceback
import pathlib
import os
import io
import sys
import json
import logging
import collections
import cftime
from ecgtools.builder import INVALID_ASSET, TRACEBACK


# Define a log object for debugging
_log = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)).split('/tools/catalog_builder')[0]

freq_opts = ['mon',
             'day',
             'daily',
             '6hr',
             '3hr',
             '1hr',
             'subhr',
             'annual',
             'year']

catalog_keys = [
                'activity_id',
                'assoc_files',
                'institution_id',
                'member_id',
                'realm',
                'variable_id',
                'table_id',
                'source_id',
                'source_type',
                'cell_methods',
                'cell_measures',
                'experiment_id',
                'variant_label',
                'grid_label',
                'units',
                'time_range',
                'chunk_freq',
                'standard_name',
                'long_name',
                'frequency',
                'file_name',
                'path'
            ]

def strip_comments(str_: str, delimiter=None):
    """ Remove comments from *str_*. Comments are taken to start with an
    arbitrary *delimiter* and run to the end of the line.
    """
    # would be better to use shlex, but that doesn't support multi-character
    # comment delimiters like '//'
    escaped_quote_placeholder = '\v'  # no one uses vertical tab

    if not delimiter:
        return str_
    lines = str_.splitlines()
    for i in range(len(lines)):
        # get rid of lines starting with delimiter
        if lines[i].startswith(delimiter):
            lines[i] = ''
            continue
        # handle delimiters midway through a line:
        # If delimiter appears quoted in a string, don't want to treat it as
        # a comment. So for each occurrence of delimiter, count number of
        # 's to its left and only truncate when that's an even number.
        # First we get rid of -escaped single "s.
        replaced_line = lines[i].replace('\\\"', escaped_quote_placeholder)
        line_parts = replaced_line.split(delimiter)
        quote_counts = [s.count('"') for s in line_parts]
        j = 1
        while sum(quote_counts[:j]) % 2 != 0:
            if j >= len(quote_counts):
                raise ValueError(f"Couldn't parse line {i+1} of string.")
            j += 1
        replaced_line = delimiter.join(line_parts[:j])
        lines[i] = replaced_line.replace(escaped_quote_placeholder, '\\\"')
    # make lookup table of correct line numbers, taking into account lines we
    # dropped
    line_nos = [i for i, s in enumerate(lines) if (s and not s.isspace())]
    # join lines, stripping blank lines
    new_str = '\n'.join([s for s in lines if (s and not s.isspace())])
    return new_str, line_nos
def parse_json(str_: str):
    """Parse JSONC (JSON with ``//``-comments) string *str_* into a Python object.
    Comments are discarded. Wraps standard library :py:func:`json.loads`.

    Syntax errors in the input (:py:class:`~json.JSONDecodeError`) are passed
    through from the Python standard library parser. We correct the line numbers
    mentioned in the errors to refer to the original file (i.e., with comments.)
    """
    def _pos_from_lc(lineno, colno, str_):
        # fix line number, since we stripped commented-out lines. JSONDecodeError
        # computes line/col no. in error message from character position in string.
        lines = str_.splitlines()
        return (colno - 1) + sum((len(line) + 1) for line in lines[:lineno])

    (strip_str, line_nos) = strip_comments(str_, delimiter='//')
    try:
        parsed_json = json.loads(strip_str,
                                 object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as exc:
        # fix reported line number, since we stripped commented-out lines.
        assert exc.lineno <= len(line_nos)
        raise json.JSONDecodeError(
            msg=exc.msg, doc=str_,
            pos=_pos_from_lc(line_nos[exc.lineno-1], exc.colno, str_)
        )
    except UnicodeDecodeError as exc:
        raise json.JSONDecodeError(
            msg=f"parse_json received UnicodeDecodeError:\n{exc}",
            doc=strip_str, pos=0
        )

    return parsed_json
def read_json(file_path: str, log=_log) -> dict:
    """Reads a struct from a JSONC file at *file_path*.
    """
    log.debug('Reading file %s', file_path)
    try:
        with io.open(file_path, 'r', encoding='utf-8') as file_:
            str_ = file_.read()
    except Exception as exc:
        # something more serious than missing file
        _log.critical("Caught exception when trying to read %s: %r", file_path, exc)
        exit(1)
    return parse_json(str_)


def parse_nc_file(file_path: pathlib.Path, catalog_info: dict) -> dict:
    # call to xr.open_dataset required by ecgtools.builder.Builder
    exclude_vars = ('time', 'time_bnds', 'date', 'hyam', 'hybm')
    with xr.open_dataset(file_path, chunks={}, decode_times=False, engine="netcdf4") as ds:
        variable_list = [var for var in ds if 'standard_name' in ds[var].attrs
                         or 'long_name' in ds[var].attrs and
                         var not in ds.coords and
                         var not in exclude_vars]
        # append time range
        if 'time' in ds.coords:
            time_var = ds.coords['time']
            calendar = None
            if 'calendar' in time_var.attrs:
                calendar = time_var.attrs['calendar']
                if calendar == 'no_leap':
                    calendar = 'noleap'
            start_time = cftime.num2date(time_var.values[0], time_var.attrs['units'], calendar=calendar)
            end_time = cftime.num2date(time_var.values[-1], time_var.attrs['units'])
            time_range = start_time.strftime("%Y%m%d:%H%M%S") + '-' + end_time.strftime("%Y%m%d:%H%M%S")
            catalog_info.update({'time_range': time_range})

        for var in variable_list:
            if len(ds[var].attrs['long_name']) == 0 and len(ds[var].attrs['long_name']) == 0:
                print('Asset variable does not contain a standard_name or long_name attribute')
                exit(1)
            for attr in catalog_keys:
                if attr in ds[var].attrs:
                    catalog_info.update({attr: ds[var].attrs[attr]})
            if catalog_info['variable_id'] == "":
                catalog_info.update({'variable_id': var})

        return catalog_info

def setup_catalog() -> dict:
    catalog_info = dict()
    for k in catalog_keys:
        catalog_info[k] = ""
    return catalog_info

# custom parser for GFDL am5 data that uses fieldlist metadata and the DRS to populate
# required catalog fields
def parse_gfdl_am5_data(file_name: str):
    catalog_info = setup_catalog()
    file = pathlib.Path(file_name)  # uncomment when ready to run

    num_dir_parts = len(file.parts)  # file name index = num_parts 1
    # isolate file from rest of path
    stem = file.stem
    # split the file name into components based on
    # assume am5 file name format is {realm}.{time_range}.[variable_id}.nc
    split = stem.split('.')
    catalog_info.update({"realm": split[0]})
    catalog_info.update({"time_range": split[1]})
    catalog_info.update({"variable_id": split[2]})
    catalog_info.update({"chunk_freq": file.parts[num_dir_parts - 2]})
    catalog_info.update({"activity_id": "GFDL"})
    catalog_info.update({"institution_id": "GFDL"})
    file_freq = file.parts[num_dir_parts - 3]

    for f in freq_opts:
        if f in file_freq:
            catalog_info.update({"frequency": f})
            break
    if 'daily' in file_freq:
        catalog_info.update({"frequency": "day"})
    elif 'monthly' in file_freq:
        catalog_info.update({"frequency": "mon"})

        # read metadata from the appropriate fieldlist
    if 'cmip' in catalog_info['realm'].lower():
        gfdl_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_CMIP.jsonc')
    else:
        gfdl_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_GFDL.jsonc')

    try:
        gfdl_info = read_json(gfdl_fieldlist, log=_log)
    except IOError:
        print("Unable to open file", gfdl_fieldlist)
        sys.exit(1)

    if hasattr(gfdl_info['variables'], catalog_info['variable_id']):
        var_metadata = gfdl_info['variables'].get(catalog_info['variable_id'])
    else:
        raise KeyError(f"{catalog_info['variable_id']} not found in {gfdl_fieldlist}")
    if hasattr(var_metadata, 'standard_name'):
        catalog_info.update({'standard_name': var_metadata.standard_name})
    if hasattr(var_metadata, 'long_name'):
        catalog_info.update({'long_name': var_metadata.long_name})
    if hasattr(var_metadata, 'units'):
        catalog_info.update({'units': var_metadata.units})
    try:
       # populate information from file metadata
       parse_nc_file(file, catalog_info)
    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}

    return catalog_info

# custom parser for pp data stored on GFDL archive filesystem
# assumed DRS of [root_dir]/pp/[realm]/[analysis type (e.g, 'ts')]/[frequency]/[chunk size (e.g., 1yr, 5yr)]
def parse_gfdl_pp_ts(file_name: str):
    catalog_info = setup_catalog()
    # files = sorted(glob.glob(os.path.join(file_name,'*.nc')))  # debug comment when ready to run
    # file = pathlib.Path(files[0])  # debug comment when ready to run
    file = pathlib.Path(file_name)  # uncomment when ready to run
    num_parts = len(file.parts)  # file name index = num_parts 1
    # isolate file from rest of path
    stem = file.stem
    # split the file name into components based on _
    split = stem.split('.')
    realm = split[0]
    time_range = split[1]
    variable_id = split[2]
    fname = file.parts[num_parts - 1]
    chunk_freq = file.parts[num_parts - 2]  # e.g, 1yr, 5yr
    freq = file.parts[num_parts - 3] # e.g mon, day, 6hr, 3hr
   
    catalog_info.update({"activity_id": "GFDL"})
    catalog_info.update({"institution_id": "GFDL"})
    catalog_info.update({"path": file_name})
    catalog_info.update({"file_name": fname})
    catalog_info.update({"variable_id": variable_id})
    catalog_info.update({"chunk_freq": chunk_freq})
    catalog_info.update({"realm": realm})
    catalog_info.update({"time_range": time_range})

    file_freq = file.parts[num_parts - 3]
    for f in freq_opts:
        if f in file_freq:
            catalog_info.update({"frequency": f})
            break
    if 'daily' in file_freq:
        catalog_info.update({"frequency": "day"})
    elif 'monthly' in file_freq:
        catalog_info.update({"frequency": "mon"})
    try:
       # populate information from file metadata
       parse_nc_file(file, catalog_info)
    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}
    
    return catalog_info

# custom parser for CESM data that uses fieldlist metadata and the DRS to populate
# required catalog fields. Bas
def parse_cesm(file_name: str):
    catalog_info = setup_catalog()
    catalog_info.update({"path": file_name})
    catalog_info.update({"activity_id": "CESM"})
    catalog_info.update({"institution_id": "NCAR"})
    # split the file path and name into parts
    file = pathlib.Path(file_name)
    stem_parts = file.stem.split('.')
    # search file and path for output frequency
    for p in list(file.parts) + stem_parts:
        if p in freq_opts:
            catalog_info.update({"frequency": p})
            break
    try:
        # populate information from file metadata
        new_catalog = parse_nc_file(file, catalog_info)
    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}
    # read metadata from the appropriate fieldlist
    cesm_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_CESM.jsonc')
    try:
        cesm_info = read_json(cesm_fieldlist, log=_log)
    except IOError:
        print("Unable to open file", cesm_fieldlist)
        sys.exit(1)

    units = new_catalog.get('units')
    new_catalog.update({'units': units.replace('/s',' s-1').replace('/m2', ' m-2')})
    var_metadata = cesm_info['variables'].get(new_catalog['variable_id'], None)
    if var_metadata is not None:
        if var_metadata.get('standard_name', None) is not None:
            new_catalog.update({'standard_name': var_metadata['standard_name']})
        if var_metadata.get('realm', None) is not None :
            new_catalog.update({'realm': var_metadata['realm']})

    return new_catalog


# custom parser for single time-slice CESM output files named <case>.<variable>.<frequency>.nc
# with no embedded date range (e.g., cesm_mdtfv3_timeslice.T.1hrPt.nc). This DRS mixes native
# CESM/CAM variable names with a CMIP6-style frequency suffix (e.g. 'Pt' for instantaneous
# sampling) instead of a CESM history stream (h0, h1, ...), so neither the stock
# parse_cesm_timeseries (expects a stream + date range) nor a CMIP6 parser (expects CMIP
# variable_ids) can handle it. parse_nc_file/parse_cesm can also mis-identify the variable
# when the file contains multiple variables with a long_name attribute (e.g., P0, hyam), so
# the variable is taken directly from the file name instead.
def parse_cesm_mdtfv3_timeslice(file_name: str):
    catalog_info = setup_catalog()
    file = pathlib.Path(file_name)
    catalog_info.update({"path": str(file)})
    catalog_info.update({"activity_id": "CESM"})
    catalog_info.update({"institution_id": "NCAR"})

    # case name may itself contain dots, so take variable/frequency from the end of the stem
    stem_parts = file.stem.split('.')
    if len(stem_parts) < 3:
        return {INVALID_ASSET: file,
                TRACEBACK: f"{file.name} does not match the <case>.<variable>.<frequency>.nc convention"}

    frequency = stem_parts[-1]
    variable_id = stem_parts[-2]
    # strip the 'Pt' (instantaneous, as opposed to time-averaged) suffix so frequency
    # matches values recognized by util.datelabel.DateFrequency (e.g., '1hrPt' -> '1hr'),
    # and downstream catalog queries built by src/data_sources.py, which never add 'Pt'
    is_instantaneous = frequency.endswith('Pt')
    if is_instantaneous:
        frequency = frequency[:-2]
    catalog_info.update({"variable_id": variable_id, "frequency": frequency})

    try:
        with xr.open_dataset(file, chunks={}, decode_times=False, engine="netcdf4") as ds:
            if variable_id not in ds.variables:
                raise KeyError(f"{variable_id} not found in {file}")
            var_attrs = ds[variable_id].attrs
            catalog_info.update({
                "units": var_attrs.get('units', ''),
                "long_name": var_attrs.get('long_name', ''),
                "standard_name": var_attrs.get('standard_name', ''),
                "experiment_id": ds.attrs.get('case', '')
            })
            if 'time' in ds.coords:
                time_var = ds.coords['time']
                calendar = time_var.attrs.get('calendar')
                if calendar == 'no_leap':
                    calendar = 'noleap'
                start_time = cftime.num2date(time_var.values[0], time_var.attrs['units'], calendar=calendar)
                end_time = cftime.num2date(time_var.values[-1], time_var.attrs['units'], calendar=calendar)
                catalog_info.update({
                    'time_range': start_time.strftime("%Y%m%d:%H%M%S") + '-' + end_time.strftime("%Y%m%d:%H%M%S")
                })
    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}

    # preserve the instantaneous-vs-time-averaged distinction carried by the 'Pt' suffix,
    # since it was stripped from the frequency column above
    if not catalog_info.get('cell_methods'):
        catalog_info.update({'cell_methods': 'time: point' if is_instantaneous else 'time: mean'})

    # fill in metadata missing from the file itself from the CESM fieldlist
    cesm_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_CESM.jsonc')
    try:
        cesm_info = read_json(cesm_fieldlist, log=_log)
    except IOError:
        print("Unable to open file", cesm_fieldlist)
        sys.exit(1)

    units = catalog_info.get('units')
    if units:
        catalog_info.update({'units': units.replace('/s', ' s-1').replace('/m2', ' m-2')})

    var_metadata = cesm_info['variables'].get(variable_id, None)
    if var_metadata is not None:
        if not catalog_info.get('standard_name') and var_metadata.get('standard_name', None) is not None:
            catalog_info.update({'standard_name': var_metadata['standard_name']})
        if var_metadata.get('realm', None) is not None:
            catalog_info.update({'realm': var_metadata['realm']})

    return catalog_info


# custom parser for GFDL fregrid-remapped output named
# <case>.<time_range>.<variable_id>.<frequency>.nc (the case name itself contains dots, e.g.
# GFDL.CM4.AMIP.1979010100-1983123123.hfls.6hr.nc), stored under a <frequency>/ subdirectory.
# This differs from the DRS assumed by parse_gfdl_pp_ts (fixed realm.time_range.variable_id.nc
# layout), so fields are taken from the end of the filename stem instead. parse_nc_file is not
# used here because these files also carry lat_bnds/lon_bnds variables with their own
# long_name/units attributes, and parse_nc_file's variable scan ends up using those to
# overwrite the actual data variable's metadata. Variables mostly use CMOR names (hfls, hus,
# ta, ...), so realm/standard_name/units are looked up from fieldlist_CMIP.jsonc first,
# falling back to fieldlist_GFDL.jsonc for native GFDL names (e.g. slp) not in the CMIP tables.
def parse_gfdl_fregrid_ts(file_name: str):
    catalog_info = setup_catalog()
    file = pathlib.Path(file_name)
    catalog_info.update({"path": str(file)})
    catalog_info.update({"activity_id": "CMIP"})

    stem_parts = file.stem.split('.')
    if len(stem_parts) < 3:
        return {INVALID_ASSET: file,
                TRACEBACK: f"{file.name} does not match the "
                           f"<case>.<time_range>.<variable_id>.<frequency>.nc convention"}

    frequency = stem_parts[-1]
    variable_id = stem_parts[-2]
    time_range = stem_parts[-3]
    catalog_info.update({"variable_id": variable_id, "frequency": frequency, "time_range": time_range})

    try:
        with xr.open_dataset(file, chunks={}, decode_times=False, engine="netcdf4") as ds:
            if variable_id not in ds.variables:
                raise KeyError(f"{variable_id} not found in {file}")
            var_attrs = ds[variable_id].attrs
            catalog_info.update({
                "units": var_attrs.get('units', ''),
                "long_name": var_attrs.get('long_name', ''),
                "standard_name": var_attrs.get('standard_name', ''),
                "cell_methods": var_attrs.get('cell_methods', ''),
                "cell_measures": var_attrs.get('cell_measures', '')
            })
            if 'time' in ds.coords:
                time_var = ds.coords['time']
                calendar = time_var.attrs.get('calendar')
                if calendar == 'no_leap':
                    calendar = 'noleap'
                start_time = cftime.num2date(time_var.values[0], time_var.attrs['units'], calendar=calendar)
                end_time = cftime.num2date(time_var.values[-1], time_var.attrs['units'], calendar=calendar)
                catalog_info.update({
                    'time_range': start_time.strftime("%Y%m%d:%H%M%S") + '-' + end_time.strftime("%Y%m%d:%H%M%S")
                })
    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}

    # realm isn't a per-variable netCDF attribute, and standard_name/units may be missing
    # from the file, so fill in any gaps from the fieldlists
    var_metadata = None
    for fieldlist_name in ('data/fieldlist_CMIP.jsonc', 'data/fieldlist_GFDL.jsonc'):
        fieldlist_path = os.path.join(ROOT_DIR, fieldlist_name)
        try:
            fieldlist = read_json(fieldlist_path, log=_log)
        except IOError:
            print("Unable to open file", fieldlist_path)
            sys.exit(1)
        var_metadata = fieldlist['variables'].get(variable_id, None)
        if var_metadata is not None:
            break

    if var_metadata is not None:
        if not catalog_info.get('realm') and var_metadata.get('realm', None) is not None:
            catalog_info.update({'realm': var_metadata['realm']})
        if not catalog_info.get('standard_name') and var_metadata.get('standard_name', None) is not None:
            catalog_info.update({'standard_name': var_metadata['standard_name']})
        if not catalog_info.get('units') and var_metadata.get('units', None) is not None:
            catalog_info.update({'units': var_metadata['units']})

    return catalog_info
