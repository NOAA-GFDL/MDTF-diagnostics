Framework configuration
=======================

In this section we describe configuration options in more generality than the test case described in :doc:`start_install`. 

The complete set of options is described in :doc:`ref_cli`, or by running ``% ./mdtf --help``. All options can be specified as a command-line flag (eg ``--OUTPUT_DIR``) or as a JSON input file of the form provided in `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/default_tests.jsonc>`__. We recommend using this file as a template, making copies and customizing it as needed.

Options given on the command line always take precedence over the input file. This is so you can store options that don't change in the file (eg. the input/output data paths) and use command-line flags to only set the options you want to change from run to run (eg. the analysis period start and end years). In all cases, the complete set of option values used in each run of the framework is included in the output directory, for reproducibility and provenance.

Adding your own model data
--------------------------

Currently the framework is only able to run on model data in the form of NetCDF files on a locally mounted disk following a specific directory hierarchy and filename convention. We hope to offer more flexibility in this area in the near future.

The directory/filename convention we use is 

``$MODEL_DATA_ROOT``/<*CASENAME*>/<*frequency*>/<*CASENAME*>.<*variable*>.<*frequency*>.nc,

where

- <*CASENAME*> is any string used to identify the model run (experiment) that generated the data,
- <*frequency*> is the frequency at which the data is sampled: one of ``1hr``, ``3hr``, ``6hr``, ``day``, ``mon`` or ``year``.
- <*variable*> is the name of the variable in your model's convention.

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

If your model data is available on a locally mounted disk, you can make `symlinks <https://en.wikipedia.org/wiki/Symbolic_link>`__ that have the needed filenames and point to the data, rather than making copies of the files. For example,

::

   % mkdir -p inputdata/model/my_new_experiment/day
   % ln -s <long CMIP path>/pr_day_GFDL-ESM4_historical_r1i1p1f1_gr1_20100101-20141231.nc \
   ? inputdata/model/my_experiment/day/my_new_experiment.pr.day.nc

will create a link to the file in the first argument that can be accessed normally:

::

   inputdata
   ├── model ( = $MODEL_DATA_ROOT)
   │   ├── GFDL.CM4.c96L32.am4g10r8
   │   ├── QBOi.EXP1.AMIP.001
   │   └── my_new_experiment
   │       └── day
   │           └── my_new_experiment.pr.day.nc

Running the code on your experiment's data
------------------------------------------

After adding your experiment's data to the directory hierarchy as described above, you can run the framework on that data using the following options. These can either be set in the "caselist" section of an input file (see `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/default_tests.jsonc>`__ for an example), or individually as command-line flags (eg. ``--CASENAME my_new_experiment``). Required settings are:

- ``CASENAME`` should be the same string used to label your model run,
- ``convention`` describes the variable naming convention your model uses. Currently recognized values are ``CMIP``, for CF-compliant output produced as part of CMIP6 (eg, by post-processing with CMOR) and ``CESM``, ``AM4`` and ``SPEAR``. We hope to offer support for the native variable naming conventions of a wider range of models in the future; for now, we recommend that you run the framework on `cmorized <https://cmor.llnl.gov/>`__ model data.
- ``FIRSTYR`` and ``LASTYR`` specify the analysis period.
- ``model`` and ``experiment`` are recorded if given, but not currently used.

When the framework is run, it determines if the variables each POD analyzes are present in the experiment data. Currently, the framework doesn't have the ability to transform data (eg, to average daily data to monthly frequency), so the match between your model data and each POD's requirements will need to be exact in order for the POD to run. If the framework can't find data requested by a POD, an error message will be logged in place of that POD's output that should help you diagnose the problem.

Other framework settings
------------------------

The paths to input and output data described in :ref:`ref-configure` only need to be modified if the corresponding data is moved (or if you'd like to send output to a new location). Note that the framework doesn't retain default values for paths, so if you run it without an input file, all required paths will need to be given explicitly on the command line.

Other relevant flags controlling the framework's output are:

- ``save_ps``: set to ``true`` to retain the vector .eps figures generated by PODs, in addition to the bitmap images linked to from the webpage.
- ``save_nc``: set to ``true`` to retain netcdf files of any raw output data saved by PODs for further analysis.
- ``make_variab_tar``: set to ``true`` to save the entire output directory as a .tar file, for archival or file transfer purposes.
- ``overwrite``: set to ``true`` to overwrite previous framework output in ``$OUTPUT_DIR``. By default, output with the same CASENAME and date range is assigned a unique name to ensure preexisting results are never overwritten.

These can be set as command-line flags each time the framework is run (eg. ``--save_ps``), or as ``true``/``false`` values in the input file (``"save_ps": true``). Note that ``true`` and ``false`` in JSON must be written all lowercase, with no quotes.

Modifying POD settings
----------------------

Individual PODs may provide user-configurable options in their ``settings.jsonc`` file, in the ``"pod_env_vars"`` section. These only need to be changed in rare or specific cases. Consult the POD's :doc:`documentation <pod_toc>` for details.
