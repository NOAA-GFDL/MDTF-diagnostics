""" Utilities for constructing ESM-intake catalogs for processed data
 Source:
 https://gitlab.dkrz.de/data-infrastructure-services/intake-esm/-/blob/master/builder/notebooks/dkrz_era5_disk_catalog.ipynb
"""
import pandas as pd
import fnmatch
import dask.dataframe as dd
import dask
from intake.source.utils import reverse_format
import os
import re
import subprocess
from pathlib import Path
import shutil
import numpy as np
import datetime
import xarray
from functools import lru_cache
import itertools
import logging

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


def _extract_attr_with_regex(input_str: str, regex, strip_chars=None):
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

    freq_regex = r'/1hr/|/3hr/|/6hr/|/day/|/fx/|/mon/|/monClim/|/subhr/|/seas/|/yr/'
    # YYYYMMDD:HHMMSS-YYYYMMDD:HHMMSS
    # (word boundary ([numbers in range 0-9 ]{repeat previous exactly 4 time})([numbers in range 0-1]
    # [numbers in range 0-9])([numbers in range 0-3][numbers in range 0-9])
    # (optional colon)(([numbers in range 0-2][numbers in range 0-3])([numbers in range 0-5][numbers in range 0-9])
    # {repeat previous exactly 2 times})*=0 or more of the HHMMSS group, word boundary
    # -[repeat the same regex for the second date string in the date range
    time_range_regex = (r'([0-9]{4}[0-1][0-9][0-3][0-9])'
                        r'(:?)(([0-2][0-3])([0-5][0-9]){2})*'
                        r'(-)([0-9]{4}[0-1][0-9][0-3][0-9])'
                        r'(:?)(([0-2][0-3])([0-5][0-9]){2})*')
    file_basename = os.path.basename(file_path)

    filename_template = (
        '{dataset_name}.{variable}.{frequency}.nc'
    )

    f = _reverse_filename_format(file_basename, filename_template=filename_template)
    fileparts = dict()
    fileparts.update(f)
    fileparts['frequency'] = _extract_attr_with_regex(file_path, regex=freq_regex, strip_chars='/')
    fileparts['time_range'] = _extract_attr_with_regex(fileparts['dataset_name'], regex=time_range_regex)

    fileparts['path'] = file_path
    try:
        part1, part2 = os.path.dirname(file_path).split(fileparts['dataset_name'])
        part1 = part1.strip('_').split('_')
    except Exception as exc:
        print(exc)
        pass

    return fileparts


def get_file_list(output_dir: str) -> list:
    # dirs=[p for p in Path(root_path).glob("*/*/") if p.is_dir()]

    cmd = ['find', output_dir, '-mindepth', '2', '-maxdepth', '5', '-type', "d"]
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
    # watch progress
    filelist = dask.compute(*filelist)

    filelist = list(itertools.chain(*filelist))
    return filelist


def parse_filename(file_path: str) -> dict:
    file = Path(file_path)  # uncomment when ready to run

    try:
        # isolate file from rest of path
        stem = file.stem
        # split the file name into components based on _
        split = stem.split('.')
        realm = ""
        time_range = ""
        variable_id = file.parts[1]
        source_type = ""
        member_id = ""
        experiment_id = file.parts[0]
        source_id = ""
        frequency = file.parts[2]
        chunk_freq = ""
        variant_label = ""
        grid_label = ""
        table_id = ""
        assoc_files = ""
    except Exception as exc:
        print(exc)
        pass
