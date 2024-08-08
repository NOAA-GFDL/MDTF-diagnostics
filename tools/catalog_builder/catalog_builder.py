# ======================================================================
# NOAA Model Diagnostics Task Force (MDTF)
# ======================================================================
# USAGE: Build esm-intake catalogs for files stored using CMIP6, CESM, or GFDL
# DRSs
#
# Input:
# Configuration yaml file with the directory containing the input data,
# the directory where the output will be written, the CASENAME to use for the output file names,
# the file names that will be linked,
# and the frequencies and variable names to use in the new symlinked file names
# Output: esm-intake catalog in csv format with the file locations and metadata required
# for the preprocessor and the MDTF-diagnostics framework

import click
import intake
import os
import io
import json
import pathlib
import sys
import time
import traceback
import typing
import collections
import xarray as xr
import yaml
from datetime import timedelta
from ecgtools import Builder
from ecgtools.builder import INVALID_ASSET, TRACEBACK
from ecgtools.parsers.cmip import parse_cmip6
from ecgtools.parsers.cesm import parse_cesm_timeseries
import logging

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)).split('/tools/catalog_builder')[0]
assert(os.path.isdir(ROOT_DIR)), f'{ROOT_DIR} not found'
# from src import util

# Define a log object for debugging
_log = logging.getLogger(__name__)
# The ClassMaker is cribbed from SO
# https://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
# Classmaker and the @catalog_class.maker decorator allow class instantiation from
# strings. The main block can simply call the desired class using the convention
# argument instead of messy if/then/else blocks. Yes, both work, but I wanted
# to try something that, if it is not more "Pythonic", is more extensible


class ClassMaker:
    def __init__(self):
        self.classes = {}

    def add_class(self, c):
        self.classes[c.__name__] = c

    # define the class decorator to return the class passed
    def maker(self, c):
        self.add_class(c)
        return c

    def __getitem__(self, n):
        return self.classes[n]


# instantiate the class maker
catalog_class = ClassMaker()

