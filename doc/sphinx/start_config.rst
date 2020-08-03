Framework configuration for user model data
===========================================

In this section we describe how to run the framework with your own model data, and more configuration options than the test case described in :doc:`start_install`.

The complete set of configuration options is described in :doc:`ref_cli`, or by running ``% ./mdtf --help``. All options can be specified as a command-line flag (e.g., ``--OUTPUT_DIR``) or as a JSON configuration input file of the form provided in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/default_tests.jsonc>`__. We recommend using this file as a template, making copies and customizing it as needed.

Options given on the command line always take precedence over the input file. This is so you can store options that don't frequently change in the file (e.g., the input/output data paths) and use command-line flags to set only those options you want to change from run to run (e.g., the analysis period start and end years). In all cases, the complete set of option values used in each run of the framework will be included in the log file as part of the output, for reproducibility and provenance.

**Summary of steps for running the framework on user data**

1. Save or link model data files following the framework's filename convention.
2. Select the variable name convention used by the model.
3. Edit the configuration input file accordingly, then 
4. Run the framework.

Adding your model data
----------------------

Currently the framework is only able to run on model data in the form of NetCDF files on a locally mounted disk following a specific directory hierarchy and filename convention, with one variable per file. We hope to offer more flexibility in this area in the near future.

The directory/filename convention we use is

``$MODEL_DATA_ROOT``/$CASENAME/$frequency/$CASENAME.$variable.$frequency.nc,

where

- $CASENAME is any string used to identify the model run (experiment) that generated the data,
- $frequency is the frequency at which the data is sampled: one of ``1hr``, ``3hr``, ``6hr``, ``day``, ``mon`` or ``year``.
- $variable is the name of the variable in your model's convention.

As an example, here's how the sample model data is organized:

::

   inputdata
   ├── model ( = $MODEL_DATA_ROOT)
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
   └── obs_data ( = $OBS_DATA_ROOT)
       ├── (... supporting data for individual PODs )

If your model data is available on a locally mounted disk, we recommend creating `symlinks <https://en.wikipedia.org/wiki/Symbolic_link>`__ that have the needed filenames and point to the data, rather than making copies of the files. For example,

::

   % mkdir -p inputdata/model/my_new_experiment/day
   % ln -s $path_to_file/pr_day_GFDL-ESM4_historical_r1i1p1f1_gr1_20100101-20141231.nc inputdata/model/my_experiment/day/my_new_experiment.pr.day.nc

will create a link to the file in the first argument that can be accessed normally:

::

   inputdata
   ├── model ( = $MODEL_DATA_ROOT)
   │   ├── GFDL.CM4.c96L32.am4g10r8
   │   ├── QBOi.EXP1.AMIP.001
   │   └── my_new_experiment
   │       └── day
   │           └── my_new_experiment.pr.day.nc

Select the model's variable name convention
-------------------------------------------

The framework requires specifying a convention for variable names used in the model data. Currently recognized conventions are

- ``CMIP``, for CF-compliant output produced as part of CMIP6;
- ``CESM``, for the NCAR `community earth system model <http://www.cesm.ucar.edu/>`__;
- ``AM4``, for the NOAA-GFDL `atmosphere model <https://www.gfdl.noaa.gov/am4/>`__;
- ``SPEAR``, for the NOAA-GFDL `seasonal model <https://www.gfdl.noaa.gov/research_highlight/spear-the-next-generation-gfdl-modeling-system-for-seasonal-to-multidecadal-prediction-and-projection/>`__.

We hope to offer support for the variable naming conventions of a wider range of models in the future. For the time being, please process output of models not on this list with `CMOR <https://cmor.llnl.gov/>`__ to make them CF-compliant.

Alternatively, the framework will load any lookup tables of the form ``src/fieldlist_$convention.jsonc`` and use them for variable name conversion. Users can add new files in this format to specify new conventions. For example, in ``src/fieldlist_CESM.jsonc`` the line ``"pr_var" : "PRECT"`` means that the CESM name for the precipitation rate is PRECT (case sensitive). In addition, ``"pr_conversion_factor" : 1000`` specifies the conversion factor to CF standard units for this variable.

Running the code on your data
-----------------------------

After adding your model data to the directory hierarchy as described above, you can run the framework on that data using the following options. These can either be set in the ``caselist`` section of the configuration input file (see `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/default_tests.jsonc>`__ for an example/template), or individually as command-line flags (e.g., ``--CASENAME my_new_experiment``). Required settings are:

- ``CASENAME`` should be the same string used to label your model run.
- ``convention`` describes the variable naming convention your model uses, determined in the previous section.
- ``FIRSTYR`` and ``LASTYR`` specify the analysis period.
- ``model`` and ``experiment`` are recorded if given, but not currently used.

When the framework is run, it determines whether the data each POD needs to run is present in the model data being provided. Specifically, the model must provide all variables needed by a POD at the required frequency. Consult the :doc:`documentation <pod_toc>` for a POD to determine the data it requires.

If the framework can't find data requested by a POD, an error message will be logged in place of that POD's output that should help you diagnose the problem. We hope to add the ability to transform data (eg, to average daily data to monthly frequency) in order to simplify this process.

Other framework settings
------------------------

The paths to input and output data (described in :ref:`ref-configure`) only need to be modified if the corresponding data is moved, or if you'd like to send output to a new location. Note that the framework doesn't retain default values for paths, so if you don't specify a configuration file, all required paths will need to be given explicitly on the command line.

Other relevant flags controlling the framework's output are:

- ``save_ps``: set to ``true`` to retain the vector .eps figures generated by PODs, in addition to the bitmap images linked to from the webpage.
- ``save_nc``: set to ``true`` to retain netcdf files of any data output at intermediate steps by PODs for further analysis.
- ``make_variab_tar``: set to ``true`` to save the entire output directory as a .tar file, for archival or file transfer purposes.
- ``overwrite``: set to ``true`` to overwrite previous framework output in ``$OUTPUT_DIR``. By default, output with the same CASENAME and date range is assigned a unique name to ensure preexisting results are never overwritten.

These can be set as command-line flags each time the framework is run (e.g.,. ``--save_ps``), or as ``true``/``false`` values in the input file (``"save_ps": true``). Note that ``true`` and ``false`` in JSON must be written all lowercase, with no quotes.

Modifying POD settings
----------------------

Individual PODs may provide user-configurable options in the ``"pod_env_vars"`` section of their ``settings.jsonc`` file, which is located in each POD's source code directory under ``/diagnostics``. These only need to be changed in rare or specific cases. Consult the POD's :doc:`documentation <pod_toc>` for details.
