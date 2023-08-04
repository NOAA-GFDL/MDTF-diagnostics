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
import pathlib
import sys
import time
import traceback
import typing
import xarray as xr
import yaml
from datetime import datetime, timedelta
from ecgtools import Builder
from ecgtools.builder import INVALID_ASSET, TRACEBACK
from ecgtools.parsers import parse_cmip6
from ecgtools.parsers.cesm import parse_cesm_timeseries


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


# custom parser for pp data stored on GFDL archive filesystem
def parse_gfdl_pp_ts(file_name: str):
    # files = sorted(glob.glob(os.path.join(file_name,'*.nc')))  # debug comment when ready to run
    # file = pathlib.Path(files[0])  # debug comment when ready to run
    file = pathlib.Path(file_name)  # uncomment when ready to run

    try:
        # isolate file from rest of path
        stem = file.stem
        # split the file name into components based on _
        split = stem.split('.')
        realm = split[0]
        time_range = split[1]
        variable_id = split[2]
        source_type = file.parts[3]
        member_id = file.parts[4]
        experiment_id = file.parts[5]
        source_id = file.parts[6]
        freq = file.parts[10]
        chunk_freq = file.parts[11]
        variant_label = ""
        grid_label = ""
        table_id = ""
        assoc_files = ""
        if 'mon' in freq.lower():
            output_frequency = 'mon'
        elif 'day' in freq.lower():
            output_frequency = 'day'
        elif '6hr' in freq.lower():
            output_frequency = '6hr'
        elif 'subhr' in freq.lower():
            output_frequency = 'subhr'

        # call to xr.open_dataset required by ecgtoos.builder.Builder
        with xr.open_dataset(file, chunks={}, decode_times=False) as ds:
            # variable_list = [var for var in ds if 'standard_name' in ds[var].attrs or 'long_name' in ds[var].attrs]
            # assert(variable_id in variable_list), \
            # "Did not find variable with standard_name or long_name {variable_id}" \
            # "in {file}"
            info = {
                'activity_id': source_id,
                'assoc_files': assoc_files,
                'institution_id': "GFDL",
                'member_id': member_id,
                'realm': realm,
                'variable_id': variable_id,
                'table_id': table_id,
                'source_id': source_id,
                'source_type': source_type,
                'experiment_id': experiment_id,
                'variant_label': variant_label,
                'grid_label': grid_label,
                'time_range': time_range,
                'chunk_freq': chunk_freq,
                'frequency': output_frequency,
                'variable': variable_id,
                'file_name': stem,
                'path': str(file)
            }

            return info

    except Exception:
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
            'variant_label',
            'time_range'
        ]  # attributes to group by when reading
        # in variables using intake-esm
        self.xarray_aggregations = [
            {'type': 'union', 'attribute_name': 'variable_id'},
            {
                'type': 'join_existing',
                'attribute_name': 'time_range',
                'options': {'dim': 'time', 'coords': 'minimal', 'compat': 'override'}
            }
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
                          extension='.nc'  # extension of target files
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
            'realm',
            'time_range'
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
        self.cb.build(file_parse_method)


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
    opt_keys = ['include_patterns', 'exclude_patterns']
    for k in opt_keys:
        if k not in conf:
            conf[k] = None

    cat_obj.cat_builder(data_paths=conf['data_root_dirs'],
                        exclude_patterns=conf['exclude_patterns'],
                        include_patterns=conf['include_patterns'],
                        dir_depth=conf['dir_depth'],
                        nthreads=conf['num_threads']
                        )
    # build the catalog
    print('Building the catalog')
    start_time = time.monotonic()

    cat_obj.call_build()

    end_time = time.monotonic()

    print("Time to build catalog:", timedelta(seconds=end_time - start_time))
    # save the catalog
    print('Saving catalog to', conf['output_filename'] + ".csv")
    cat_obj.call_save(output_dir=conf['output_dir'],
                      output_filename=conf['output_filename']
                      )
    print('Catalog builder has completed successfully.')
    sys.exit(0)


if __name__ == '__main__':
    main(prog_name='ESM-Intake Catalog Maker')
