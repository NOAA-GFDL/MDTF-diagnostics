Walkthrough of framework operation
==================================

We now describe in greater detail the actions that are taken when the framework is run, focusing on aspects that are relevant for the operation of individual PODs. For the rest of this section, the `Example Diagnostic POD <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example>`__ (short name: ``example``) is used as a concrete example to illustrate how a POD is implemented and integrated into the framework.

.. figure:: ../img/dev_flowchart.jpg
   :align: center
   :width: 100 %

Step 1: Framework invocation
----------------------------

The user runs the framework by executing the framework’s main driver script ``$CODE_ROOT/mdtf``, rather than executing the PODs directly. This is where the user specifies the model run to be analyzed, and chooses which PODs to run via the ``pod_list`` section of the configuration input ``src/default_tests.jsonc``.

- Some of the configuration options can be input through command line, see the :doc:`command line reference <ref_cli>` or run ``% $CODE_ROOT/mdtf --help``.

Step 2: Data request
--------------------

Each POD describes the model data it requires as input in the ``varlist`` section of its ``settings.jsonc`` (or simply *settings*) file, with each entry in ``varlist`` corresponding to one model data file used by the POD. The framework goes through all the PODs to be run in ``pod_list`` and assembles a top-level list of required model data from their ``varlist``. It then queries the source of the model data for the presence of each requested variable with the requested characteristics (e.g., frequency, units, etc.).

- The most important features of the settings file are described in the :doc:`settings file <dev_settings_quick>` and documented in full detail on the :doc:`reference page <ref_settings>`.

- Variables are specified in the settings file in a model-independent way, using `CF convention <http://cfconventions.org/>`__ standard terminology wherever possible. If your POD requires derived quantities that are not part of the standard model output (e.g., column weighted averages), you should incorporate necessary preprocessings for computing these from standard output variables into your POD’s code. POD may request variables outside of the CF conventions (by requiring an exact match on the variable name), but this will severely limit the situations in which your POD will be run.

- Some of the variables your POD requests may be unavailable or without the requested frequency (or other characteristics). You can specify a *backup plan* for this situation by designating sets of variables as *alternates* if feasible: when the framework is unable to obtain a variable that has the ``alternates`` attribute in ``varlist``, it will then (and only then) query the model data source for the variables named as alternates.

- If no alternates are defined or the alternate variables are also unavailable, the framework concludes that it’s unable to run the POD on the provided model data. Your POD will not be executed, and an error message listing the missing variables will be presented to the user in your POD’s entry as ``error log`` in the top-level results page ``index.html``.

Once the framework has determined which PODs are able to run given the model data, it prepares the necessary environment variables, including directory paths and the requested variable names (as defined in ``src/filedlist_$convention.jsonc``) for PODs' operation.

- Actually, at this step, the framework also checks the PODs' observational/supporting data under ``inputdata/obs_data/``. If the directory of any of the PODs in ``pod_list`` is missing, the framework would just crash with error messages showing on the terminal.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The example POD uses only one model variable in its `varlist <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L46>`__: surface air temperature, recorded at monthly frequency.

- If you add ``example`` to ``pod_list`` and try to run the framework, it will crash because the directory for observational/supporting data doesn't exist.

- Create an empty ``example`` directory under ``inputdata/obs_data/``. Now the framework can run but would skip the example POD.

Step 3: Runtime environment configuration
-----------------------------------------

In the ``runtime_requirements`` section of your POD’s settings file, we request that you provide a list of languages and third-party libraries your POD uses. The framework will check that all these requirements are met by one of the Conda environments under ``$CONDA_ENV_DIR/``.

- The requirements should be satisfied by one of the existing generic Conda environments (updated by you if necessary), or a new environment you created specifically for your POD.

- If not, your POD will be skipped, with the error message ``Not a conda environment`` included at the end of your POD’s ``log`` entry in the top-level results page ``index.html``.

Example diagnostic
^^^^^^^^^^^^^^^^^^

In its settings file, the example POD lists its `requirements <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L38>`__: Python 3, and the matplotlib, xarray and netCDF4 third-party libraries for Python. In this case, the framework assigns the POD to run in the generic `python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_python3_base.yml>`__ environment provided by the framework.

Step 4: POD execution
---------------------

At this point, your POD’s requirements have been met, so the framework sets the necessary environment variables, activates the right Conda environment, then begins execution of your POD’s code by calling the top-level driver script listed in the settings file.

- All information passed from the framework to your POD is in the form of Unix/Linux shell environment variables; see the `reference documentation <ref_envvars.html>`__ for a complete list of the environment variables.

- We encourage that your POD prints out messages of its progress as it runs. This can be useful in debugging. All text your POD writes to stdout or stderr (i.e., displayed in a terminal) will be captured by the framework and saved in a log file available to the user via ``index.html``.

- Properly structure your code/scripts and include *error and exception handling* mechanisms in your code so that simple issues would not completely shut down the POD's operation. Here are a few suggestions:

   1. Separate basic and advanced diagnostics. Certain computations (e.g., fitting) may need adjustment or are more likely to fail when model performance out of observed range. Organize your POD scripts so that the basic part can produce results even when the advanced part fails.

   2. If some of the observational data files are missing by accident, the POD should still be able to run analysis and produce figures for model data.

   3. Say a POD reads in multiple variable files and computes certain statistics for individual variables. If some of the files are missing or corrupted, the POD should still produce results for the rest.

- The framework contains additional exception-handling mechanisms so that if a POD experiences a fatal or unrecoverable error, the rest of the tasks and POD-calls by the framework can continue. The error messages will be captured and presented to the user as part of the log file to determine what went wrong.

POD execution: paths
^^^^^^^^^^^^^^^^^^^^
@@@
See :ref:`ref-using-env-vars` for the most important environment variables set by the framework for your POD's operation, and `a more comprehensive list <ref_envvars.html>`__. To achieve the design goal of portability, you should ensure that **no paths are hard-coded in your POD**, for any reason. Instead, they should reference one of the environment variables.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The framework starts a subprocess, sets environment variables and the Conda environment, and runs the `example-diag.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example/example_diag.py>`__ script in python. See comments in the code. The script reads the model surface air temperature data located at ``$TAS_FILE``, and reference digested temperature data at ``$OBS_DATA/example_tas_means.nc``.

The calculation performed by the example POD is chosen to be simple: it just does a time average of the model data. The observational data was supplied in time-averaged form, following the instructions for digested results above.

The model time averages are saved to ``$WK_DIR/model/netCDF/temp_means.nc`` for use by the user. Then both the observational and model means are plotted: the model plot is saved to ``$WK_DIR/model/PS/example_model_plot.eps`` and the observational data plot is saved to ``$WK_DIR/obs/PS/example_obs_plot.eps``.

Output and cleanup
------------------

At this point, your POD has successfully finished running, and all remaining tasks are handled by the framework. The framework converts the postscript plots to bitmaps according to the following rule:

- ``$WK_DIR/model/PS/<filename>.eps`` → ``$WK_DIR/model/filename.png``
- ``$WK_DIR/obs/PS/<filename>.eps`` → ``$WK_DIR/obs/filename.png``

The webpage template is copied to ``$WK_DIR`` by the framework, so in writing the template file all plots should be referenced as relative links to this location, eg. "``<A href=model/filename.png>``".

Values of all environment variables are substituted in the html template, allowing you to reference the run’s ``CASENAME`` and date range. Beyond this, we don’t offer a way to alter the text of your POD’s output webpage at run time.

The framework links your POD’s html page to the top-level ``index.html`` page, and copies all files to the specified output location.
