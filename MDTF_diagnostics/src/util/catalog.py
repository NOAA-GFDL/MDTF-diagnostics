""" Utilities for constructing ESM-intake catalogs for processed data
 Source:
 https://gitlab.dkrz.de/data-infrastructure-services/intake-esm/-/blob/master/builder/notebooks/dkrz_era5_disk_catalog.ipynb
"""
import fnmatch
import datetime
import dask
from intake.source.utils import reverse_format
import os
import re
import subprocess
from pathlib import Path
import itertools
import logging
from src import cli
from . import ClassMaker

_log = logging.getLogger(__name__)


def get_file_list(output_dir: str) -> list:
    """Get a list of files in a directory"""

    cmd = ['find', output_dir, '-mindepth', '1', '-maxdepth', '5', '-type', "d"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    output = proc.stdout.read().decode('utf-8').split()
    dirs = [Path(entry) for entry in output]

    @dask.delayed
    def _file_dir_files(directory):
        try:
            cmd = ['find', '-L', directory.as_posix(), '-name', '*.nc', '-type', "f"]
            proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            output = proc.stdout.read().decode('utf-8').split()
        except Exception as exc:
            print(exc)
            output = []
        return output

    print('Getting list of assets...\n')
    filelist = [_file_dir_files(d) for d in dirs]

    filelist = dask.compute(*filelist)

    filelist = set(list(itertools.chain(*filelist)))
    new_filelist = list(filelist)
    return new_filelist


def define_pp_catalog_assets(config, cat_file_name: str) -> dict:
    """ Define the version and attributes for the post-processed data catalog"""
    cmip6_cv_info = cli.read_config_file(config.CODE_ROOT,
                                         "data/cmip6-cmor-tables/Tables",
                                         "CMIP6_CV.json")

    cat_dict = {'esmcat_version': datetime.datetime.today().strftime('%Y-%m-%d'),
                'description': 'Post-processed dataset for MDTF-diagnostics package',
                'attributes': []
                }

    for att in cmip6_cv_info['CV']['required_global_attributes']:
        if att == 'variant_label':
            att = "member_id"
        cat_dict["attributes"].append(
            dict(column_name=att,
                 vocabulary=f"https://github.com/WCRP-CMIP/CMIP6_CVs/blob/master/"
                            f"CMIP6_required_global_attributes.json"
                 )
        )

    # add columns required for GFDL/CESM institutions and MDTF-diagnostics functionality
    append_atts = ['chunk_freq', 'path', 'standard_name', "time_range"]
    for att in append_atts:
        cat_dict["attributes"].append(
            dict(column_name=att)
        )

    cat_dict["assets"] = {
        "column_name": "path",
        "format": "netcdf"
    }
    cat_dict["aggregation_control"] = {
        "variable_column_name": "variable_id",
        "groupby_attrs": [
            "institution_id",
            "source_id",
            "member_id",
            "experiment_id",
            "frequency",
            "table_id",
            "grid_label",
            "realm",
            "chunk_freq",
            "variant_label"
        ],
        "aggregations": [
            {
                "type": "union",
                "attribute_name": "variable_id",
                "options": {}
            }
        ]
    }
    
    # check groupby_attrs to prevent Key Error in PODs
    for att in cat_dict["aggregation_control"]["groupby_attrs"]:
        if att not in cat_dict["attributes"]:
            cat_dict["attributes"].append(
                dict(column_name=att)
            )


    return cat_dict
