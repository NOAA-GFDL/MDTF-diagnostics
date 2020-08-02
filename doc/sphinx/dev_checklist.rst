POD Development Checklist
=========================

In this section, we compile a to-do list summarizing necessary steps for POD implementation, as well as a checklist for mandatory POD documentation and testing before submitting your POD.

We recommend running the framework on the sample model data again with both ``save_ps`` and ``save_nc`` in the configuration input ``src/default_tests.jsonc`` set to ``true``. This will preserve directories and files created by individual PODs in the output directory, which could come in handy when you go through the instructions below, and help understand how a POD is expected to write output.

Preparation for POD implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We assume that, at this point, you have a set of scripts, written in :doc:`languages <dev_instruct>` consistent with the framework's open source policy, that a) read in model data, b) perform analysis, and c) output figures. Here are 3 steps to prepare your scripts for POD implementation.

- Give your POD an official name (e.g., *Convective Transition*; referred to as ``long_name``) and a short name (e.g., *convective_transition_diag*). The latter will be used consistently to name the directories and files associated with your POD, so it should (1) loosely resemble the long_name, (2) avoid space bar and special characters (!@#$%^&\*), and (3) not repeat existing PODs' name (i.e., the directory names under ``diagnostics/``). Try to make your POD's name specific enough that it will be distinct from PODs contributed now or in the future by other groups working on similar phenomena.

- If you have multiple scripts, organize them so that there is a main driver script calling the other scripts, i.e., a user only needs to execute the driver script to perform all read-in data, analysis, and plotting tasks. This driver script should be named after the POD's short name (e.g., ``convective_transition_diag.py``).

- You should have no problem getting scripts working as long as you have (1) the location and filenames of model data, (2) the model variable naming convention, and (3) where to output files/figures. The framework will provide these as *environment variables* that you can access (e.g., using ``os.environ`` in Python, or ``getenv`` in NCL). *DO NOT* hard code these paths/filenames/variable naming convention, etc., into your scripts. See the `complete list <ref_envvars.html>`__ of environment variables supplied by the framework.

- Your scripts should not access the internet or other networked resources.

.. _ref-example-env-vars:

An example of using framework-provided environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The framework provides a collection of environment variables, mostly in the format of strings but also some numbers, so that you can and *MUST* use in your code to make your POD portable and reusable.

For instance, using 3 of the environment variables provided by the framework, ``CASENAME``, ``DATADIR``, and ``pr_var``, the full path to the hourly precipitation file can be expressed as

::

   MODEL_OUTPUT_DIR = os.environ["DATADIR"]+"/1hr/"
   pr_filename = os.environ["CASENAME"]+"."+os.environ["pr_var"]+".1hr.nc"
   pr_filepath = MODEL_OUTPUT_DIR + pr_filename

You can then use ``pr_filepath`` in your code to load the precipitation data.

Note that in Linux shell or NCL, the values of environment variables are accessed via a ``$`` sign, e.g., ``os.environ["CASENAME"]`` in Python is equivalent to ``$CASENAME`` in Linux shell/NCL.

.. _ref-using-env-vars:

Relevant environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment variables most relevant for a POD's operation are:

- ``POD_HOME``: Path to directory containing POD's scripts, e.g., ``diagnostics/convective_transition_diag/``.

- ``OBS_DATA``: Path to directory containing POD's supporting/digested observation data, e.g., ``inputdata/obs_data/convective_transition_diag/``.

- ``DATADIR``: Path to directory containing model data files for one case/experiment, e.g., ``inputdata/model/QBOi.EXP1.AMIP.001/``.

- ``WK_DIR``: Path to directory for POD to output files. Note that **this is the only directory a POD is allowed to write its output**. E.g., ``wkdir/MDTF_QBOi.EXP1.AMIP.001_1977_1981/convective_transition_diag/``.

   1. Output figures to ``$WK_DIR/obs/`` and ``$WK_DIR/model/`` respectively.

   2. ``$WK_DIR/obs/PS/`` and ``$WK_DIR/model/PS/``: If a POD chooses to save vector-format figures, save them as ``EPS`` under these two directories. Files in these locations will be converted by the framework to ``PNG`` for HTML output. Caution: avoid using ``PS`` because of potential bugs in recent ``matplotlib`` and converting to PNG.

   3. ``$WK_DIR/obs/netCDF/`` and ``$WK_DIR/model/netCDF/``: If a POD chooses to save digested data for later analysis/plotting, save them in these two directories in ``NetCDF``.

Note that (1) values of ``POD_HOME``, ``OBS_DATA``, and ``WK_DIR`` change when the framework executes different PODs; (2) the ``WK_DIR`` directory and subdirectories therein are automatically created by the framework. **Each POD should output files as described here** so that the framework knows where to find what, and also for the ease of code maintenance.

More environment variables for specifying model variable naming convention can be found in the ``src/filedlist_$convention.jsonc`` files. Also see the `list <ref_envvars.html>`__  of environment variables supplied by the framework.

To-do list for POD implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following are the necessary steps for the POD module implementation and integration into the framework. You can use the PODs currently included in the code package under ``diagnostics/`` as concrete examples since they all have the same structure as described below:

1. Create your POD directory under ``diagnostics/`` and put all scripts in. Among the scripts, there should be 1) a main driver script, 2) a template html, and 3) a ``settings.jsonc`` file. The POD directory, driver script, and html template should all be named after your POD's short name.

   - For instance, ``diagnostics/convective_transition_diag/`` contains its driver script ``convective_transition_diag.py``, ``convective_transition_diag.html``, and ``settings.jsonc``, etc.

   - The framework will call the driver script, which calls the other scripts in the same POD directory.

   - The html template will be copied by the framework into the output directory to display the figures generated by the POD. You should be able to create a new html template by simply copying and modifying the example templates from existing PODs even without prior knowledge about html syntax.

   - ``settings.jsonc`` contains a POD's information. The framework will read this setting file to find out the driver script's name, verify the required environment and model data files are available, and prepare the necessary environment variables before executing the driver script.