def strip_comments(str_: str, delimiter=None):
    """Remove comments from *str_*. Comments are taken to start with an
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

freq_opts = ['mon',
             'day',
             'daily',
             '6hr',
             '3hr',
             '1hr',
             'subhr',
             'annual',
             'year']

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


class CatalogBase(object):
    """Catalog base class\n
    """

    def __init__(self):
        self.groupby_attrs = [
            'activity_id',
            'institution_id',
            'source_id',
            'experiment_id',
            'frequency',
            'member_id',
            'table_id',
            'grid_label',
            'realm',
            'variant_label'
        ]  # attributes to group by when reading
        # in variables using intake-esm
        self.xarray_aggregations = [
            {'type': 'union', 'attribute_name': 'variable_id'}
        ]
        self.data_format = "netcdf" # netcdf or zarr
        self.variable_col_name = "variable_id"
        self.path_col_name = "path"
        self.cb = None

    def cat_builder(self, data_paths: list,
                    exclude_patterns=None,
                    include_patterns=None,
                    dir_depth=1,
                    nthreads=-1
                    ):
        if exclude_patterns is None:
            exclude_patterns: typing.List[str] = None
        if include_patterns is None:
            include_patterns: typing.List[str] = None
        self.cb = Builder(paths=data_paths,
                          depth=dir_depth,
                          exclude_patterns=exclude_patterns,  # Exclude the following directories
                          include_patterns=include_patterns,
                          joblib_parallel_kwargs={'n_jobs': nthreads},  # Number of jobs to execute -
                          # should be equal to # threads you are using
                          extension='.nc' # extension of target file
                          )

    def call_save(self, output_dir: str,
                  output_filename: str
                  ):
        self.cb.save(
            # name of the catalog
            name=output_filename,
            # directory where catalog will be written
            directory=os.path.join(output_dir),
            # Column name including filepath
            path_column_name=self.path_col_name,
            # Column name including variables
            variable_column_name=self.variable_col_name,
            # Data file format - could be netcdf or zarr (in this case, netcdf)
            data_format=self.data_format,
            # Which attributes to group by when reading in variables using intake-esm
            groupby_attrs=self.groupby_attrs,
            # Aggregations which are fed into xarray when reading in data using intake
            aggregations=self.xarray_aggregations
        )


@catalog_class.maker
class CatalogCMIP(CatalogBase):
    """Class to generate CMIP data catalogs\n
    """

    def __init__(self):
        super().__init__()

    def call_build(self, file_parse_method=None):
        if file_parse_method is None:
            file_parse_method = parse_cmip6
        # see https://github.com/ncar-xdev/ecgtools/blob/main/ecgtools/parsers/cmip6.py
        # for more parsing methods
        self.cb = self.cb.build(parsing_func=file_parse_method)
        print('Build complete')


@catalog_class.maker
class CatalogGFDL(CatalogBase):
    """Class to generate GFDL data catalogs\n
    """
    def __init__(self):
        super().__init__()
        self.groupby_attrs = [
            'activity_id',
            'institution_id',
            'experiment_id',
            'frequency',
            'member_id',
            'realm'
        ]
    def call_build(self,
                   file_parse_method=None):

        if file_parse_method is None:
            file_parse_method = parse_gfdl_pp_ts
        # see https://github.com/ncar-xdev/ecgtools/blob/main/ecgtools/parsers/cmip6.py
        # for more parsing methods
        self.cb = self.cb.build(parsing_func=file_parse_method)
        print('Build complete')


@catalog_class.maker
class CatalogCESM(CatalogBase):
    """Class to generate CESM data catalogs\n
    Note that class attributes are defined based on the example for
    building catalogs for CESM timeseries data provided by ecgtools.
    """
    def __init__(self):
        super().__init__()
        self.groupby_attrs = [
            'component',
            'stream',
            'case',
            'frequency'
        ]

        self.xarray_aggregations = [
            {'type': 'union', 'attribute_name': 'variable_id'},
            {
                'type': 'join_existing',
                'attribute_name': 'date',
                'options': {'dim': 'time', 'coords': 'minimal', 'compat': 'override'}
            }
        ]

    def call_build(self, file_parse_method=None):
        if file_parse_method is None:
            file_parse_method = parse_cesm_timeseries
        # see https://github.com/ncar-xdev/ecgtools/blob/main/ecgtools/parsers/cesm.py
        # for more parsing methods
        self.cb = self.cb.build(parsing_func=file_parse_method)


def load_config(config):
    if os.path.exists(config):
        with open(config, 'r') as f:
            return yaml.safe_load(f.read())


@click.option('--config',
              type=click.Path(),
              help='Path to config file'
              )
@click.command()
def main(config: str):
    """A tool to generate intake-esm catalogs of datasets to preprocess for use with the MDTF-diagnostics package"""
    conf = load_config(config)
    for p in conf['data_root_dirs']:
        try:
            os.path.isdir(p)
        except FileNotFoundError:
            print("{p} not found. Check data_root_dirs for typos.")
        # data_obj = parse_gfdl_pp_ts(p)  # debug custom parser

    # instantiate the builder class instance for the specified convention
    cat_cls = catalog_class["Catalog" + conf['convention'].upper()]
    # initialize the catalog object
    cat_obj = cat_cls()
    # instantiate the esm catalog builder
    opt_keys = ['include_patterns', 'exclude_patterns', 'dataset_id']
    for k in opt_keys:
        if k not in conf:
            conf[k] = None

    cat_obj.cat_builder(data_paths=conf['data_root_dirs'],
                        exclude_patterns=conf['exclude_patterns'],
                        include_patterns=conf['include_patterns'],
                        dir_depth=conf['dir_depth'],
                        nthreads=conf['num_threads']
                        )

    file_parse_method = None
    if conf['dataset_id'] is not None:
        if 'am5' in conf['dataset_id'].lower():
            file_parse_method = parse_gfdl_am5_data

    # build the catalog
    print('Building the catalog')
    start_time = time.monotonic()

    cat_obj.call_build(file_parse_method=file_parse_method)

    end_time = time.monotonic()

    print("Time to build catalog:", timedelta(seconds=end_time - start_time))
    # save the catalog
    print('Saving catalog to', conf['output_dir'],'/',conf['output_filename'] + ".csv")

    cat_obj.call_save(output_dir=conf['output_dir'],
                      output_filename=conf['output_filename']
                      )
    print('Catalog builder has completed successfully.')
    sys.exit(0)


if __name__ == '__main__':
    main(prog_name='ESM-Intake Catalog Maker')
