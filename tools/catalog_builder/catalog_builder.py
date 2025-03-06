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
import sys
import time
import typing
import yaml
import parsers
from datetime import timedelta
from ecgtools import Builder
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
        self.file_parse_method = ""

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
                          joblib_parallel_kwargs={'n_jobs': nthreads}  # Number of jobs to execute -
                          # should be equal to # threads you are using
                          )

    def call_build(self, file_parse_method=None):
        if file_parse_method is None:
            file_parse_method = self.file_parse_method
        # see https://github.com/ncar-xdev/ecgtools/blob/main/ecgtools/parsers/cmip6.py
        # for more parsing methods
        self.cb = self.cb.build(parsing_func=file_parse_method)
        print('Build complete')

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
        self.file_parse_method = parse_cmip6


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
        self.file_parse_method = parsers.parse_gfdl_pp_ts


@catalog_class.maker
class CatalogCESM(CatalogBase):
    """Class to generate CESM data catalogs\n
    Note that class attributes are defined based on the example for
    building catalogs for CESM timeseries data provided by ecgtools.
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
        self.file_parse_method = parsers.parse_cesm


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
            file_parse_method = parsers.parse_gfdl_am5_data

    # build the catalog
    print('Building the catalog')
    start_time = time.monotonic()

    cat_obj.call_build(file_parse_method=file_parse_method)

    end_time = time.monotonic()

    print("Time to build catalog:", timedelta(seconds=end_time - start_time))
    # save the catalog
    print('Saving catalog to',conf['output_dir'],'/',conf['output_filename'] + ".csv")

    cat_obj.call_save(output_dir=conf['output_dir'],
                      output_filename=conf['output_filename']
                      )
    print('Catalog builder has completed successfully.')
    sys.exit(0)


if __name__ == '__main__':
    main(prog_name='ESM-Intake Catalog Maker')
