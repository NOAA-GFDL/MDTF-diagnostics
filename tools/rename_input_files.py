# ======================================================================
# NOAA Model Diagnostics Task Force (MDTF)
#
# Rename input files
#
# ======================================================================
# Usage
#
# USAGE: rename input files that do not adhere to the default Local_file
# convention of <CASENAME>.<frequency>.<variable name>.nc
# and write to the directory [root path]/[model]/[CASENAME]/[frequency]
#
# Input:
# Configuration file with the information provided in src/default_tests.jsonc
#


import os
import yaml
import click

@click.command()
@click.option('--config_file', type=str, help='Path to the MDTF-diagnostics runtime config file')
def cli_parser(config_file: str):
    """A developer tool to rename netCDF input files to match the MDTF-diagnostics Local_file format"""
    assert (os.path.isfile(config_file)), "File not Found. Check Path to config file for typos."
    with open(config_file, 'r') as stream:
        try:
            case_info = yaml.safe_load(stream)
            print(case_info)
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == '__main__':
    cli_parser(prog_name='Rename Input Files')