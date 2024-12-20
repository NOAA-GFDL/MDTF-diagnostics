import xarray as xr
import traceback
import pathlib
import os
import io
import sys
import json
import logging
import collections
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
        # "s to its left and only truncate when that's an even number.
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


# custom parser for GFDL am5 data that uses fieldlist metadata and the DRS to populate
# required catalog fields
def parse_gfdl_am5_data(file_name: str):

    file = pathlib.Path(file_name)  # uncomment when ready to run

    num_dir_parts = len(file.parts)  # file name index = num_parts 1
    # isolate file from rest of path
    stem = file.stem
    # split the file name into components based on
    # assume am5 file name format is {realm}.{time_range}.[variable_id}.nc
    split = stem.split('.')
    num_file_parts = len(split)
    realm = split[0]
    cell_methods = ""
    cell_measures = ""
    time_range = split[1]
    start_time = time_range.split('-')[0]
    end_time = time_range.split('-')[1]
    variable_id = split[2]
    source_type = ""
    member_id = ""
    experiment_id = ""
    source_id = ""
    chunk_freq = file.parts[num_dir_parts - 2]  # e.g, 1yr, 5yr
    variant_label = ""
    grid_label = ""
    table_id = ""
    assoc_files = ""
    activity_id = "GFDL"
    institution_id = ""
    long_name = ""
    standard_name = ""
    units = ""
    output_frequency = ""
    file_freq = file.parts[num_dir_parts - 3]

    for f in freq_opts:
        if f in file_freq:
            output_frequency = f
            break
    if 'daily' in output_frequency:
        output_frequency = 'day'
    elif 'monthly' in output_frequency:
        output_frequency = 'mon'

        # read metadata from the appropriate fieldlist
    if 'cmip' in realm.lower():
        gfdl_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_CMIP.jsonc')
    else:
        gfdl_fieldlist = os.path.join(ROOT_DIR, 'data/fieldlist_GFDL.jsonc')
    try:
        gfdl_info = read_json(gfdl_fieldlist, log=_log)
    except IOError:
        print("Unable to open file", gfdl_fieldlist)
        sys.exit(1)

    if hasattr(gfdl_info['variables'], variable_id):
        var_metadata = gfdl_info['variables'].get(variable_id)
    else:
        raise KeyError(f'{variable_id} not found in {gfdl_fieldlist}')

    if hasattr(var_metadata, 'standard_name'):
        standard_name = var_metadata.standard_name
    if hasattr(var_metadata, 'long_name'):
        long_name = var_metadata.long_name
    if hasattr(var_metadata, 'units'):
        units = var_metadata.units

    try:
        info = {
            'activity_id': activity_id,
            'assoc_files': assoc_files,
            'institution_id': institution_id,
            'member_id': member_id,
            'realm': realm,
            'variable_id': variable_id,
            'table_id': table_id,
            'source_id': source_id,
            'source_type': source_type,
            'cell_methods': cell_methods,
            'cell_measures': cell_measures,
            'experiment_id': experiment_id,
            'variant_label': variant_label,
            'grid_label': grid_label,
            'units': units,
            'time_range': time_range,
            'start_time': start_time,
            'end_time': end_time,
            'chunk_freq': chunk_freq,
            'standard_name': standard_name,
            'long_name': long_name,
            'frequency': output_frequency,
            'file_name': stem,
            'path': str(file)
        }

        return info

    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}


# custom parser for pp data stored on GFDL archive filesystem
# assumed DRS of [root_dir]/pp/[realm]/[analysis type (e.g, 'ts')]/[frequency]/[chunk size (e.g., 1yr, 5yr)]

def parse_gfdl_pp_ts(file_name: str):
    # files = sorted(glob.glob(os.path.join(file_name,'*.nc')))  # debug comment when ready to run
    # file = pathlib.Path(files[0])  # debug comment when ready to run
    file = pathlib.Path(file_name)  # uncomment when ready to run
    num_parts = len(file.parts)  # file name index = num_parts 1
    # isolate file from rest of path
    stem = file.stem
    # split the file name into components based on _
    split = stem.split('.')
    realm = split[0]
    cell_methods = ""
    cell_measures = ""
    time_range = split[1]
    start_time = time_range.split('-')[0]
    end_time = time_range.split('-')[1]
    variable_id = split[2]
    source_type = ""
    member_id = ""
    experiment_id = ""
    source_id = ""
    chunk_freq = file.parts[num_parts - 2]  # e.g, 1yr, 5yr
    variant_label = ""
    grid_label = ""
    table_id = ""
    assoc_files = ""
    activity_id = "GFDL"
    institution_id = ""

    output_frequency = ""
    file_freq = file.parts[num_parts - 3]
    for f in freq_opts:
        if f in file_freq:
            output_frequency = f
            break
    if 'daily' in output_frequency:
        output_frequency = 'day'
    elif 'monthly' in output_frequency:
        output_frequency = 'mon'

    try:
        # call to xr.open_dataset required by ecgtoos.builder.Builder
        with xr.open_dataset(file, chunks={}, decode_times=False) as ds:
            variable_list = [var for var in ds if 'standard_name' in ds[var].attrs or 'long_name' in ds[var].attrs]
            if variable_id not in variable_list:
                print(f'Asset variable {variable_id} not found in {file}')
                exit(1)
            standard_name = ""
            long_name = ""
            if 'standard_name' in ds[variable_id].attrs:
                standard_name = ds[variable_id].attrs['standard_name']
                standard_name.replace("", "_")
            if 'long_name' in ds[variable_id].attrs:
                long_name = ds[variable_id].attrs['long_name']
            if len(long_name) == 0 and len(standard_name) == 0:
                print('Asset variable does not contain a standard_name or long_name attribute')
                exit(1)

            if 'cell_methods' in ds[variable_id].attrs:
                cell_methods = ds[variable_id].attrs['cell_methods']
            if 'cell_measures' in ds[variable_id].attrs:
                cell_measures = ds[variable_id].attrs['cell_measures']

            units = ds[variable_id].attrs['units']
            info = {
                'activity_id': activity_id,
                'assoc_files': assoc_files,
                'institution_id': institution_id,
                'member_id': member_id,
                'realm': realm,
                'variable_id': variable_id,
                'table_id': table_id,
                'source_id': source_id,
                'source_type': source_type,
                'cell_methods': cell_methods,
                'cell_measures': cell_measures,
                'experiment_id': experiment_id,
                'variant_label': variant_label,
                'grid_label': grid_label,
                'units': units,
                'time_range': time_range,
                'start_time': start_time,
                'end_time': end_time,
                'chunk_freq': chunk_freq,
                'standard_name': standard_name,
                'long_name': long_name,
                'frequency': output_frequency,
                'file_name': stem,
                'path': str(file)
            }

            return info

    except Exception as exc:
        print(exc)
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}
