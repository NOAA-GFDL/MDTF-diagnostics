.. role:: console(code)
   :language: console
   :class: highlight

Running the package on your data
================================

In this section we describe how to proceed beyond running the simple test case described in the
:doc:`previous section <start_install>`, in particular how to run the framework on your own model data.

Preparing your data for use by the package
------------------------------------------

You have multiple options for organizing or setting up access to your model's data in a way that the framework
can recognize. This task is performed by a "data source," a code plug-in that handles obtaining model data from
a remote location for analysis by the PODs.

In order to identify what variable names correspond to the physical quantities requested by each POD, the LocalFile
data source requires that model data follow one of several recognized variable naming conventions defined by
the package. The currently recognized conventions are:

* ``CMIP``: Variable names and units as used in the
  `CMIP6 <https://www.wcrp-climate.org/wgcm-cmip/wgcm-cmip6>`__ `data request <https://doi.org/10.5194/gmd-2019-219>`__.
  There is a `web interface <http://clipc-services.ceda.ac.uk/dreq/index.html>`__ to the request.
  Data from any model that has been published as part of CMIP6
  (e.g., made available via `ESGF <https://esgf-node.llnl.gov/projects/cmip6/>`__) should follow this convention.

* ``CESM``: Variable names and units used in the default output of models developed at the
  `National Center for Atmospheric Research <https://ncar.ucar.edu>`__, such as
  `CAM <https://www.cesm.ucar.edu/models/cesm2/atmosphere/>`__ (all versions) and
  `CESM <https://www.cesm.ucar.edu/models/cesm2/>`__.

* ``GFDL``: Variable names and units used in the default output of models developed at the
  `Geophysical Fluid Dynamics Laboratory <https://www.gfdl.noaa.gov/>`__, such as
  `AM4 <https://www.gfdl.noaa.gov/am4/>`__, `CM4 <https://www.gfdl.noaa.gov/coupled-physical-model-cm4/>`__ and
  `SPEAR <https://www.gfdl.noaa.gov/spear/>`__.

The names and units for the variables in the model data you're adding need to conform to one of the above conventions
in order to be recognized by the LocalFile data source. For models that aren't currently supported, the workaround we
recommend is to generate ``CMIP``-compliant data by postprocessing model output with the
`CMOR <https://cmor.llnl.gov/>`__ tool.
We hope to offer support for the naming conventions of a wider range of models in the future.

Generating an ESM-intake catalog of your model dataset
++++++++++++++++++++++++++++++++++++++++++++++++++++++

The MDTF-diagnostics uses `intake-ESM <https://intake-esm.readthedocs.io/en/stable/>`__ catalogs and APIs to access
model datasets and verify POD data requirements. The MDTF-diagnostics package provides a basic
`catalog_builder script <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/tools/catalog_builder>`__
that uses `ecgtools <https://ecgtools.readthedocs.io/en/latest/>`__ APIs to generate data catalogs.

The NOAA-GFDL workflow team also maintains an `intake-ESM catalog builder
<https://noaa-gfdl.github.io/CatalogBuilder>`__ that uses the directory structure to generate data catalogs.
It is optimized for the files stored on GFDL systems, but can be configured to generate catalogs on a local file system.
The GFDL catalog builder has canned cases to embrace interoperability with the MDTF’s preprocessor rewrite and support
for ongoing GFDL model development. The package has been tested on GFDL AM5 simulations and CMIP directory structures
at this time. Please open a `GitHub issue <https://github.com/NOAA-GFDL/CatalogBuilder/issues>`__ or start
a `discussion<https://github.com/NOAA-GFDL/CatalogBuilder/discussions>`__ if you need assistance with the GFDL builder.

We encourage MDTF-diagnostics users to try running both catalog builders. Feel free to extend either tool to suit your needs, and consider submitting your additions to the appropriate
repository(ies).

See :doc:`the catalog documentation <ref-catalogs>` for more information on the implementation of
ESM-intake catalogs in the framework and the required column information for preprocessor functionality.

Adding your observational data files
++++++++++++++++++++++++++++++++++++

If you have observational data you want to analyze available on a locally mounted disk, we recommend creating
`symlinks <https://en.wikipedia.org/wiki/Symbolic_link>`__ that have the needed filenames, rather than making copies
of the data files. For example,

