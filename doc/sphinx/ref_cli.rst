.. role:: console(code)
   :language: console
   :class: highlight

Command-line options
====================

Running the package
-------------------

If you followed the :ref:`recommended installation method<ref-conda-install>` for installing the framework with the `conda <https://docs.conda.io/en/latest/>`__ package manager, the installation process will have created a driver script named ``mdtf`` in the top level of the code directory. This script should always be used as the entry point for running the package. 

This script is minimal and shouldn't conflict with customized shell environments: it only sets the conda environment for the framework and calls `mdtf_framework.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/mdtf_framework.py>`__, the python script which should be used as the entry point if a different installation method was used. In all cases the command-line options are as described here.

Usage
-----

::

    mdtf [options] [CASE_ROOT_DIR]
    mdtf info [TOPIC]

The first form of the command runs the package's diagnostics on model data files in the directory ``CASE_ROOT_DIR``. The options, described below, can be set on the command line or in an input file specified with the ``-f``/``--input-file`` flag. An example of such an input file is provided at `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__.

The second form of the command prints information about the installed diagnostics. To get a list of topics recognized by the command, run :console:`% mdtf info`.


.. _ref-cli-options:

Command-line options
--------------------

For long command line flags, words may be separated with hyphens (GNU standard) or with underscores (python variable name convention). For example, ``--file-transfer-timeout`` and ``--file_transfer_timeout`` are both recognized by the package as synonyms for the same setting.

If you're using site-specific functionality (via the ``--site`` flag, described below), additional options may be available beyond what is listed here: see the :doc:`site-specific documentation<site_toc>` for your site. In addition, your choice of site may set default values for these options; the default values and the location of the configuration file defining them are listed as part of running :console:`% mdtf --site <your site> --help`. 

General options
+++++++++++++++

-h, --help     Show a help message, potentially more up-to-date than this page, along with your site's default values for these options.
--version      Show the program's version number and exit.
-s, --site <site_name>   | Setting to use site-specific customizations and functionality. <*site_name*> is the name of one of the directories in `sites/ <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/sites>`__, which contain additional code and configuration files to use. 
   |
   | The default value for this setting is ``local``. The sites/local/ directory is left empty in order to enable any installation to be customized (e.g. settings the paths to where supporting data was installed) without needing to alter the framework code. For more information on how to do this, see the documentation for the `'local' site <../sphinx_sites/local.html>`__.
   |
   | In general, see the :doc:`site-specific documentation<site_toc>` for information on what functionality is added for a given site.

-f, --input-file <input_file>    Path to a user configuration file that sets options listed here. This can be a JSON file of the form given in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__ (which is intended to be copied and used as a template), or a text file containing flags and command-line arguments as they would be entered in the shell. Additional options set explicitly on the command line will still override settings in this file.

Paths
+++++

Locations of input and output data. All the paths in this section must be on a locally mounted filesystem. Environment variables in paths (e.g., ``$HOME``) are resolved at runtime according to the shell context the package is called from. Relative paths are resolved relative to the code directory.

--CASE-ROOT-DIR <CASE_ROOT_DIR>    Alternate method to specify the root directory of input model data, with a flag instead of a positional argument.
--MODEL-DATA-ROOT <MODEL_DATA_ROOT>    Directory to store input data from different models. Depending on the choice of <*data_manager*> (see below), input model data will typically be copied from a remote filesystem to this location.
--OBS-DATA-ROOT <OBS_DATA_ROOT>     Directory containing observational and supporting data required by individual PODs. Currently, this must be downloaded manually as part of the framework installation. See :numref:`ref-download` of the :doc:`installation guide<start_install>` for instructions.
--WORKING-DIR <WORKING_DIR>     Working directory. This will be used as scratch storage by the framework and the PODs.
-o, --OUTPUT-DIR <OUTPUT_DIR>    Destination for output files.

Data
++++

Settings that describe the input model data and how it should be obtained.

-c, --convention <naming_convention>   | The convention for variable names and units used in the input model data. Defaults to ``CMIP``, for data produced as part of CMIP6 data request, or compatible with it.
   |
   | See the :doc:`ref_conventions` for documentation on the recognized values for this option.

--strict    Disables any model data selection heuristics provided by <*data_manager*>. The details of what this does depend on the <*data_manager*>, but in general this means that model data will only be searched for based on a literal interpretation of the user's input, with an error raised if that input doesn't specify a unique model run/experiment.
--disable-preprocessor    If set, this flag disables preprocessing of input model data done by the framework before the PODs are run. Specifically, this skips validation of ``standard_name`` and ``units`` CF attributes in file metadata, and skips unit conversion and level extraction functions. This is only provided as a workaround for input data which is known to have incorrect metadata: using this flag means that the user assumes responsibility for verifying that the input data has the units requested by all PODs being run.
--overwrite-file-metadata     If set, this flag overwrites metadata in input model data files with the metadata in the framework's record. The framework's metadata record can either be set through the choice of a naming convention (the ``--convention`` flag above), or explicitly per variable in the configuration file used by the :ref:`ref-data-source-explictfile` option for ``--data-manager`` (see below). The default behavior is to either raise an error or update the framework's record in the event of a conflict with the file's metadata, since the latter is assumed to be an accurate description of the file's contents. Like the previous flag, this is setting is intended as a workaround for input data which is known to have incorrect metadata.
--data-manager <data_manager>   | Method used to search for and fetch input model data. <*data_manager*> is case-insensitive, and spaces and underscores are ignored.
   |
   | See the :doc:`ref_data_sources` for documentation on the available options, and the settings that are specific to each.
