# ======================================================================
# NOAA Model Diagnostics Task Force (MDTF)
#
# Rename input files
#
# ======================================================================
# Usage
#
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


import os
from abc import ABC, abstractmethod
import shutil
import sys
import yaml
from pathlib import Path
import dask
import intake
from ecgtools import Builder
from ecgtools.parsers.cesm import parse_cesm_timeseries
import click


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


@catalog_class.maker
class CatalogCMIP(CatalogBase, ABC):
    """Class to generate CMIP data catalogs\n
    """

    def cat_builder(self, *args, **kwargs):
        pass

    def drs(self):
        pass

    class CatalogGFDL(CatalogBase, ABC):
        """Class to generate GFDL data catalogs\n
        """

        def cat_builder(self, *args, **kwargs):
            pass

        def drs(self):
            pass

    class CatalogCESM(CatalogBase, ABC):
        """Class to generate CESM data catalogs\n
        """

        def cat_builder(self, *args, **kwargs):
            pass

        def drs(self):
            pass


@click.command()
@click.option('--data_paths',
              type=list,
              help='List of path(s) to the root directory(ies) with the desired files')
@click.option('--convention',
              default='cmip',
              type=click.Choice(['cmip', 'gfdl', 'cesm', 'ncar']),
              help='DRS convention')
@click.option('--output_dir',
              default='./',
              help='Directory where catalog csv file will be written (default current working directory')
@click.option('--output_filename',
              default='catalog.csv',
              help='Name of the data catalog csv file')
@click.option('--exclude_patterns',
              type=list,
              help='List of directories or wildcard patterns to exclude from catalog')
def main(data_paths: list, convention: str, output_dir: str, output_filename: str, exclude_patterns:list=[]):
    """A tool to generate intake-esm catalogs of datasets to preprocess for use with the MDTF-diagnostics package"""
    for p in data_paths:
        try:
            os.path.isdir(p)
        except FileNotFoundError:
            print("{p} not found. Check data_paths for typos.")

    cat_builder = Builder(
        # Archive directory with GFDL pp model output
        paths=data_paths,
        # Depth of 4 since we are traversing the component/ts/freq/chunk directory
        depth=4,
        # Exclude the following directories
        exclude_patterns=["*/av/*", "*DO_NOT_USE"],
        # Number of jobs to execute - should be equal to # threads you are using
        joblib_parallel_kwargs={'n_jobs': -1},
    )
    cat_builder  # instantiate a builder object for the pp directory

    cat_builder = cat_builder.build(parse_cesm_timeseries)
    # save the catalog
    cat_builder.save(
        os.path.join(output_dir, output_filename),
        # Column name including filepath
        path_column_name='path',
        # Column name including variables
        variable_column_name='variable',
        # Data file format - could be netcdf or zarr (in this case, netcdf)
        data_format="netcdf",
        # Which attributes to groupby when reading in variables using intake-esm
        groupby_attrs=["component", "stream", "case"],
        # Aggregations which are fed into xarray when reading in data using intake
        aggregations=[
            {'type': 'union', 'attribute_name': 'variable'},
            {
                "type": "join_existing",
                "attribute_name": "time_range",
                "options": {"dim": "time", "coords": "minimal", "compat": "override"},
            },
        ],
    )

