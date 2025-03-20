.. role:: console(code)
   :language: console
   :class: highlight
.. _ref-cli:
Runtime configuration options
=============================

Running the package
-------------------

If you followed the :ref:`recommended installation method<ref-conda-install>` for installing the framework
the `conda <https://docs.conda.io/en/latest/>`__ package manager, the installation process will have created
a driver script named ``mdtf`` in the top level of the code directory.
This script should always be used as the entry point for running the package.

This script is minimal and shouldn't conflict with customized shell environments:
it only sets the conda environment for the framework and calls
`mdtf_framework.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/mdtf_framework.py>`__,
the python script which should be used as the entry point if a different installation method was used. In all cases
the command-line options are as described here.

Usage
-----

::


The first form of the command runs the package's diagnostics on model data files in the directory ``CASE_ROOT_DIR``.
The options, described below, can be set on the command line or in an input file specified with the
``-f```` flag. An example of such an input file is provided at
`src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__.

The second form of the command prints information about the installed diagnostics.
To get a list of topics recognized by the command, run :console:`% mdtf info`.


.. _ref-cli-options:
General options
+++++++++++++++

-h, --help     Show a help message, potentially more up-to-date than this page, along with your site's default values
for these options.

-f    Path to a user configuration file that sets options listed here. This can be a JSON file of the form given in
 `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__
 (which is intended to be copied and used as a template)

Runtime configuration file settings
-----------------------------------

Path settings
+++++++++++++

Locations of input and output data. All the paths in this section must be on a locally mounted filesystem. Environment variables in paths (e.g., ``$HOME``) are resolved at runtime according to the shell context the package is called from. Relative paths are resolved relative to the code directory.

-OBS_DATA_ROOT     <str> Required setting if running PODs that require observational data. Directory containing
  observational and supporting data required by individual PODs. Currently, this must be downloaded manually as part
  of the framework installation. See :numref:`ref-download` of the :doc:`installation guide<start_install>` for
  instructions.

-WORK_DIR     <str> Optional. Working directory. This will be used as scratch storage by the framework and the PODs.
 defaults to <*OUTPUT_DIR*> if not specified.

-OUTPUT-DIR    <str> Required setting. Destination for output files.

Data options
++++++++++++

Options that describe the input model data and how it should be obtained. The settings are defined
in the example configuration files in the `templates/ <https://github.com/NOAA/MDTF-diagnostics/tree/main/templates>`__
directory.

-convention    <str; CMIP | GFDL | CESM> The convention for variable names and units used in the input model data.

-large_file    <bool> Set this flag when running the package on a large volume of input model data: specifically, if the
 full time series for any requested variable is over 4gb. This may impact performance for variables less than 4gb but
 otherwise has no effect.
 When set, this causes the framework and PODs to use the netCDF-4 format (CDF-5 standard, using the HDF5 API;
 see the `netCDF FAQ <https://www.unidata.ucar.edu/software/netcdf/docs/faq.html#How-many-netCDF-formats-are-there-and-what-are-the-differences-among-them>`__)
 for all intermediate data files generated during the package run. If the flag is not set (default), the netCDF4
 Classic format is used instead. Regardless of this setting, the package can read input model data in any
 netCDF4 format.

Conda/micromamba settings
+++++++++++++++++++++++++

-conda_root     <str> path to anaconda, miniconda, or micromamba installation

-conda_env_root     <str> path to directory with conda enviroments

-micromamba_exe     <str> path to the micromamba executable. REQUIRED if using micromamba

Analysis settings
+++++++++++++++++

Settings determining what analyses the package performs.

-pod_list    <list of POD identifiers>  Specification for which diagnostics (PODs) the package should run on the model
 data, given as a list separated by spaces.
 Valid identifiers for PODs are the name(s) of the diagnostic(s) as given in the
 `diagnostics/ <https://github.com/NOAA/MDTF-diagnostics/tree/main/diagnostics>`__ directory.

-startdate    <yyyymmdd> or <yyyymmddHHmmss> Required setting. Starting year of analysis period.

-enddate     <yyyymmdd> or <yyyymmddHHmmss> Required setting. Ending year of analysis period. The analysis period is taken
 to be a **closed interval**

-model     <str> Optional. Name of model, mainly for user reference.

-realm     <str | list of strings> Optional. Dataset realm. May be used to refine query search.
 If not defined, the query uses the POD realm.

-frequency    <str | list of strings> Optional. Dataset frequency. May be used to refine query search.
 If not defined, the query uses the POD frequency.

Runtime options
+++++++++++++++

Options that control how the package is deployed (how code dependencies are managed) and how the diagnostics are run.

-user_pp_scripts    <list of strings> Optional. List with custom preprocessing script(s) to run on data
 Place these scripts in the user_scripts directory of your copy of the MDTF-diagnostics repository. Note that
 the framework will automatically run any scripts defined in the list.

Output options
++++++++++++++

Options determining what files are output by the package.

-run_pp     <bool> Set to true to run the preprocessor; default true.

-translate_data    <bool> Set to true to perform data translation; default true.

-save_ps    <bool> Set to true have PODs save postscript figures in addition to bitmaps; Default false.

-save_pp_data    <bool> Set to true have PODs save netCDF files of processed data; default true

-make_variab_tar    <bool> Set to true save package output in a single .tar file. This will only contain HTML
 and bitmap plots regardless of whether the flags above are used. Default false.

-overwrite   <bool>  Set to true to have new runs of the package overwrite any pre-existing results in <*OUTPUT_DIR*>.
 default false

-make_multicase_figure    <bool> Generate html output for multiple figures per case. Default false.
