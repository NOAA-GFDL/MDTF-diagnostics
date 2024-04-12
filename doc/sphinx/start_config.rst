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

* ``NCAR``: Variable names and units used in the default output of models developed at the
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

Adding your model data files
++++++++++++++++++++++++++++

* <*dataset_name*> is any string uniquely identifying the dataset,
* <*frequency*> is a string describing the frequency at which the data is sampled, e.g.
  ``1hr``, ``3hr``, ``6hr``, ``day``, ``mon`` or ``year``.
* <*variable_name*> is the name of the variable in the convention chosen in the previous section.

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

All configuration options for the package are set via its command line interface, which is described in :doc:`ref_cli`,
or by running :console:`% mdtf --help`. Because it's cumbersome to deal with long lists of command-line flags,
options are set in a JSON or Yaml configuration file passed to the package with the ``-f`` flag. An example of this
input file is given in
`templates/runtime_config.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__,
which you used :ref:`previously<ref-execute>` to run the package on test data. We recommend using this file as a
template, making copies and customizing it as needed.

Option values given on the command line always take precedence over those set in the configuration file.
This is so that you can store options that don't frequently change in the file (e.g., input/output paths)
and then use flags to set only those options you want to change from run to run
(e.g., the start and end dates for the analysis). In all cases, the complete set of option values used in each run
of the package is saved as a JSON configuration file in the package's output, so you can always reproduce your results.

Options controlling the analysis
++++++++++++++++++++++++++++++++

The configuration options required to specify what analysis the package should do are:

* ``--CASENAME`` <*name*>: Identifier used to label this run of the package. Can be set to any string.
* ``--experiment`` <*dataset_name*>: The name (subdirectory) you assigned to the data files in the previous section.
If this option isn't given, its value is set from <*CASENAME*>.
* ``--convention`` <*convention name*>: The naming convention used to assign the <*variable_name*>s,
from the previous section.
* ``--startdate`` <*YYYYMMDD*>: The starting year of the analysis period.
* ``--enddate`` <*YYYYMMDD*>: The end year of the analysis period.
An error will be raised if the data provided for any requested variable doesn't span this date range.

If specifying these in a configuration file, these options should given as entry in a list titled ``case_list``
(following the example in
`templates/runtime_config.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__).
Using the package to compare the results of a list of different experiments is a major feature planned for an upcoming
release.

You will also need to specify the list of diagnostics to run. This can be given as a list of POD names (as given in the
`diagnostics/ <https://github.com/tsjackson-noaa/MDTF-diagnostics/tree/main/diagnostics>`__ directory),
 by a ``pod_list`` attribute

Other options
+++++++++++++

Some of the most relevant options which control the package's output are:

* ``--save-ps``: Set this flag to have PODs save copies of all plots as postscript files (vector graphics)
in addition to the bitmaps used in the HTML output pages.
* ``--save-nc``: Set this flag to have PODs retain netCDF files of any intermediate calculations,
which may be useful if you want to do further analyses with your own tools.
* ``--make-variab-tar``: Set this flag to save the collection of files (HTML pages and bitmap graphics)
output by the package as a single .tar file, which can be useful for archival purposes.

The full list of configuration options is given at :doc:`ref_cli`.

Running the package
+++++++++++++++++++

From this point, the instructions for running the package are the same as for
:ref:`running it on the sample data<ref-execute>`, assuming you've set the configuration options by editing a copy o
the configuration file template at `templates/runtime_config.jsonc
 <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates/runtime_config.jsonc>`__. The package is run in the
same way:

.. code-block:: console

   % cd <CODE_ROOT>
   % ./mdtf -f <new config file path>

The first few lines of console output will echo the values you've provided for <*CASENAME*>, etc., as confirmation.

The output of the package will be saved as a series of web pages in a directory named
MDTF\_<*CASENAME*>\_<*startdate*>\_<*enddate*> within <*OUTPUT_DIR*>.
If you run the package multiple times with the same configuration values,
it's not necessary to change the <*CASENAME*>: by default, the suffixes ".v1", ".v2", etc. will be added to duplicate
output directory names so that results aren't accidentally overwritten.

The results of the diagnostics are presented as a series of web pages, with the top-level page named index.html.
To view the results in a web browser, run (e.g.,)