2. Create a directory under ``inputdata/obs_data/`` named after the short name, and put all your *digested* observation data in (or more generally, any quantities that are independent of the model being analyzed).

   - Digested data should be in the form of numerical data, not figures.

   - Raw data, e.g., undigested reanalysis data will be rejected.

   - The data files should be small (preferably a few MB) and just enough for producing figures for model comparison.

   - If you really cannot reduce the data size or require GB of space, consult with the lead team.

3. Provide the Conda environment your POD requires. Either you can use one of the Conda environments currently supplied with the framework, defined by the YAML (.yml) files in ``src/conda/``, or submit a .yml file for a new environment.

   - We recommend using existing Conda environments as much as possible. Consult with the lead team if you would like to submit a new one.

   - If you need a new Conda environment, add a new .yml file to ``src/conda/``, and install the environment using the ``conda_env_setup.sh`` script as described in the :doc:`Getting Started <start_install>`.

4. If your POD requires model data not included in the samples, prepare your own data files following instructions given in the :doc:`Getting Started <start_config>`, and create a new configuration input from the template ``src/default_tests.jsonc``.

Update ``case_list`` and ``pod_list`` in the configuration input file for your POD. Now you can try to run the framework following the :doc:`Getting Started <start_install>` and start debugging. Good luck!

.. _ref-checklist:

Checklist before submitting your POD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After getting your POD working under the framework, there are 2 additional steps regarding the mandatory POD documentation and testing before you can submit your work to the lead team.

4. Provide documentation following the templates:

   A. Provide a comprehensive POD documentation in reStructuredText (.rst) format. This should include a one-paragraph synopsis of the POD, developers’ contact information, required programming language and libraries, and model output variables, a brief summary of the presented diagnostics as well as references in which more in-depth discussions can be found.

      - Create a ``doc`` directory under your POD directory (e.g., ``diagnostics/convective_transition_diag/doc/``) and put the .rst file and figures inside. It should be easy to copy and modify the .rst examples from existing PODs.

   B. All scripts should be self-documenting by including in-line comments. The main driver script (e.g., ``convective_transition_diag.py``) should contain a comprehensive header providing information that contains the same items as in the POD documentation, except for the "More about this diagnostic" section.

   C. The one-paragraph POD synopsis (in the POD documentation) as well as a link to the Full Documentation should be placed at the top of the html template (e.g., ``convective_transition_diag.html``).

5. Test before distribution. It is important that you test your POD before sending it to the lead team contact. Please take the time to go through the following procedures:

   A. Test how the POD fails. Does it stop with clear errors if it doesn’t find the files it needs? How about if the dates requested are not presented in the model data? Can developers run it on data from another model? Here are some simple tests you should try:

      - Move the ``inputdata`` directory around. Your POD should still work by simply updating the values of ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` in the configuration input file.

      - Try to run your POD with a different set of model data. For POD development and testing, the MDTF-1 team produced the Timeslice Experiments output from the `NCAR CAM5 <https://www.earthsystemgrid.org/dataset/ucar.cgd.ccsm4.NOAA-MDTF.html>`__ and `GFDL AM4 (contact the lead team for password) <http://data1.gfdl.noaa.gov/MDTF/>`__.

      - If you have problems getting another set of data, try changing the files' ``CASENAME`` and variable naming convention. The POD should work by updating ``CASENAME`` and ``convention`` in the configuration input.

      - Try your POD on a different machine. Check that your POD can work with reasonable machine configuration and computation power, e.g., can run on a machine with 32 GB memory, and can finish computation in 10 min. Will memory and run time become a problem if one tries your POD on model output of high spatial resolution and temporal frequency (e.g., avoid memory problem by reading in data in segments)? Does it depend on a particular version of a certain library? Consult the lead team if there's any unsolvable problems.

   B. After you have tested your POD thoroughly, make clean tar files for distribution. Make a tar file of your digested observational data (preserving the ``inputdata/obs_data/`` structure). Do the same for model data used for testing (if different from what is provided by the MDTF page). Upload your POD code to your :doc:`GitHub repo <dev_git_intro>`. The tar files (and your GitHub repo) should not include any extraneous files (backups, ``pyc``, ``*~``, or ``#`` files).

      - Use ``tar -tf`` to see what is in the tar file.

   C. β-test before distribution. Find people (β-testers) who are not involved in your POD's implementation and are willing to help. Give the tar files and point your GitHub repo to them. Ask them to try running the framework with your POD following the Getting Started instructions. Ask for comments on whether they can understand the documentation.

      - Possible β-tester candidates include nearby postdocs/grads and members from other POD-developing groups.

6. Submit your POD code through :doc:`GitHub pull request <dev_git_intro>`, and share the tar files of digested observation (and model data if any) with the lead-team contact. Please also provide a list of tests you've conducted along with the machine configurations (e.g., memory size).
