Walkthrough of framework operation
==================================

We now describe in greater detail the actions that are taken when the framework is run, focusing on aspects that are relevant for the operation of individual PODs. The `Example Diagnostic POD <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example>`__ (short name: ``example``) is used as a concrete example .....@@@

.. figure:: ../img/dev_flowchart.jpg
   :align: center
   :width: 100 %

Step 1: Framework invocation
----------------------------

The user runs the framework by executing the framework’s main driver script ``$CODE_ROOT/mdtf``, rather than executing the PODs directly. This is where the user specifies the model run to be analyzed, and chooses which PODs to run via the ``pod_list`` section of the configuration input ``src/default_tests.jsonc``.

- Some of the configuration options can be input through command line, see the :doc:`command line reference <ref_cli>` or run ``% $CODE_ROOT/mdtf --help``.

At this stage, the framework also creates the directory ``$OUTPUT_DIR/`` (default: ``mdtf/wkdir/``) and subdirectories therein for hosting the output files by the framework and PODs from each run.

Note that when running, the framework will collect the messages relevant to individual PODs, including (1) the status of required data and environment, and (2) texts printed out by PODs during execution, and save them as log files under each POD's output directory. These ``log`` files can be viewed via the top-level results page ``index.html`` and are useful for debugging.

Step 2: Data request
--------------------

Each POD describes the model data it requires as input in the ``varlist`` section of its ``settings.jsonc`` file, with each entry in ``varlist`` corresponding to one model data file used by the POD. The framework goes through all the PODs to be run in ``pod_list`` and assembles a top-level list of required model data from their ``varlist``. It then queries the source of the model data for the presence of each requested variable with the requested characteristics (e.g., frequency, units, etc.).

- The most important features of ``settings.jsonc`` are described in the :doc:`settings file <dev_settings_quick>` and documented in full detail on the :doc:`reference page <ref_settings>`.

- Variables are specified in ``settings.jsonc`` following `CF convention <http://cfconventions.org/>`__ wherever possible. If your POD requires derived quantities that are not part of the standard model output (e.g., column weighted averages), incorporate necessary preprocessings for computing these from standard output variables into your code. POD are allowed to request variables outside of the CF conventions (by requiring an exact match on the variable name), but this will severely limit the POD's application.

- Some of the requested variables may be unavailable or without the requested characteristics (e.g., frequency). You can specify a *backup plan* for this situation by designating sets of variables as *alternates* if feasible: when the framework is unable to obtain a variable that has the ``alternates`` attribute in ``varlist``, it will then (and only then) query the model data source for the variables named as alternates.

- If no alternates are defined or the alternate variables are also unavailable, the framework will skip executing your POD, and an ``error log`` will be presented in ``index.html``.

Once the framework has determined which PODs are able to run given the model data, it prepares the necessary environment variables, including directory paths and the requested variable names (as defined in ``src/filedlist_$convention.jsonc``) for PODs' operation.

- At this step, the framework also checks the PODs' observational/supporting data under ``inputdata/obs_data/``. If the directory of any of the PODs in ``pod_list`` is missing, the framework would terminate with error messages showing on the terminal. Note that the framework only checks the presence of the directory, but not the files therein.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The example POD uses only one model variable in its `varlist <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L46>`__: surface air pressure, recorded at monthly frequency.

1. If you add ``example`` to ``pod_list`` (using the ``QBOi.EXP1.AMIP.001`` case) and try to run the framework, it will crash because the directory for observational/supporting data doesn't exist. We recommend you to comment out other entries in ``pod_list``

2. Create an empty ``example`` directory under ``inputdata/obs_data/``. Now the framework can run the example POD, which cannot produce results for observations.

Step 3: Runtime environment configuration
-----------------------------------------

In the ``runtime_requirements`` section of your POD’s ``settings.jsonc``, we request that you provide a list of languages and third-party libraries your POD uses. The framework will check that all these requirements are met by one of the Conda environments under ``$CONDA_ENV_DIR/``.

- The requirements should be satisfied by one of the existing generic Conda environments (updated by you if necessary), or a new environment you created specifically for your POD.

- If there isn't a suitable environment, your POD will be skipped with a ``Not a conda environment`` error message added to the log file.

Example diagnostic
^^^^^^^^^^^^^^^^^^