.. code-block:: console

    % mkdir -p inputdata/obs_data/[pod name]
    % ln -s <path> inputdata/obs_data/[pod name]/[file name]

will create a symbolic link to the file at <*path*> that follows the filename convention used by this data source:

::

   inputdata
   ├── obs_data ( = <OBS_DATA_ROOT>)
   │   ├── example
   │       ├── example file


Running the package on your data
--------------------------------

How to configure the package
++++++++++++++++++++++++++++

All configuration options for the package options are set in a JSON or Yaml
configuration file passed to the package with the ``-f`` flag. An example of this input file is given in
`templates/runtime_config.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__,
which you used :ref:`previously<ref-execute>` to run the package on test data. We recommend using one of the files as a
template, copying it, and customizing it as needed.

Options controlling the analysis
++++++++++++++++++++++++++++++++

The configuration options required to specify what analysis the package should do are:

* **pod_list**: (list of strings) comma-separated list of PODs to run with the framework

* **case_list**: Main block with the information for each model data case to run with the framework
  The block for each case is a string with the name of each model simulation (case). Note that there is no
  explicit *CASENAME* paramater in the configuration file; the framework will define each *CASENAME* key using string
  value that defines the case block.

    * **convention**: (string, required): convention of case; ["CMIP" | "CESM" | "GFDL"]

    * **startdate**: (string with format <YYYY>, <YYYYmm> <*YYYYmmdd*> or <*YYYYmmddHHMMSS>, required):
      The starting date of the analysis period

    * **enddate** (string with format <YYYY>, <YYYYmm> <*YYYYmmdd*> or <*YYYYmmddHHMMSS, required): The end date of the
      analysis period.

    * **realm** (string, optional): realm of the dataset. If defined, the preprocessor will query the catalog with the
      dataset realm instead of the POD realm.

    * **model**: (string, optional) name of the model for each case

An error will be raised if the data provided for any requested variable doesn't span the date range defined by
**startdate** and **enddate**

Options for data management
+++++++++++++++++++++++++++

* **DATA_CATALOG**: (string; *required*) Full or relative path to the model data ESM-intake catalog .json header file

* **OBS_DATA_ROOT**: (string; optional) Full or relative path to Parent directory containing observational data. Must
  be set if running PODs that have required observational datasets.

* **WORK_DIR**: (string; required) Full or relative path to working directory

* **OUTPUT_DIR**: (string; optional) Full or relative path to output directory; The results of each run of the framework
  will be put in an `MDTF_output` subdirectory of this directory. Defaults to **WORK_DIR** if blank.

* **conda_root**: (string; required) Location of the Anaconda/miniconda or micromamba installation to use for managing
  package dependencies (path returned by running `conda info --base` or `micromamba info`.)

* **conda_env_root**: (string; required) Directory containing the framework-specific conda environments. This should
  be equal to the "--env_dir" flag passed to `conda_env_setup.sh`

* **micromambe_exe** (string; required if using micromamba to manage conda environments)
  Full path to the micromamba executable

Options for workflow control
++++++++++++++++++++++++++++

* **run_pp**: (boolean) Set to *true* to run the preprocessor; default *true*

* **translate_data**: (boolean) Set to *true* to perform data translation. If *false*, the preprocessor query
  automatically uses the convention for each case in the input dataset for the query, and skips translating the
  variable names and attributes to the POD convention. Note that this means that the precipRateToFluxConversion is not
  applied. This option is best if you know that the input dataset has variable attributes that exactly match the
  the POD variable attributes; default *true*

* **save_ps**: (boolean) Set to *true* to have PODs save postscript figures in addition to bitmaps; default *false*

* **large_file**: (boolean) Set to *true* for files > 4 GB. The framework will write processed
  netCDF files in `NETCDF4_CLASSIC` format; if *false* files are written in `NETCDF4` format; default *false*

* **save_pp_data**: (boolean) set to *true* to retain processed data in the `OUTPUT_DIR` after preprocessing.
  If *false*, delete processed data after POD output is finalized; default *true*

* **make_variab_tar**: (boolean) Set to *true* to save HTML and bitmap plots in a .tar file; default *false*

* **make_multicase_figure_html**: (boolean) Set to *true* to auto-generate html output for multiple figures per case;
  default *false*

* **overwrite**: (boolean) Set to *true* to overwrite newest existing `OUTPUT_DIR` from a previous run; default *false*

* **user_pp_scripts**: (list of strings) comma-separated Python list of strings with custom preprocessing scripts to
  include in the workflow. Add any custom script(s) you want to run to the
  `user_scripts <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/user_scripts>`__ directory of your copy of
  the MDTF-diagnostics repository. The scripts will run even if the list is populated whether **run_pp** is set to
  *true* or *false*.

Running the MDTF-diagnostics package with multiple cases
========================================================

Version 3 and later of the MDTF-diagnostics package provides support for "multirun" diagnostics that analyze output from
multiple model datasets (with or without observational data). "Single-run" PODs that analyze one model dataset
and/or one observational dataset and multirun PODs cannot be run together because the framework is
configured to run each case on each POD.

The example_multicase POD and configuration
--------------------------------------------
A multirun test POD called *example_multicase* is available in ``diagnostics/example_multicase`` that demonstrates
how to configure "multirun" diagnostics that analyze output from multiple datasets.
The `multirun_config_template.jsonc file
<https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example_multicase/multirun_config_template.jsonc>`__
contains separate ``pod_list`` and ``case_list`` blocks. As with the single-run configuration, the ``pod_list`` may
contain multiple PODs separated by commas. The `case_list` contains multiple blocks of information for each case that
the POD(s) in the ``pod_list`` will analyze. The ``CASENAME``, ``convention``, ``startdate``, and ``enddate`` attributes
must be defined for each case. The ``convention`` must be the same for each case, but ``startdate`` and ``enddate``
may differ among cases. ``realm`` and ``model`` are optional case attributes that the user can include to refine the catalog
query (e.g., search for data with realm = 'atmos-cmip' instead of 'atmos'.

Directions for generating the synthetic data in the configuration file are provided in the file comments, and in the
quickstart section of the `README file
<https://github.com/NOAA-GFDL/MDTF-diagnostics#5-run-the-framework-in-multi_run-mode-under-development>`__

