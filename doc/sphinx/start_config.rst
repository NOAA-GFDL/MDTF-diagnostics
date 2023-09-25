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

For a list of the available data sources, what types of model data they provide and how to configure them,
see the :doc:`data source reference<ref_data_sources>`. In the rest of this section,
we describe the steps required to add your own model data for use with the
:ref:`LocalFile<ref-data-source-localfile>` data source, since it's currently the most general-purpose option.

Selecting and formatting the model data
+++++++++++++++++++++++++++++++++++++++

Consult the `list of available PODs <https://github.com/NOAA-GFDL/MDTF-diagnostics#available-and-planned-diagnostics>`__
to identify which diagnostics you want to run and what variables are required as input for each. In general,
if the data source can't find data that's required by a POD,
an error message will be logged in place of that POD's output that should help you diagnose the problem.

The LocalFile data source works with model data structured with each variable stored in a separate netCDF file.
Some additional conditions on the metadata are required: any model output compliant with the
`CF conventions <http://cfconventions.org/>`__ is acceptable, but only a small subset of those conventions are required
by this data source. See the :doc:`data format reference<ref_data>` for a complete description of what's required.

Naming variables according to a convention
++++++++++++++++++++++++++++++++++++++++++

The LocalFile data source is intended to deal with output produced by different models,
which poses a problem because different models use different variable names for the same physical quantity.
For example, in NCAR's `CESM2 <https://www.cesm.ucar.edu/models/cesm2/>`__ the name for total precipitation is
``PRECT``, while the name for the same quantity in GFDL's
`CM4 <https://www.gfdl.noaa.gov/coupled-physical-model-cm4/>`__ is ``precip``.

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

The LocalFile data source reads files from a local directory that follow the filename convention used
for the sample model data. Specifically, the files should be placed in a subdirectory in <*MODEL_DATA_ROOT*>
and named following the pattern

<*MODEL_DATA_ROOT*>/<*dataset_name*>/<*frequency*>/<*dataset_name*>.<*variable_name*>.<*frequency*>.nc,

where

* <*MODEL_DATA_ROOT*> is the path where the sample model data was installed (see :ref:`ref-configure`),
* <*dataset_name*> is any string uniquely identifying the dataset,
* <*frequency*> is a string describing the frequency at which the data is sampled, e.g. ``1hr``, ``3hr``, ``6hr``, ``day``, ``mon`` or ``year``.
* <*variable_name*> is the name of the variable in the convention chosen in the previous section.

As an example, here's how the sample model data is organized:

::

   inputdata
   ├── model ( = <MODEL_DATA_ROOT>)
   │   ├── GFDL.CM4.c96L32.am4g10r8
   │   │   └── day
   │   │       ├── GFDL.CM4.c96L32.am4g10r8.precip.day.nc
   │   │       └── (... other .nc files )
   │   └── QBOi.EXP1.AMIP.001
   │       ├── 1hr
   │       │   ├── QBOi.EXP1.AMIP.001.PRECT.1hr.nc
   │       │   └── (... other .nc files )
   │       ├── 3hr
   │       │   └── QBOi.EXP1.AMIP.001.PRECT.3hr.nc
   │       ├── day
   │       │   ├── QBOi.EXP1.AMIP.001.FLUT.day.nc
   │       │   └── (... other .nc files )
   │       └── mon
   │           ├── QBOi.EXP1.AMIP.001.PS.mon.nc
   │           └── (... other .nc files )

Note that the ``GFDL.CM4.c96L32.am4g10r8`` dataset uses the ``GFDL`` convention (precipitation = ``precip``), while the ``QBOi.EXP1.AMIP.001`` dataset uses the ``NCAR`` convention (precipitation = ``PRECT``).

If the data you want to analyze is available on a locally mounted disk, we recommend creating `symlinks <https://en.wikipedia.org/wiki/Symbolic_link>`__ that have the needed filenames, rather than making copies of the data files. For example,

.. code-block:: console

   % mkdir -p inputdata/model/my_dataset/day
   % ln -s <path> inputdata/model/my_dataset/day/my_dataset.pr.day.nc

