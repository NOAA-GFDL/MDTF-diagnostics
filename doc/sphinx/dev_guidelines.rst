POD development instructions
============================

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
------------------------------------------------------------

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
------------------------------

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