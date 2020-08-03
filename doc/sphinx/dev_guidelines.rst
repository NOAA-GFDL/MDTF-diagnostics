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

Other tips on implementation:
-----------------------------

#. Structure of the code package: Implementing the constituent PODs in accordance with the structure described in earlier sections makes it easy to pass the package (or just part of it) to other groups.

#. Robustness to model file/variable names: Each POD should be robust to modest changes in the file/variable names of the model output; see :doc:`Getting Started <start_config>` regarding the model data filename structure, :ref:`ref-example-env-vars` and :ref:`ref-Checklist` regarding using the environment variables and robustness tests. Also, it would be easier to apply the code package to a broader range of model output.

#. Save digested data after analysis: Can be used, e.g., to save time when there is a substantial computation that can be re-used when re-running or re-plotting diagnostics. See :ref:`ref-output-cleanup` regarding where to save the output.

#. Self-documenting: For maintenance and adaptation, to provide references on the scientific underpinnings, and for the code package to work out of the box without support. See :ref:`ref-Checklist`.

#. Handle large model data: The spatial resolution and temporal frequency of climate model output have increased in recent years. As such, developers should take into account the size of model data compared with the available memory. For instance, the example POD precip_diurnal_cycle and Wheeler_Kiladis only analyze part of the available model output for a period specified by the environment variables ``FIRSTYR`` and ``LASTYR``, and the convective_transition_diag module reads in data in segments.

#. Basic vs. advanced diagnostics (within a POD): Separate parts of diagnostics, e.g, those might need adjustment when model performance out of obs range.

#. Avoid special characters (``!@#$%^&*``) in file/script names.


See :ref:`ref-execute` and :doc:` framework operation walkthrough <dev_walkthrough>` for details on how the package is called. See the :doc:`command line reference <ref_cli>` for documentation on command line options (or run ``mdtf --help``).

Avoid making assumptions about the machine on which the framework will run beyond what’s listed here; a development priority is to interface the framework with cluster and cloud job schedulers to enable individual PODs to run in a concurrent, distributed manner.

