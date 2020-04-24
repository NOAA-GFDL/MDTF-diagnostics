# Command-line option reference

## Usage
```
src/mdtf.py [options] CASE_ROOT_DIR
src/mdtf.py info [INFO_TOPIC]
```

[src/mdtf.py](../blob/master/src/mdtf.py) is the top-level driver script for the framework. The first form runs diagnostics on the model input data located at `CASE_ROOT_DIR`. The second form prints online help about the installed diagnostics.

## General options

* `-h, --help`: Show a help message, potentially more up-to-date than this page.
* `--version`: Show program's version number and exit.
* `--config-file, --config_file, -f <FILE>`: Use framework settings in a text file `<FILE>`. This can be a JSON file in the form of either 1) a list of `"option": "value"` pairs, or 2) an edited copy of the [src/defaults.json](../blob/master/src/defaults.json) file with defaults changed to desired values, or 3) a plain text file containing options as they would be entered on the command line. **Note** that any other options set via the command line will still override settings in this file.

## Paths

**Note** that all the paths below should be on a _local_ filesystem. Environment variables in paths (eg `$HOME`) are resolved according to the shell context mdtf.py was called from. Relative paths are resolved relative to the repo directory.

* `--MODEL-DATA-ROOT, --MODEL_DATA_ROOT <DIR>`: Directory to store input data from different models. Depending on the choice of `data_manager` (see below), input model data will typically be copied from a remote filesystem to this location.
* `--OBS-DATA-ROOT, --OBS_DATA_ROOT <DIR>`: Directory containing observational data used by individual PODs. Currently, this must be downloaded manually as part of the framework installation. See [TODO: REF] for instructions.
* `--WORKING-DIR, --WORKING_DIR <DIR>`: Working directory.
* `--OUTPUT-DIR, --OUTPUT_DIR <DIR>`: Destination for output files. Currently this must be on the same filesystem as `WORKING_DIR`.

## Model data

* `--CASE-ROOT-DIR, --CASE_ROOT_DIR <DIR>`: Alternate method to specify root directory of model data.
* `--FIRSTYR, -Y <year>`: Starting year of analysis period.
* `--LASTYR, -Z <year>`: Ending year of analysis period (inclusive).
* `--CASENAME <name>`: Identifier used to label the input model dataset.
* `--convention <convention>`: Variable name/unit convention used in model data. Defaults to CMIP6-style conventions.
* `--model <source_id>`: Model name (only used in retrieving data from a CMIP6 directory structure).
* `--experiment <experiment_id>`: Experiment ID (only used in retrieving data from a CMIP6 directory structure).

## Model data retrieval settings

* `--data-manager, --data_manager <DATA_MANAGER>` Method used to fetch model data. (default: GFDL_auto)
* `--file-transfer-timeout, --file_transfer_timeout <seconds>` Time (in seconds) to wait before giving up on transferring a data file to the local filesystem. Set to zero to wait indefinitely. (default: 300)
* `--keep-temp, --keep_temp`: Set flag to retain local copies of fetched model data (in MODEL_DATA_ROOT) between runs of the framework. Default is false. This can be useful when you need to run a diagnostic repeatedly for development purposes and the model data hosted remotely.

## Diagnostics

* `--pods, -p [...]`: List of diagnostics to run on model data, separated by spaces. This can be `all` (the default), one or more POD names, or one or more realms. Run `mdtf_gfdl.py info pods` for a list of recognized POD names.

## Runtime settings

* `--environment-manager, --environment_manager <ENVIRONMENT_MANAGER>`: Method to manage POD runtime dependencies. (default: GFDL_conda)
* `--conda-root, --conda_root <DIR>`: Path to the Anaconda installation. Only used if environment_manager = 'Conda'. Set equal to '' to use conda from your system's $PATH.
* `--conda-env-root, --conda_env_root <DIR>`: Root directory for Anaconda environment installs. Only used if environment_manager = 'Conda'. Set equal to '' to install in your system's default location.
* `--venv-root, --venv_root <DIR>`: Root directory for python virtual environments. Only used if environment_manager = 'Virtualenv'. Set equal to '' to install in your system's default location. (default: ./envs/venv)
* `--r-lib-root, --r_lib_root <DIR>`: Root directory for R packages requested by PODs. Only used if environment_manager = 'Virtualenv'. Set equal to '' to install in your system library. (default: ./envs/r_libs)

## Output settings

* `--save-ps, --save_ps`: Set flag to have PODs save postscript figures in addition to bitmaps. (default: False)
* `--save-nc, --save_nc`: Set flag to have PODs save netCDF files of processed data. (default: False)
* `--make-variab-tar, --make_variab_tar`: Set flag to save HTML and bitmap plots in a .tar file. (default: False)
* `--overwrite`: Set flag to overwrite results in OUTPUT_DIR. Default is false: Runs of the framework are saved as directories with the name `MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>`, so if a directory with that name is found in OUTPUT_DIR, the current results will be saved as `MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>.1`, `MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>.2`, etc.

## Debugging settings

* `--verbose, -v`: Increase log verbosity level.
* `--test-mode, --test_mode`: Set flag for framework test. Data is fetched but PODs are not run.
* `--dry-run, --dry_run`: Set flag for framework test. No external commands are run and no remote data is copied. Implies `test_mode`.