POD output
----------
The framework defines a root directory ``_MDTF_output[_v#]/[POD name]`` for each
POD in the pod_list. ``_MDTF_output[_v#]/[POD name]`` contains the the main framework log files, and subdirectories for each
case. Processed data files for each case are placed in ``_MDTF_output[_v#]/[CASENAME]/[data output frequency]``.
The pod html file is written to ``$OUTPUT_DIR/[POD name]/[POD_name].html`` (`$OUTPUT_DIR` defaults to ``$WORK_DIR``
if it is not defined), and the output figures are placed in ``$OUTPUT_DIR/[POD name]/model`` depending on how the paths
are defined in the POD's html template.

.. note::

  The framework creates an ``obs/`` subirectory in each ``$WORK_DIR``by default, but will be empty unless a
  POD uses observational dataset and writes observational data figures to this directory.
  Figures that are generated as .eps files before conversion to .png files are written to
  ``_MDTF_OUTPUT[_v#]/[POD name]/model/PS``.

Multirun environment variables
------------------------------
Multirun PODs obtain information for environment variables for the case and variable attributes
described in the :doc:`configuration section <./start_config>`
from a yaml file named *case_info.yaml* that the framework generates at runtime. The ``case_info.yaml`` file is written
to ``_MDTF_OUTPUT[_v#]/[POD name]``, and has a corresponding environment variable ``case_env_file`` that the POD uses to
parse the file. The ``example_multicase.py`` script demonstrates to how to read the environment variables from
``case_info.yaml`` using the ``case_env_file`` environment variable into a dictionary,
then loop through the dictionary to obtain the post-processed data for analysis. An example ``case_info.yaml`` file
with environment variables defined for the synthetic test data is located in the ``example_multicase`` directory.

Running the package
+++++++++++++++++++

From this point, the instructions for running the package are the same as for
:ref:`running it on the sample data<ref-execute>`, assuming you've set the configuration options by editing a copy of
the configuration file template at `templates/runtime_config.jsonc
 <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__. The package is run in the
same way:

.. code-block:: console

    % cd <CODE_ROOT>
    % ./mdtf -f <new config file path>

The output of the package will be saved as a series of web pages in a directory named ``MDTF_output/[pod_name]`` in
``<OUTPUT_DIR>``.

If you run the package multiple times with the same configuration values and **overwrite** set to *false, the suffixes
".v1", ".v2", etc. will be added to duplicate ``MDTF_output`` directory names.