In its ``settings.jsonc``, the example POD lists its `requirements <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L38>`__: Python 3, and the matplotlib, xarray and netCDF4 third-party libraries for Python. In this case, the framework assigns the POD to run in the generic `python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_python3_base.yml>`__ environment provided by the framework.

3. In 2, you should be able to get results from the example POD. You can try to hide the python3_base environment (e.g., by temporarily renaming the ``_MDTF_python3_base`` directory under ``$CONDA_ENV_DIR/``), and run the framework again. You'll see the error message in the new log file. Don't forget to undo the change to the ``_MDTF_python3_base`` directory afterwards.

Step 4: POD execution
---------------------

At this point, your POD’s requirements have been met, so the framework (1) sets the necessary environment variables, (2) activates the right Conda environment, then (3) begins execution of your POD’s code by calling the top-level driver script listed in its ``settings.jsonc``.

- See :ref:`ref-using-env-vars` for most relevant environment variables, and how your POD is expected to output results.

- All information passed from the framework to your POD is in the form of Unix/Linux shell environment variables; see `reference <ref_envvars.html>`__ for a complete list of environment variables.

- For debugging, we encourage that your POD prints out messages of its progress as it runs. All text written to stdout or stderr (i.e., displayed in a terminal) will be captured by the framework and added to a log file available to the users via ``index.html``.

- Properly structure your code/scripts and include *error and exception handling* mechanisms so that simple issues would not completely shut down the POD's operation. Here are a few suggestions:

   A. Separate basic and advanced diagnostics. Certain computations (e.g., fitting) may need adjustment or are more likely to fail when model performance out of observed range. Organize your POD scripts so that the basic part can produce results even when the advanced part fails.

   B. If some of the observational data files are missing by accident, the POD should still be able to run analysis and produce figures for model data regardless.

   C. Say a POD reads in multiple variable files and computes statistics for individual variables. If some of the files are missing or corrupted, the POD should still produce results for the rest. (Although in this case, the framework would skip this POD anyway.)

- The framework contains additional exception-handling mechanisms so that if a POD experiences a fatal or unrecoverable error, the rest of the tasks and POD-calls by the framework can continue. The error messages will be included in the POD's log file.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The framework calls the driver script `example-diag.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example/example_diag.py>`__ listed in ``settings.jsonc``. Take a look at the script and the comments therein.

The the script performs tasks roughly in the following order:

   (1) It reads the model surface air pressure data located at ``$PS_FILE``,
   (2) computes the time average,
   (3) saves the model time averages to ``$WK_DIR/model/netCDF/temp_means.nc`` for later use,
   (4) plots model figure ``$WK_DIR/model/PS/example_model_plot.eps``,
   (5) reads the digested pressure data in time-averaged form at ``$OBS_DATA/example_ps_means.nc``, and
   (6) saves the observational data plot to ``$WK_DIR/obs/PS/example_obs_plot.eps``.

4. The digested pressure data wasn't provided with the code package. If you've followed 2, the example POD is still able generate the html page but with observational figure missing. This is because the script is organized to finish plotting the model figure before accessing the missing digested pressure data. You can try moving the lines corresponding to (5) and (6) upward in the script to see how the POD can fail without producing meaningful results.

5. In 2, the model time average has been saved to ``$WK_DIR/model/netCDF/temp_means.nc``. To make the example POD function normally, copy, move, and rename the file to ``$OBS_DATA/example_ps_means.nc``, and run the framework again.

Step 5: Output and cleanup
--------------------------

At this point, your POD has successfully finished running, and all remaining tasks are handled by the framework. The framework converts the postscript plots to bitmaps according to the following rule:

- ``$WK_DIR/model/PS/<filename>.eps`` → ``$WK_DIR/model/filename.png``
- ``$WK_DIR/obs/PS/<filename>.eps`` → ``$WK_DIR/obs/filename.png``

The html template for each POD is then copied to ``$WK_DIR`` by the framework.

- In writing the template file all plots should be referenced as relative links to this location, e.g., "``<A href=model/filename.png>``". See templates from existing POD.

- Values of all environment variables referenced in the html template are substituted by the framework, allowing you to show the run’s ``CASENAME``, date range, etc. Beyond this, (i.e., through environment variables), we don’t offer other ways to alter the text of your POD’s output webpage at run time.

Finally, the framework links your POD’s html page to the top-level ``index.html``, and copies all files to the specified output location.
