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
from pathlib import Path

@click.command()
@click.option('--config_file', type=str, help='Path to the MDTF-diagnostics runtime config file')
def main(config_file: str):
    """A developer tool to rename netCDF input files to match the MDTF-diagnostics Local_file format"""
    assert (os.path.isfile(config_file)), "File not Found. Check Path to config file for typos."
    with open(config_file, 'r') as stream:
        try:
            case_info = yaml.safe_load(stream)
            print(case_info)
        except yaml.YAMLError as exc:
            print(exc)

    casename = case_info['CASENAME']
    in_path = case_info['origFilePath']
    out_path = case_info['outputFilePath']
    append_new_filenames(case_info['files'], casename)
    link_files(in_path, out_path, case_info['files'])


def append_new_filenames(file_list=list, casename=str):
    for f in file_list:
        print(f)
        f['new_name'] = '.'.join([casename, f['var'], f['freq'], 'nc'])

def link_files(input_dir_path=str, output_dir_path=str, file_list=list):
    for f in file_list:
        f['inpath'] = os.path.join(input_dir_path,f['name'])
        assert os.path.isfile(f['inpath']), f['inpath']+" not found. Check file name and path for errors."
        f['outpath'] = os.path.join(output_dir_path)
        Path(f['outpath']).mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    main(prog_name='Rename Input Files')
