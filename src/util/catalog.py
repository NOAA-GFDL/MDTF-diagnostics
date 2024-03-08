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

_log = logging.getLogger(__name__)


def _reverse_filename_format(file_basename, filename_template=None, gridspec_template=None):
    """
    Uses intake's ``reverse_format`` utility to reverse the string method format.
    Given format_string and resolved_string, find arguments
    that would give format_string.format(arguments) == resolved_string
    """
    try:
        return reverse_format(filename_template, file_basename)
    except ValueError:
        try:
            return reverse_format(gridspec_template, file_basename)
        except Exception as exc:
            print(
                f'Failed to parse file: {file_basename} using patterns: {filename_template}: {exc}'
            )
            return {}


def _extract_attr_with_regex(input_str: str, regex: str, strip_chars=None):
    pattern = re.compile(regex, re.IGNORECASE)
    match = re.findall(pattern, input_str)
    if match:
        match = max(match, key=len)
        if isinstance(match, tuple):
            match = ''.join(match)
        if strip_chars:
            match = match.strip(strip_chars)
        return match
    else:
        return None


exclude_patterns = ['*/files/*', '*/latest/*']


def _filter_func(path: str) -> bool:
    return not any(
        fnmatch.fnmatch(path, pat=exclude_pattern) for exclude_pattern in exclude_patterns
    )


def mdtf_pp_parser(file_path: str) -> dict:
    """ Extract attributes of a file using information from MDTF OUTPUT DRS
    """
    # get catalog in information from pp file name
    freq_regex = r'/1hr/|/3hr/|/6hr/|/day/|/fx/|/mon/|/monClim/|/subhr/|/seas/|/yr/'
    # YYYYMMDD:HHMMSS-YYYYMMDD:HHMMSS
    # (([numbers in range 0-9 ]{repeat previous exactly 4 time}[numbers in range 0-1]
    # [numbers in range 0-9][numbers in range 0-3][numbers in range 0-9])
    # (optional colon)(([numbers in range 0-2][numbers in range 0-3])([numbers in range 0-5][numbers in range 0-9])
    # {repeat previous exactly 2 times})*=0 or more of the HHMMSS group
    # -(repeat the same regex for the second date string in the date range)
    time_range_regex = r'([0-9]{4}[0-1][0-9][0-3][0-9])' \
                       r'(:?)(([0-2][0-3])([0-5][0-9]){2})*' \
                       r'(-)([0-9]{4}[0-1][0-9][0-3][0-9])' \
                       r'(:?)(([0-2][0-3])([0-5][0-9]){2})*'
    file_basename = os.path.basename(file_path)

    filename_template = (
        '{dataset_name}.{variable_id}.{frequency}.nc'
    )

    f = _reverse_filename_format(file_basename, filename_template=filename_template)
    #  ^..^
    # /o  o\
    # oo--oo~~~
    cat_entry = dict()
    cat_entry.update(f)
    cat_entry['path'] = file_path
    cat_entry['frequency'] = _extract_attr_with_regex(file_path, regex=freq_regex, strip_chars='/')
    cat_entry['time_range'] = _extract_attr_with_regex(cat_entry['dataset_name'], regex=time_range_regex)
    cat_entry['experiment_id'] = cat_entry['dataset_name'].split('_' + cat_entry['time_range'])[0]

    return cat_entry


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
        if att == 'Conventions':
            att = "convention"
        cat_dict["attributes"].append(
            dict(column_name=att,
                 vocabulary=f"https://github.com/WCRP-CMIP/CMIP6_CVs/blob/master/"
                            f"CMIP6_required_global_attributes.json"
                 )
        )

    cat_dict["assets"] = {
        "column_name": "path",
        "format": "netcdf"
    }
    cat_dict["aggregation_control"] = {
        "variable_column_name": "variable_id",
        "groupby_attrs": [
            "activity_id",
            "institution_id",
            "source_id",
            "experiment_id",
            "frequency",
            "table_id",
            "grid_label",
            "realm",
            "variant_label",
            "time_range"
        ],
        "aggregations": [
            {
                "type": "union",
                "attribute_name": "variable_id",
                "options": {}
            },
            {
                "type": "join_existing",
                "attribute_name": "time_range",
                "options": {"dim": "time", "coords": "minimal", "compat": "override"}
            }
        ]
    }

    return cat_dict
