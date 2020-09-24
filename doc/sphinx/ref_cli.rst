Command-line option reference
=============================

Usage
-----

::

    mdtf [options] [INPUT_FILE] [CASE_ROOT_DIR]
    mdtf info [TOPIC]


If the framework was installed to use `Conda <https://docs.conda.io/en/latest/>`__ (recommended), the top-level ``mdtf`` driver script is created at install time. It sets the conda environment and calls `src/mdtf.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/mdtf.py>`__, the top-level script for non-conda installations.

The first form of the command runs diagnostics on data at ``CASE_ROOT_DIR``, using configuration set on the command line or in ``INPUT_FILE``. 

* ``INPUT_FILE``: Path to a user configuration file that sets options listed here. This can be a JSON file of the form given in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__ (which is intended to be copied and used as a template), or a text file containing command-line arguments. Options set explicitly on the command line will still override settings in this file.
* ``CASE_ROOT_DIR``: Root directory of model data to analyze.

The second form of the command prints information about available diagnostics; run without an argument ('mdtf info') to see a list of available topics.

General options
---------------

* ``-h, --help``: Show a help message, potentially more up-to-date than this page, along with your site's default values for these options.
* ``--version``: Show program's version number and exit.
* ``--input-file, --input_file, -f <INPUT_FILE>``: Alternate way to specify user configuration file (with a flag instead of a positional argument.) 

Paths
-----

Parent directories of input and output data. **Note** that all the paths below should be on a *local* filesystem. Environment variables in paths (eg ``$HOME``) are resolved according to the shell context ``mdtf`` was called from. Relative paths are resolved relative to the repo directory.

* ``--MODEL-DATA-ROOT, --MODEL_DATA_ROOT <DIR>``: Directory to store input data from different models. Depending on the choice of ``data_manager`` (see below), input model data will typically be copied from a remote filesystem to this location.
* ``--OBS-DATA-ROOT, --OBS_DATA_ROOT <DIR>``: Directory containing observational data used by individual PODs. Currently, this must be downloaded manually as part of the framework installation. See :numref:`ref-download` of the :doc:`installation guide <start_install>` for instructions.
* ``--WORKING-DIR, --WORKING_DIR <DIR>``: Working directory.
* ``--OUTPUT-DIR, --OUTPUT_DIR, -o <DIR>``: Destination for output files. Currently this must be on the same filesystem as ``WORKING_DIR``.

Model data
----------

* ``--CASE-ROOT-DIR, --CASE_ROOT_DIR <DIR>``: Alternate method to specify root directory of model data (with a flag instead of a positional argument.)
* ``--FIRSTYR, -Y <year>``: Starting year of analysis period.
* ``--LASTYR, -Z <year>``: Ending year of analysis period (inclusive).
* ``--CASENAME, -n <name>``: Identifier used to label the input model dataset.
* ``--convention, -c <convention>``: Variable name/unit convention used in model data. Defaults to CMIP6-style conventions.
* ``--model, -m <source_id>``: Model name (only used in retrieving data from a CMIP6 directory structure).
* ``--experiment, -e <experiment_id>``: Experiment ID (only used in retrieving data from a CMIP6 directory structure).

Model data retrieval settings
-----------------------------

* ``--data-manager, --data_manager <DATA_MANAGER>`` Method used to fetch model data.
* ``--file-transfer-timeout, --file_transfer_timeout <seconds>`` Time (in seconds) to wait before giving up on transferring a data file to the local filesystem. Set to zero to wait indefinitely.
* ``--keep-temp, --keep_temp``: Set flag to retain local copies of fetched model data (in ``MODEL_DATA_ROOT``) between runs of the framework. Default is false. This can be useful when you need to run a diagnostic repeatedly for development purposes and the model data hosted remotely.

Diagnostics
-----------

* ``--pods, -p [...]``: List of diagnostics to run on model data, separated by spaces. This can be ``all`` (the default), one or more `POD names <https://github.com/tsjackson-noaa/MDTF-diagnostics/tree/main/diagnostics>`__, or one or more modeling realms. Run ``mdtf info pods`` for a list of installed PODs.

Runtime settings
----------------

* ``--environment-manager, --environment_manager <ENVIRONMENT_MANAGER>``: Method to manage POD runtime dependencies.
* ``--conda-root, --conda_root <DIR>``: Path to the Anaconda installation. Only used if environment_manager = 'Conda'. Set equal to '' to use conda from your system's $PATH.
* ``--conda-env-root, --conda_env_root <DIR>``: Root directory for Anaconda environment installs. Only used if environment_manager = 'Conda'. Set equal to '' to install in your system's default location.
* ``--venv-root, --venv_root <DIR>``: Root directory for python virtual environments. Only used if environment_manager = 'Virtualenv'. Set equal to '' to install in your system's default location.
* ``--r-lib-root, --r_lib_root <DIR>``: Root directory for R packages requested by PODs. Only used if environment_manager = 'Virtualenv'. Set equal to '' to install in your system library.

Output settings
---------------

* ``--save-ps, --save_ps``: Set flag to have PODs save postscript figures in addition to bitmaps.
* ``--save-nc, --save_nc``: Set flag to have PODs save netCDF files of processed data.
* ``--save-non-nc, --save_non_nc``: Set flag to save all processed data except netcdf files.
* ``--make-variab-tar, --make_variab_tar``: Set flag to save HTML and bitmap plots in a .tar file.
* ``--overwrite``: Set flag to overwrite results in OUTPUT_DIR. Default is false: Runs of the framework are saved as directories with the name ``MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>``, so if a directory with that name is found in OUTPUT_DIR, the current results will be saved as ``MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>.1``, ``MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>.2``, etc.

Debugging settings
------------------

* ``--verbose, -v``: Increase log verbosity level.
* ``--test-mode, --test_mode``: Set flag for framework test. Data is fetched but PODs are not run.
* ``--dry-run, --dry_run``: Set flag for framework test. No external commands are run and no remote data is copied. Implies ``test_mode``.








