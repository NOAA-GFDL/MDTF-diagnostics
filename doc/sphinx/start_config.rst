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
  `CESM2 <https://www.cesm.ucar.edu/models/cesm2/>`__.

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
<https://github.com/aradhakrishnanGFDL/CatalogBuilder>`__ that uses the directory structure to generate data catalogs.
It is optimized for the files stored on GFDL systems, but can be configured to generate catalogs on a local file system.

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

    * **model**: (string) name of the model for each case

    * **Convention**: (string) convention of case; ["CMIP" | "CESM" | "GFDL"]

    * **startdate**: (string with format <*YYYYMMDD*> or <*YYYYMMDDHHmmss>) The starting date of the analysis period

    * **enddate** (string with format <*YYYYMMDD*> or <*YYYYMMDDHHmmss>) The end date of the analysis period.

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

* **translate_data**: (boolean) Set to *true* to perform data translation; default *true*

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

The output of the package will be saved as a series of web pages in a directory named MDTF_output/[pod_name] in
<*OUTPUT_DIR*>.

If you run the package multiple times with the same configuration values and **overwrite** set to *false, the suffixes
".v1", ".v2", etc. will be added to duplicate `MDTF_output` directory names.
