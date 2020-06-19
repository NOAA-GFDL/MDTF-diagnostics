Walkthrough of framework operation 
==================================

We now describe in greater detail the actions that are taken when the framework is run, focusing only on aspects that are relevant for the operation of individual PODs. For the rest of this walkthrough, the `Example Diagnostic POD <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example>`__ is used as a concrete example to illustrate how a POD is implemented and integrated into the framework. 

.. figure:: ../img/dev_flowchart.jpg
   :align: center
   :width: 100 %

Framework invocation
--------------------

The user runs the framework by executing the framework’s driver script, rather than executing the PODs directly. This is where the user specifies the model run to be analyzed. The user can choose which PODs to run, with the default being all of them except for the example.

See section 3 of the Getting Started for more details on how the package is called. See the :doc:`command line reference <ref_cli>` for documentation on command line options (or run ``mdtf --help``).

Data request
------------

Each POD describes the model data it requires as input in the ``"varlist"`` section of its settings file. The most important features of this file are described in the :doc:`settings file <dev_settings_quick>` and documented in full detail on the :doc:`reference page <ref_settings>`.) Each entry in the ``varlist`` section corresponds to one model data file used by the POD. 

The framework goes through all the PODs to be run and assembles a top-level list of required model data from their ``varlist`` sections. It then queries the source of the model data for the presence of each requested variable with the requested characteristics.

Variables are specified in the settings file in a model-independent way, using `CF convention <http://cfconventions.org/>`__ standard terminology wherever possible. If your POD takes derived quantities as input (column weighted averages, etc.) we recommend that you incorporate whatever preprocessing is necessary to compute these into your POD’s code. Your POD may request variables outside of the CF conventions (by requiring an exact match on the variable name), but please be aware that this will severely limit the situations in which your POD will be run (see below).

It may be that some of the variables your POD requests are not available: they were not saved during the model run, or they weren’t output at the requested frequency (or other characteristics). You have the option to specify a “backup plan” for this situation by designating sets of variables as “alternates,” where this is scientifically feasible: if the framework is unable to obtain a variable that has the “alternates” attribute set in the ``varlist``, it will then (and only then) query the model data source for the variables named as alternates.

If no alternates are defined or the alternate variables are not available, the framework concludes that it’s unable to run the POD on the provided model data. Your POD’s code will not be executed, and an error message listing the missing variables will be presented to the user in your POD’s entry in the top-level results page.

Once the framework has determined which PODs are able to run given the model data, it downloads a local copy of the requested variables.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The example diagnostic uses only one model variable in its `varlist <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L46>`__: surface air temperature, recorded at monthly frequency. 

Runtime environment configuration
---------------------------------

In the first section of your POD’s settings file, we request that you provide a list of programs your POD uses to run (names of interpreters for scripting languages, as well as any utility programs) and any third-party libraries they use.

The framework will check that all these programs and libraries are available on the system it’s running on. The mechanism for doing so will differ, depending on whether the framework is making use of the conda package manager or not. If these dependencies are not found (for whatever reason), your POD will not be run and an error message will be presented to the user.

Example diagnostic
^^^^^^^^^^^^^^^^^^

In its settings file, the example diagnostic lists its `requirements <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/d8d9f951d2c887b9a30fc496298815ab7ee68569/diagnostics/example/settings.jsonc#L38>`__ as the python language interpreter, and the matplotlib, xarray and netCDF4 third-party libraries for python. In this walkthrough, we assume the framework is managing its dependencies using the conda package manager, so the framework assigns the POD to run in the `“python-base” <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_python_base.yml>`__ conda environment, which was created when the user installed the framework.

POD execution
-------------

At this point, your POD’s requirements have been met, so the framework begins execution of your POD’s code by calling the top-level script listed in your POD’s settings file.

All information is passed from the framework to your POD in the form of unix shell environment variables; see the `reference documentation <ref_envvars.html>`__ for details on their names and values.

You should avoid making assumptions about the environment in which your POD will run beyond what’s listed here; a development priority is to interface the framework with cluster and cloud job schedulers to enable individual PODs to run in a concurrent, distributed manner. 

We encourage that your POD produce a log of its progress as it runs: this can be useful in debugging. All text your POD writes to stdout or stderr is captured in a log file and made available to the user.

If your POD experiences a fatal or unrecoverable error, it should signal that to the framework in the conventional unix way by exiting with a return code different from zero. This error will be presented to the user, who can then look over the log file to determine what went wrong.

POD execution: paths
^^^^^^^^^^^^^^^^^^^^

Recall that installing the code will create a directory titled ``MDTF-diagnostics`` containing the files listed on the github page. Below we refer to this MDTF-diagnostics directory as ``$CODE_ROOT``. It contains the following subdirectories:
diagnostics/ : directories containing source code of individual PODs
doc/ : directory containing documentation (a local mirror of the github wiki and documentation site)
src/ : source code of the framework itself
tests/ : unit tests for the framework
Please refer to the Getting Started document, section 3 for background on the paths.

The most important environment variables set by the framework describe the location of resources your POD needs. To achieve the design goal of portability, you should ensure that **no paths are hard-coded in your POD**, for any reason. Instead, they should reference one of the following variable names (note ``$POD_HOME`` is used in linux shell and NCL; in Python ``os.environ["POD_HOME"]`` would be used):

- ``$POD_HOME``: Path to the top-level directory containing your diagnostic’s source code. This will be of the form .../MDTF-diagnostics/diagnostics/<your POD's name>. This can be used to call sub-scripts from your diagnostic’s driver script. This directory should be treated as read-only.

- ``$OBS_DATA``: Path to the top-level directory containing any digested observational or reference data you’ve provided as the author of your diagnostic. Files and sub-directories will be present within this directory with the names and layout in which you supplied them. The framework will ensure this is copied to a local filesystem when your diagnostic is run, but this directory should be treated as read-only. The path to each model data file is provided in an environment variable you name in that variable’s entry in the varlist section of the settings file.

- ``$WK_DIR``: path to your POD’s working directory. This is the only location to which your POD should write files. Within this, the framework will create sub-directories which should be where your output is written:

- ``$WK_DIR/obs/PS`` and ``$WK_DIR/model/PS``: All output plots produced by your diagnostic should be written to one of these two directories. Only files in these locations will be converted to bitmaps for HTML output.

- ``$WK_DIR/obs/netCDF`` and ``$WK_DIR/model/netCDF``: Any output data files your diagnostic wants to make available to the user should be saved to one of these two directories.

Example diagnostic
^^^^^^^^^^^^^^^^^^

The framework starts a unix subprocess, sets environment variables and the conda environment, and runs the `example-diag.py <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example/example_diag.py>`__ script in python. See comments in the code. The script reads the model surface air temperature data located at ``$TAS_FILE``, and reference digested temperature data at ``$OBS_DATA/example_tas_means.nc``.

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
