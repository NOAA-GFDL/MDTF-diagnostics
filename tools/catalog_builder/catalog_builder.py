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
import glob
import intake
import os
import pathlib
import traceback
import xarray as xr
import yaml
from datetime import datetime
from ecgtools import Builder
from ecgtools.builder import INVALID_ASSET, TRACEBACK
from ecgtools.parsers.cesm import parse_cesm_timeseries
from ecgtools.parsers import parse_cmip6


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

# custom parser for data stored on GFDL uda
# TODO: move to separate module and submit PR to ecg-tools repo
def parse_gfdl_uda(file_name: str):
    #files = sorted(glob.glob(os.path.join(root_dir,'*/*/*/*/*/*/*.nc')))
    #file = pathlib.Path(files[0])
    file = pathlib.Path(file_name[0])
    info = dict()

    try:
        # isolate file from rest of path
        stem = file.stem
        # split the file name into components based on _
        split = stem.split('_')
        variable_id = split[0]
        table_id = split[1]
        source_id = split[2]
        experiment_id = split[3]
        variant_label = split[4]
        grid_label = split[5]
        date_range = split[6]
        if 'mon' in table_id.lower():
            output_frequency = 'mon'
        elif 'day' in table_id.lower():
            output_frequency = 'day'
        elif '6hr' in table_id.lower():
            output_frequency = '6hr'
        elif 'subhr' in table_id.lower():
            output_frequency = 'subhr'

        with xr.open_dataset(file, chunks={}, decode_times=False) as ds:
            variable_list = [var for var in ds if 'standard_name' in ds[var].attrs]

            info = {
                'sample_dataset': source_id,
                'variable_id': variable_id,
                'table_id': table_id,
                'source_id': source_id,
                'experiment_id': experiment_id,
                'variant_label': variant_label,
                'grid_label': grid_label,
                'date_range': date_range,
                'frequency': output_frequency,
                'variable': variable_list[0],
                'file_name': stem,
                'path': str(file),
            }

        return info

    except Exception:
        return {INVALID_ASSET: file, TRACEBACK: traceback.format_exc()}


class CatalogBase(object):
    """Catalog base class\n
    """

    def __init__(self):
        self.joblib_parallel_kwargs = {'n_jobs': -1}  # default parallel jobs
        self.groupby_attrs = ["component", "stream", "case"]  # attributes to group by when reading
        # in variables using intake-esm
        self.xarray_aggregations = [
                {'type': 'union', 'attribute_name': 'variable'},
                {
                    "type": "join_existing",
                    "attribute_name": "time_range",
                    "options": {"dim": "time", "coords": "minimal", "compat": "override"},
                },
            ],
        self.data_format = "netcdf" # netcdf or zarr
        self.cb = None

    def cat_builder(self, data_paths: list,
                    exclude_patterns=None,
                    dir_depth=1
                    ):
        if exclude_patterns is None:
            exclude_patterns = ["DO_NOT_USE"]
        self.cb = Builder(paths=data_paths,
                          depth=dir_depth,
                          exclude_patterns=exclude_patterns,  # Exclude the following directories
                          joblib_parallel_kwargs=self.joblib_parallel_kwargs,  # Number of jobs to execute -
                          # should be equal to # threads you are using
                          extension='.nc'  # extension of target files
                          )

    def cat_save(self, output_dir: str,
                 output_filename: str
                 ):
        self.cb.save(
            os.path.join(output_dir, output_filename),
            # Column name including filepath
            path_column_name='path',
            # Column name including variables
            variable_column_name='variable',
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
        self.groupby_attrs = [
            'activity_id',
            'institution_id',
            'source_id',
            'experiment_id',
            'table_id',
            'grid_label'
        ],
        self.xarray_aggregations = [
            {'type': 'union', 'attribute_name': 'variable_id'},
            {
                'type': 'join_existing',
                'attribute_name': 'date_range',
                'options': {'dim': 'time', 'coords': 'minimal', 'compat': 'override'},
            }
        ]

    def cat_builder(self, data_paths: list,
                    exclude_patterns=None,
                    dir_depth=1
                    ):

        self.cb = Builder(paths=data_paths, depth=dir_depth, njobs=4)

    def call_build(self, file_parse_method=None):
        if file_parse_method is None:
            file_parse_method = parse_cmip6
        # see https://github.com/ncar-xdev/ecgtools/blob/main/ecgtools/parsers/cmip6.py
        # for more parsing methods
        self.cb = self.cb.build(parsing_func=file_parse_method)
        print('RRR')


@catalog_class.maker
class CatalogGFDL(CatalogBase):
    """Class to generate GFDL data catalogs\n
    """

    def call_build(self):
        pass
        # TODO create parse_gfdl_timeseries module and
        # submit PR to ecgtools
        # return self.build(parse_gfdl_timeseries)


@catalog_class.maker
class CatalogCESM(CatalogBase):
    """Class to generate CESM data catalogs\n
    """
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
        data_obj = parse_gfdl_uda(p)  # debug custom parser


    # instantiate the builder class instance for the specified convention
    cat_cls = catalog_class["Catalog" + conf['convention'].upper()]
    # initialize the catalog object
    cat_obj = cat_cls()
    # instantiate the esm catalog builder
    cat_obj.cat_builder(data_paths=conf['data_root_dirs'],
                        exclude_patterns=conf['exclude_patterns'],
                        dir_depth=conf['dir_depth']
                        )
    # build the catalog
    print('Building the catalog')
    cat_obj.call_build()
    # save the catalog
    print('Saving catalog to', conf['output_filename'])
    cat_obj.save(output_dir=conf['output_dir'],
                 output_filename=conf['output_filename']
                 )

if __name__ == '__main__':
    main(prog_name='ESM-Intake Catalog Maker')
