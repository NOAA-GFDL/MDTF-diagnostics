Development Cheatsheet
==============================

Creating and submitting a POD
-----------------------------
1. Prepare for implementation  

   - Run the unmodified MDTF-diagnostics package to make sure that your conda installation, directory structure, etc... are set up properly  
   - Modify the conda environment to work for your POD by adding a configuration file ``MDTF_diagnostics/src/conda/env_[YOUR POD NAME].yml`` with any new required modules.  Be sure to re-run ``MDTF-diagnostics/src/conda/conda_env_setup.sh`` to install your POD's environment if it requires a separate YAML file with additional modules.
   - Name your POD, make a directory for your POD in MDTF-diagnostics/diagnostics, and move your code to your POD directory  
   - ``cp`` your observational data to ``MDTF_diagnostics/../inputdata/obs_data/[YOUR POD NAME]``  
   - If necessary, ``cp`` your model data to ``MDTF_diagnostics/../inputdata/model/[model dataset name]`` 
2. Link your POD code into the framework  

   - Modify your POD's driver script (e.g, ``driver.py``) to interface with your code
   - Modify pod's ``settings.jsonc`` to specify variables that will be passed to the framework
   - Modify your code to use ``ENV_VARS`` provided by the framework (see the *Notes* for descriptions of the available environment variables)
      - Input files:
         - model input data: ``MDTF-diagnostics/../inputdata/model/[dataset name]/[output frequency]``
         - observational input data: ``MDTF-diagnostics/../inputdata/obs_data/[POD name]``
         - Sample datasets should be submitted using the default directory structure
         - You may re-define input data locations in the ``MODEL_DATA_ROOT`` and ``OBS_DATA_ROOT`` definitions in the ``default_tests.jsonc`` file (or whatever the name of your runtime settings jsonc file is).
      - Working files: 
         - ``${WK_DIR}`` is a framework environment variable defining the working directory. It is set to ``MDTF-diagnostics/../wkdir`` by default.
         - ``${WK_DIR}`` contains temporary files and logs. 
         - You can modify ``${WK_DIR}`` by changing "WORKING_DIR" to the desired location in ``default_tests.jsonc``
      - Output files: 
         - POD output files are written to the following locations by the framework:
            - Postscript files: ``${WK_DIR}/[POD NAME]/[model,obs]/PS``
            - Other files, including PNG plots: ``${WK_DIR}/[POD NAME]/[model,obs]``
         - Set the "OUTPUT_DIR" option in default_tests.jsonc to write output files to a different location; "OUTPUT_DIR" defaults to "WORKING_DIR" if it is not defined.
         - Output figure locations:  
            - PNG files should be placed directly in ``$WK_DIR/obs/`` and ``$WK_DIR/model/``  
            - If a POD chooses to save vector-format figures, they should be written into the ``$WK_DIR/obs/PS`` and ``$WK_DIR/model/PS`` directories. Files in these locations will be converted by the framework to PNG, so use those names in the html file.
            - If a POD uses matplotlib, it is recommended to write as figures as EPS instead of PS because of potential bugs
   
   - Modify html files to point to the figure names

3. Place your documentation in ``MDTF-diagnostics/diagnostics/[YOUR POD NAME]/docs``
4. Test your code with the framework 
5. Submit a Pull Request for your POD using the GitHub website

Notes:
------
- **Make sure that WORKING_DIR and OUTPUT_DIR have enough space to hold datafor your POD(s) AND any PODs included in the package.**
- Defining POD variables
   - Add variables to the ``varlist`` block in the ``MDTF-diagnostics/diagnostics/[POD name]/settings.jsonc`` and define the following:  
      - the variable name: the short name that will generate the corresponding ``${ENV_VAR}`` (e.g., "zg500" generates the ``${ENV_VAR}`` "zg500_var")
      - the standard name with a corresponding entry in the appropriate fieldlist file(s)  
      - variable units
      - variable dimensions (e.g., [time, lat, lon])
      - scalar coordinates for variables defined on a specific atmospheric pressure level (e.g. ``{"lev": 250}`` for a field on the 250-hPa p level).
   - If your variable is not in the necessary fieldlist file(s), add them to the file(s), or open an issue on GitHub requesting that the framework team add them. Once the files are updated, merge the changes from the main branch into your POD branch. 
   - Note that the variable name and the standard name must be unique fieldlist entries
- Environment variables
   - To define an environment variable specific to your POD, add a ``"pod_env_vars"`` block to the ``"settings"`` block in your POD's ``settings.jsonc`` file and define the desired variables 
   - Reference an environment variable in Python by calling ``os.environ["VARIABLE NAME"]``  
   - NCL code can reference environment variables by calling ``getenv("VARIABLE NAME")``  
   - Framework-specific environment variables include:
      - OBS_DATA : path to the top-level directory containing any observational or reference data for your POD
      - POD_HOME : Path to the top-level directory containing your POD's source code
      - WK_DIR : path to the POD working directory
      - DATADIR : Path to directory containing input data files for one case/experiment
      - CASENAME : User-provided label describing the run of model data being analyzed
      - FIRSTYR: Four-digit year describing the first year of the analysis period
      - LASTYR: Four-digit year describing the last year of the analysis period
