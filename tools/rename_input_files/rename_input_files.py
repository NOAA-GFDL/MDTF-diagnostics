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
# and write to the directory [outputDir]/[CASENAME]/[frequency]
#
# Input:
# Configuration yaml file with the directory containing the input data,
# the directory where the output will be written, the CASENAME to use for the output file names,
# the file names that will be linked,
# and the frequencies and variable names to use in the new symlinked file names
# Output: symlinks to the desired files in the directory [outputDir]/[CASENAME]/[freq]
# with the format <CASENAME>.<freq>.<variable name>.nc


import os
import sys
import yaml
import click
from pathlib import Path


@click.command()
@click.option('--config_file', type=str, help='Path to the MDTF-diagnostics runtime config file')
def main(config_file: str):
    """A developer tool to rename netCDF input files to match the MDTF-diagnostics Local_file format"""
    assert (os.path.isfile(config_file)), f"{config_file} not found. Check Path to config file for typos."
    with open(config_file, 'r') as stream:
        try:
            case_info = yaml.safe_load(stream)
            print(case_info)
        except yaml.YAMLError as exc:
            print(exc)

    casename = case_info['CASENAME']
    in_path = case_info['inputPath']
    assert (os.path.isdir(in_path)), f"Input directory {in_path} not found."
    out_path = os.path.join(case_info['outputPath'], casename)
    append_new_filenames(case_info['files'], casename)
    link_files(in_path, out_path, case_info['files'])
    sys.exit(0)


# add new_name attribute to the original file name
# with the format <CASENAME>.<frequency>.<variable name>.nc
def append_new_filenames(file_list=list, casename=str):
    for f in file_list:
        print(f)
        f['new_name'] = '.'.join([casename, f['var'], f['freq'], 'nc'])


# symlink files in inputFilePath to LocalFile-formatted outputFilePath
def link_files(input_dir_path=str, output_dir_path=str, file_list=list):
    for f in file_list:
        f['inpath'] = os.path.join(input_dir_path, f['name'])
        assert os.path.isfile(f['inpath']), f['inpath'] + " not found. Check file name and path for errors."
        f['outpath'] = os.path.join(output_dir_path, f['freq'])
        Path(f['outpath']).mkdir(parents=True, exist_ok=True)
        # Create a symbolic link pointing inpath to outpath
        newfilepath = os.path.join(f['outpath'], f['new_name'])
        if not os.path.isfile(newfilepath):
            os.symlink(f['inpath'], newfilepath)
        assert os.path.isfile(newfilepath),  f'Unable to symlink {newfilepath}.' \
                                             f' Check to ensure that you have write permission to' + f['outpath']


if __name__ == '__main__':
    main(prog_name='Rename Input Files')
