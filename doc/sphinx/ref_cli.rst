.. role:: console(code)
   :language: console
   :class: highlight

Command-line options
====================

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

-f Path to a user configuration file that sets options listed here. This can be a JSON file of the form given in
 `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__
 (which is intended to be copied and used as a template)

Path settings
+++++++++++++

Locations of input and output data. All the paths in this section must be on a locally mounted filesystem. Environment variables in paths (e.g., ``$HOME``) are resolved at runtime according to the shell context the package is called from. Relative paths are resolved relative to the code directory.

--OBS-DATA-ROOT <OBS_DATA_ROOT>   Required setting if running PODs that require observational data. Directory containing
  observational and supporting data required by individual PODs. Currently, this must be downloaded manually as part
  of the framework installation. See :numref:`ref-download` of the :doc:`installation guide<start_install>` for instructions.
--WORK-DIR <WORKING_DIR>     Working directory. This will be used as scratch storage by the framework and the PODs.
  Optional; defaults to <*OUTPUT_DIR*> if not specified.
-o, --OUTPUT-DIR <OUTPUT_DIR>    Required setting. Destination for output files.

Data options
++++++++++++

Options that describe the input model data and how it should be obtained.

--convention <naming_convention>   | The convention for variable names and units used in the input model data. Defaults
  to ``CMIP``, for data produced as part of CMIP6 data request, or compatible with it.
   |
   | See the :doc:`ref_conventions` for documentation on the recognized values for this option.

--large_file   | Set this flag when running the package on a large volume of input model data: specifically, if the full
  time series for any requested variable is over 4gb. This may impact performance for variables less than 4gb but
  otherwise has no effect.
   |
   | When set, this causes the framework and PODs to use the netCDF-4 format (CDF-5 standard, using the HDF5 API;
   | see the `netCDF FAQ <https://www.unidata.ucar.edu/software/netcdf/docs/faq.html#How-many-netCDF-formats-are-there-and-what-are-the-differences-among-them>`__) for all intermediate data files generated during the package run. If the flag is not set (default), the netCDF4 Classic format is used instead. Regardless of this setting, the package can read input model data in any netCDF4 format.

--disable-preprocessor    If set, this flag disables preprocessing of input model data done by the framework before the PODs are run. Specifically, this skips validation of ``standard_name`` and ``units`` CF attributes in file metadata, and skips unit conversion and level extraction functions. This is only provided as a workaround for input data which is known to have incorrect metadata: using this flag means that the user assumes responsibility for verifying that the input data has the units requested by all PODs being run.
Conda/micromamba settings
+++++++++++++++++++++++++
--conda_root     path to anaconda, miniconda, or micromamba installation
--conda_env_root     path to directory with conda enviroments
--micromamba_exe     path to the micromamba executable. REQUIRED if using micromamba

Analysis settings
+++++++++++++++++

Settings determining what analyses the package performs.

CASENAME <name>    Required setting. Identifier used to label this run of the package. Can be set to any string.
startdate <yyyymmdd> or <yyyymmddHHmmss>   Required setting. Starting year of analysis period.
enddate <yyyymmdd>  or <yyyymmddHHmmss>   Required setting. Ending year of analysis period. The analysis period is taken
to be a **closed interval**
pod_list <list of POD identifiers>    Specification for which diagnostics (PODs) the package should run on the model
data, given as a list separated by spaces. Optional; default behavior is to attempt to run all PODs.

  Valid identifiers for PODs are:

  - The name of the diagnostic as given in the
    `diagnostics/ <https://github.com/NOAA/MDTF-diagnostics/tree/main/diagnostics>`__ directory.

Runtime options
+++++++++++++++

Options that control how the package is deployed (how code dependencies are managed) and how the diagnostics are run.

Output options
++++++++++++++

Options determining what files are output by the package.

save-ps    Set flag to have PODs save postscript figures in addition to bitmaps.
save-nc    Set flag to have PODs save netCDF files of processed data.
save-non-nc    Set flag to have PODs save all intermediate data **except** netCDF files.
make-variab-tar    Set flag to save package output in a single .tar file. This will only contain HTML and bitmap plots,
regardless of whether the flags above are used.
overwrite    If this flag is set, new runs of the package will overwrite any pre-existing results in <*OUTPUT_DIR*>.