--large_file   | Set this flag when running the package on a large volume of input model data: specifically, if the full time series for any requested variable is over 4gb. This may impact performance for variables less than 4gb but otherwise has no effect.
   |
   | When set, this causes the framework and PODs to use the netCDF-4 format (CDF-5 standard, using the HDF5 API; see the `netCDF FAQ <https://www.unidata.ucar.edu/software/netcdf/docs/faq.html#How-many-netCDF-formats-are-there-and-what-are-the-differences-among-them>`__) for all intermediate data files generated during the package run. If the flag is not set (default), the netCDF4 Classic format is used instead. Regardless of this setting, the package can read input model data in any netCDF4 format.


Analysis
++++++++

Settings determining what analyses the package performs.

-n, --CASENAME <name>    Identifier used to label this run of the package. Can be set to any string.
-Y, --FIRSTYR <YYYY>    Starting year of analysis period.
-Z, --LASTYR <YYYY>     Ending year of analysis period. The analysis period is taken to be a **closed interval**, including all model data that falls between the start of 1 Jan on <*FIRSTYR*> and the end of 31 Dec on <*LASTYR*>.
-p, --pods <list of POD identifiers>    Specification for which diagnostics (PODs) the package should run on the model data, given as a list separated by spaces. If given as the last command-line option, you will need to add ``--`` to distinguish the last entry from <*CASE_ROOT_DIR*> (standard shell syntax). 

  Valid identifiers for PODs are:

  - The name of the diagnostic as given in the `diagnostics/ <https://github.com/tsjackson-noaa/MDTF-diagnostics/tree/main/diagnostics>`__ directory. Run :console:`% mdtf info pods` for a list of installed diagnostics.
  - The name of a modeling realm, in which case all PODs analyzing data from that realm will be selected. Run :console:`% mdtf info realms` for a list of installed diagnostics sorted by realm.
  - ``all``, the default setting, which selects all installed diagnostics.

  Giving multiple identifiers selects the union of all PODs described by each identifier.

Runtime settings
++++++++++++++++

Settings that control how the package is deployed (how code dependencies are managed) and how the diagnostics are run.

--environment-manager <environment_manager>   | Method the package should use to manage third-party code dependencies of diagnostics. <*environment_manager*> is case-insensitive, and spaces and underscores are ignored.
   |
   | See the :doc:`ref_runtime_mgrs` for documentation on the available options, and the settings that are specific to each.

   .. note::
      The values used for this option and its settings must be compatible with how the package was set up during :doc:`installation<start_install>`. Missing code dependencies are not installed at runtime; instead any POD with missing dependencies raises an error and is not run.

Output settings
+++++++++++++++

Settings determining what files are output by the package.

--save-ps    Set flag to have PODs save postscript figures in addition to bitmaps.
--save-nc    Set flag to have PODs save netCDF files of processed data.
--save-non-nc    Set flag to have PODs save all intermediate data **except** netCDF files.
--make-variab-tar    Set flag to save package output in a single .tar file. This will only contain HTML and bitmap plots, regardless of whether the flags above are used.
--overwrite    If this flag is set, new runs of the package will overwrite any pre-existing results in <*OUTPUT_DIR*>. The default behavior is for subsequent runs of the package to be output as MDTF\_<*CASENAME*>\_<*FIRSTYR*>\_<*LASTYR*>, MDTF\_<*CASENAME*>\_<*FIRSTYR*>\_<*LASTYR*>.v1, MDTF\_<*CASENAME*>\_<*FIRSTYR*>\_<*LASTYR*>.v2, etc. Setting this flag disables the use of the ".v1", ".v2", ... suffixes.

Debugging settings
++++++++++++++++++

-v, --verbose    Increase log verbosity level. ``-v`` prints more detailed debug information. This setting only affects console output: all logged information is always recorded in the log file saved with the package output.
-q, --quiet    Decreases the console log verbosity level. ``-q`` prints only warnings and errors, ``-qq`` prints errors only, and ``-qqq`` prints no output. This setting only affects console output: all logged information is always recorded in the log file saved with the package output.
--file-transfer-timeout <seconds>    Time (in seconds) to wait before giving up on transferring a data file to the local filesystem. Set to zero to wait indefinitely.
--keep-temp    Set flag to retain local copies of fetched model data (in <*MODEL_DATA_ROOT*>) between runs of the framework. The default behavior deletes this data after the package runs successfully. Retaining a local copy of the data can be useful when the model data is hosted remotely and you need to run a diagnostic repeatedly for development purposes.
--test-mode    Flag for use in framework testing: model data is fetched but PODs are not run.
--dry-run    Flag for use in framework testing: no external commands are run and no remote data is copied. Implies ``--test-mode``.

POD-specific options
--------------------

We don't currently provide a mechanism to pass options directly to individual PODs via the command line. Individual PODs may provide user-configurable options in the settings file which only need to be changed in rare or specific cases. These options are listed in the ``"pod_env_vars"`` section of the ``settings.jsonc`` located in each POD’s source code directory under ``diagnostics/``. Consult the :doc:`documentation <pod_toc>` for the POD in question for details.

