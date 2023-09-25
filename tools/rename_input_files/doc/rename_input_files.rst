.. _ref-rename-input-files:

rename_input_files.py
=====================

USAGE
-----
Rename input files that do not adhere to the default Local_file data_manager
convention of `<CASENAME>.<frequency>.<variable name>.nc`
and write to the directory `[outputDir]/[CASENAME]/[frequency]`

To use, run the following command:

`> ./rename_input_files.py --config_file [configuration file name].py`

Input
-----
Configuration yaml file with the directory containing the input data,
the directory where the output will be written, the CASENAME to use for the output file names,
the file names for the copied data,
and the frequencies and variable names to use in the new file names

The file `config_template.yml` shows how to define the *casename* and *frequency*
parameters, the paths to the original input data and the output directory where the
modified file names will be copied, the names of the files to change, and the corresponding
variable names that will be substituted in the modfied file names.

Output
------
Copies of the desired files to the directory `[outputDir]/[CASENAME]/[freq]`
with the format `<CASENAME>.<freq>.<variable name>.nc`

Required packages:
------------------
The required packages are included in the _MDTF_base conda
environment:
- os
- sys
- pyyaml
- click
- pathlib
- shutil