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
import shutil
import sys
import yaml
from pathlib import Path
import dask
import intake
import ecgtools
import click


@click.command()
@click.option('--root_path', type=str, help='Path to the root directory with the desired files')
@click.option('--convention', type=str, default='cmip', help='DRS convention')
def main(root_path: str, convention: str):
    """A developer tool to rename netCDF input files to match the MDTF-diagnostics Local_file format"""
    assert (os.path.isdir(root_path)), f"{root_path} not found. Check Path for typos."
