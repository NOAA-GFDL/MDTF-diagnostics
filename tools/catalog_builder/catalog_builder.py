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
import intake
from ecgtools import Builder
from ecgtools.parsers.cesm import parse_cesm_timeseries
from ecgtools.parsers.cmip import parse_cmip_timeseries
import click

# The ClassMaker is cribbed from SO
# https://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
# It allows


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
        self.joblib_parallel_kwargs = {'n_jobs': -1}  # default parallel jobs
        self.depth = 1  # default directory depth to traverse when searching data_paths
        self.cb = None

    def cat_builder(self, data_paths: list,
                    exclude_patterns=None):
        if exclude_patterns is None:
            exclude_patterns = ["DO_NOT_USE"]
        self.cb = Builder(paths=data_paths,
                          depth=self.depth,
                    # Exclude the following directories
                    exclude_patterns=exclude_patterns,
                    # Number of jobs to execute - should be equal to # threads you are using
                    joblib_parallel_kwargs=self.joblib_parallel_kwargs,
                          )

    def cat_save(self, output_dir: str, output_filename: str):
        return self.save(
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


@catalog_class.maker
class CatalogCMIP(CatalogBase):
    """Class to generate CMIP data catalogs\n
    """

    def build(self):
        return self.build(parse_cmip_timeseries)


@catalog_class.maker
class CatalogGFDL(CatalogBase):
    """Class to generate GFDL data catalogs\n
    """

    def build(self):
        pass
        # TODO create parse_gfdl_timeseries module and
        # submit PR to ecgtools
        # return self.build(parse_gfdl_timeseries)


@catalog_class.maker
class CatalogCESM(CatalogBase):
    """Class to generate CESM data catalogs\n
    """

    def build(self):
        return self.build(parse_cesm_timeseries)


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

    # instantiate the builder class instance for the specified convention
    cat_builder = catalog_class["Catalog" + convention.upper()]
    # initialize the esm-intake builder object
    cat_builder.builder(data_paths=data_paths,
                        exclude_patterns=exclude_patterns)


    cat_builder = cat_builder.build()
    # save the catalog
    cat_builder.save(output_dir, output_filename)


