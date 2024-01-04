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

mdtf_cv = dict()
mdtf_cv["frequency"] = {"subhrPt": "sub-hourly",
                        "6hr": "4x-daily",
                        "6hrPt": "4x-daily",
                        "hr": "hourly",
                        "day": "daily",
                        "mon": "monthly"}
mdtf_cv["startdate"] = ""
mdtf_cv["enddate"] = ""
mdtf_cv["cell_methods"] = []
def get_file_list(output_dir: str) -> list:  # , depth=0, extension='*.nc'):
    depth = 1
    from dask.diagnostics import ProgressBar

    # dirs=[p for p in Path(root_path).glob("*/*/") if p.is_dir()]

    cmd = ['find', output_dir, '-mindepth', '4', '-maxdepth', '4', '-type', "d"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    output = proc.stdout.read().decode('utf-8').split()
    dirs = [Path(entry) for entry in output]

    @dask.delayed
    def _file_dir_files(directory):
        try:
            cmd = ['find', '-L', directory.as_posix(), '-name', '*.nc', '-type', "f", "-perm", "-444"]
            proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            output = proc.stdout.read().decode('utf-8').split()
        except Exception as exc:
            print(exc)
            output = []
        return output

    print('Getting list of assets...\n')
    filelist = [_file_dir_files(directory) for directory in dirs]
    # watch progress
    with ProgressBar():
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
        realm = split[0]
        time_range = split[1]
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