will create a symbolic link to the file at <*path*> that follows the filename convention used by this data source:

::

   inputdata
   ├── model ( = <MODEL_DATA_ROOT>)
   │   ├── GFDL.CM4.c96L32.am4g10r8
   │   ├── QBOi.EXP1.AMIP.001
   │   └── my_dataset
   │       └── day
   │           └── my_dataset.pr.day.nc

Finally, we note that it's not necessary to place the files (or symlinks) for all experiments in <*MODEL_DATA_ROOT*>. To point the LocalFile data source to data stored in the subdirectory hierarchy following the pattern described above, but located in a different place, pass that location to the package as <*CASE_ROOT_DIR*>.

Running the package on your data
--------------------------------

How to configure the package
++++++++++++++++++++++++++++

All configuration options for the package are set via its command line interface, which is described in :doc:`ref_cli`, or by running :console:`% mdtf --help`. Because it's cumbersome to deal with long lists of command-line flags, options can also be set in a JSON configuration file passed to the package with the ``-f``/``--input-file`` flag. An example of this input file is given in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__, which you used :ref:`previously<ref-execute>` to run the package on test data. We recommend using this file as a template, making copies and customizing it as needed.

Option values given on the command line always take precedence over those set in the configuration file. This is so that you can store options that don't frequently change in the file (e.g., input/output paths) and then use flags to set only those options you want to change from run to run (e.g., the start and end years for the analysis). In all cases, the complete set of option values used in each run of the package is saved as a JSON configuration file in the package's output, so you can always reproduce your results.

Options controlling the analysis
++++++++++++++++++++++++++++++++

The configuration options required to specify what analysis the package should do are:

* ``--CASENAME`` <*name*>: Identifier used to label this run of the package. Can be set to any string.
* ``--experiment`` <*dataset_name*>: The name (subdirectory) you assigned to the data files in the previous section.
If this option isn't given, its value is set from <*CASENAME*>.
* ``--convention`` <*convention name*>: The naming convention used to assign the <*variable_name*>s,
from the previous section.
* ``--FIRSTYR`` <*YYYY*>: The starting year of the analysis period.
* ``--LASTYR`` <*YYYY*>: The end year of the analysis period. The analysis period includes all data that falls
between the start of 1 Jan on <*FIRSTYR*> and the end of 31 Dec on <*LASTYR*>.
An error will be raised if the data provided for any requested variable doesn't span this date range.

If specifying these in a configuration file, these options should given as entry in a list titled ``case_list``
(following the example in
`src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__).
Using the package to compare the results of a list of different experiments is a major feature planned for an upcoming
release.

You will also need to specify the list of diagnostics to run. This can be given as a list of POD names (as given in the `diagnostics/ <https://github.com/tsjackson-noaa/MDTF-diagnostics/tree/main/diagnostics>`__ directory), or ``all`` to run all PODs. This list can be given by the ``--pods`` command-line flag, or by a ``pod_list`` attribute in the ``case_list`` entry.

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

From this point, the instructions for running the package are the same as for :ref:`running it on the sample data<ref-execute>`, assuming you've set the configuration options by editing a copy of the configuration file template at `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__. The package is run in the same way:

.. code-block:: console

   % cd <CODE_ROOT>
   % ./mdtf -f <new config file path>

The first few lines of console output will echo the values you've provided for <*CASENAME*>, etc., as confirmation.

The output of the package will be saved as a series of web pages in a directory named
MDTF\_<*CASENAME*>\_<*FIRSTYR*>\_<*LASTYR*> within <*OUTPUT_DIR*>.
If you run the package multiple times with the same configuration values,
it's not necessary to change the <*CASENAME*>: by default, the suffixes ".v1", ".v2", etc. will be added to duplicate
output directory names so that results aren't accidentally overwritten.

The results of the diagnostics are presented as a series of web pages, with the top-level page named index.html.
To view the results in a web browser, run (e.g.,)

.. code-block:: console

   % google-chrome <OUTPUT_DIR>/MDTF_<CASENAME>_<FIRSTYR>_<LASTYR>/index.html &
