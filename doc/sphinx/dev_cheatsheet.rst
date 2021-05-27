Development Cheatsheet
==============================

Where are the files?
--------------------

My POD scripts and supporting documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
POD files should be placed in a directory that you create in MDTF-diagnostics/diagnostics: MDTF-diagnostics/diagnostics/[POD name].
The files include:
- settings.jsonc: settings file for your POD. You can use the example/settings.jsonc file as template
- POD scripts
- documentation : place in a directory called MDTF-diagnostics/diagnostics/[POD name]/doc. Documentation includes:
    - POD description and links to supporting documentation (.rst file(s))
    - supporting figures

Input Model Data for my POD
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The default input data locations are:
   - model input data: MDTF-diagnostics/../inputdata/model/[dataset name]/[output frequency]
   - observational input data: MDTF-diagnostics/../inputdata/obs_data/[POD name]
Sample datasets should be submitted using the default directory structure.
You may re-define input data locations in the MODEL_DATA_ROOT and OBS_DATA_ROOT definitions in the
default_tests.jsonc file (or whatever the name of your runtime settings jsonc file is).

Output Data from my POD
^^^^^^^^^^^^^^^^^^^^^^^
``${WK_DIR}`` is a framework environment variable defining the working directory, and is set to MDTF-diagnostics/../wkdir by default.
``${WK_DIR}`` contains POD output figures, temporary files, and logs.
You can modify ``${WK_DIR}`` by changing "WORKING_DIR" to the desired location in default_tests.jsonc.

You can also modify the "OUTPUT_DIR" option in default_tests.jsonc to write output files to a different location if you wish.
"OUTPUT_DIR" defaults to "WORKING_DIR" if it is not defined.

POD output files are written to the following locations:
   - Postscript files: ${WK_DIR}/[POD NAME]/[model,obs]/PS
   - Other files, including PNG plots: ${WK_DIR}/[POD NAME]/[model,obs]
The ${WK_DIR}/[POD NAME]/POD.html file should be modified to include the paths to the output plots.


How do I define variables for my POD?
-------------------------------------

Add variables to the "varlist" block in the MDTF-diagnostics/diagnostics/[POD name]/settings.jsonc and define the following:
- the variable name: the short name that will generate the corresponding ``${ENV_VAR}``
(e.g., "zg500" generates the ``${ENV_VAR}`` "zg500_var")
- the standard name with a corresponding entry in the appropriate fieldlist file(s). If your variable is not in the necessary fieldlist file(s),
add them to the file(s), or open an issue on GitHub requesting that the framework team add them.
Once the files are updated, merge the changes from the develop branch into your POD branch. Note that the variable name and the standard name must be unique fieldlist entries.
- variable units
- variable dimensions (e.g., [time, lat, lon])
- scalar coordinates for variables defined on a specific atmospheric pressure level (e.g. {"lev": 250} for a field on the 250-hPa p level).

How do I define and reference environment variables?
----------------------------------------------------

- To define an environment variable specific to your POD, add a "pod_env_vars" block to the "settings" block inyour POD's settings.jsonc file and define the desired variables.
Reference the a variable in your POD (python) code by calling ``os.environ["VARIABLE NAME"]``.
NCL code can reference environment variables by calling ``getenv("VARIABLE NAME")``.

- You can reference the environment variables defined by the framework using os.environ["ENV_VARIABLE_NAME"].
Framework-specific environment variables include:
   - OBS_DATA : path to the top-level directory containing any observational or reference data for your POD
   - POD_HOME : Path to the top-level directory containing your diagnostic’s source code (../MDTF-diagnostics/diagnostics/[POD NAME]).
   - WK_DIR : path to the POD working directory
   - DATADIR : Path to directory containing input data files for one case/experiment
   - CASENAME : User-provided label describing the run of model data being analyzed
   - FIRSTYR: Four-digit year describing the first year of the analysis period
   - LASTYR: Four-digit year describing the last year of the analysis period
