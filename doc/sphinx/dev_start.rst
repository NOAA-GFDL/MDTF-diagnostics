.. role:: console(code)
   :language: console
   :class: highlight

.. _ref-dev-start:

Developer installation instructions
===================================

To download and install the framework for development, follow the instructions for end users given in
:doc:`start_install`, with the following developer-specific modifications:

Obtaining the source code
^^^^^^^^^^^^^^^^^^^^^^^^^

POD developers should create their branches from the
`main branch <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main>`__ of the framework code

.. code-block:: console

    git checkout -b [POD branch name] main

This is the "beta test" version, used for testing changes before releasing them to end users

Developers may download the code from GitHub as described in :ref:`ref-download`, but we strongly recommend that you
clone the repo in order to keep up with changes in the main branch, and to simplify submitting pull requests with your
POD's code. Instructions for how to do this are given in :doc:`dev_git_intro`.

Installing dependencies with Conda
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Regardless of development language, we strongly recommend that developers use conda to manage their language and
library versions. Note that Conda is not Python-specific, but allows coexisting versioned environments of most
scripting languages, including, `R <https://anaconda.org/conda-forge/r-base>`__,
`NCL <https://anaconda.org/conda-forge/ncl>`__, `Ruby <https://anaconda.org/conda-forge/ruby>`__, etc...


Python-based PODs should be written in Python 3.11 or newer. We provide a developer version of the python3_base environment (described below) that includes Jupyter and other developer-specific tools. This is not installed by default, and must be requested by passing the ``--all`` flag to the conda setup script:

If you are using Anaconda or miniconda to manage the conda environments, run:

.. code-block:: console

    % cd $CODE_ROOT
    % ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR


Installing dependencies with Micromamba
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Micromamba is a lightweight version of Anaconda. It is required to install the base and python3_base conda enviroments
on macOS machines with Apple M-series chips. Installation instructions are available in the
`Micromamba Documentation <https://mamba.readthedocs.io/en/latest/micromamba-installation.html>`__,
Once Micromamba is installed on your system, run the following to install all conda environments if you are NOT using an
Apple M-series machine, where `$MICROMAMBA_ROOT` is the location of the micromamba installation, and
`MICROMAMBA_EXE` is the path to the micromamba executable on your system:

.. code-block:: console

   % cd $CODE_ROOT
   % ./src/conda/micromamba_env_setup.sh --all --conda_root $MICROMAMBA_ROOT --micromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR

If you are using an Apple M-series machine, you can install just the base and python3_base environments:

.. code-block:: console
   % ./src/conda/micromamba_env_setup.sh -e base --micromamba_root $MICROMAMBA_ROOT --mircromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR
   % ./src/conda/micromamba_env_setup.sh -e python3_base --micromamba_root $MICROMAMBA_ROOT --mircromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR

POD development using existing Conda environments
-------------------------------------------------

To prevent the proliferation of dependencies, we suggest that new POD development use existing Conda environments
whenever possible, e.g.,
`python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_python3_base.yml>`__,
`NCL_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_NCL_base.yml>`__,
and `R_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_R_base.yml>`__
for Python, NCL, and R, respectively.

In case you need any exotic third-party libraries, e.g., a storm tracker, consult with the lead team and create
your own Conda environment following :ref:`instructions <ref-create-conda-env>` below.

Python
^^^^^^

The framework provides the
`_MDTF_python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_pythone3_base.yml>`__
Conda environment (recall the ``_MDTF`` prefix for framework-specific environment) as the generic Python environment,
which you can install following the :ref:`instructions <ref-conda-install>`. You can then activate this environment by
running in a terminal:

.. code-block:: console

    % source activate $CONDA_ENV_DIR/_MDTF_python3_base

where ``$CONDA_ENV_DIR`` is the path you used to install the Conda environments. After you've finished working under
this environment, run :console:`% conda deactivate` or simply close the terminal.

Other languages
^^^^^^^^^^^^^^^

The framework also provides the `_MDTF_NCL_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_NCL_base.yml>`__
and `_MDTF_R_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_R_base.yml>`__
Conda environments as the generic NCL and R environments.

.. _ref-create-conda-env:

POD development using a new Conda environment
---------------------------------------------

If your POD requires languages that aren't available in an existing environment or third-party libraries unavailable
through the common `conda-forge <https://conda-forge.org/feedstocks/>`__ and
`anaconda <https://docs.anaconda.com/anaconda/packages/pkg-docs/>`__ channels, we ask that you notify the framework
developers (since this situation may be relevant to other developers) and submit a
`YAML (.yml) file <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually>`__ that creates the environment needed for your POD.

- The new YAML file should be added to ``src/conda/``, where you can find templates for existing environments from
  which you can create your own.

- The YAML filename should be ``env_$your_POD_short_name.yml``.

- The first entry of the YAML file, name of the environment, should be ``_MDTF_$your_POD_short_name``.

- We recommend listing conda-forge as the first channel to search, as it's entirely open source and has the largest
  range of packages. Note that combining packages from different channels (in particular, conda-forge and Anaconda
  channels) may create incompatibilities.

- We recommend constructing the list of packages manually, by simply searching your POD's code for ``import``
  statements referencing third-party libraries. Please do *not* exporting your development environment with
  :console:`% conda env export`, which gives platform-specific version information and will not be fully portable in
  all cases; it also does so for every package in the environment, not just the "top-level" ones you directly requested.

- We recommend specifying versions as little as possible, out of consideration for end-users: if each POD specifies
  exact versions of all its dependencies, conda will need to install multiple versions of the same libraries.
  In general, specifying a version should only be needed in cases where backward compatibility was broken or a bug
  affecting your POD was fixed (e.g., postscript font rendering on Mac OS with older NCL). Conda installs the latest
  version of each package that's consistent with all other dependencies.

Framework interaction with Conda environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As described in :ref:`ref-execute`, when you run the ``mdtf`` executable, among other things,
it reads ``pod_list`` in ``runtime_config.[jsonc | yml]`` and executes POD codes accordingly. For a POD included in the
list (referred to as $POD_NAME):

*  The framework checks for required packages in the POD's ``settings.jsonc`` file in
   ``$CODE_ROOT/diagnostics/$POD_NAME/``. The ``runtime_requirements`` section in ``settings.jsonc``
   specifies the programming language(s) adopted by the POD:

    a). If purely Python 3, the framework will look for ``src/conda/env_python3_base.yml`` and check its content to
    determine whether the POD's requirements are met, and then switch to ``_MDTF_python3_base`` and run the POD.

    b). Similarly, if NCL or R is used, then ``NCL_base`` or ``R_base`` environment will be activated at runtime.

Note that for the 6 existing PODs depending on NCL (EOF_500hPa, MJO_prop_amp, MJO_suite, MJO_teleconnection,
precip_diurnal_cycle, and Wheeler_Kiladis), Python is also used but merely as a wrapper. Thus the framework will
switch to ``_MDTF_NCL_base`` when seeing both NCL and Python in ``settings.jsonc``.

The framework verifies PODs' requirements via looking for the YAML files and their contents. Thus if you choose
to selectively install conda environments using the ``--env`` flag (:ref:`ref-conda-install`), remember to install all
the environments needed for the PODs you're interested in, and that ``_MDTF_base`` is mandatory for the framework's
operation.

For instance, the minimal installation for running the ``EOF_500hPa`` and ``convective_transition_diag PODs``
requres ``_MDTF_base`` (mandatory), ``_MDTF_NCL_base`` (because of b), and ``_MDTF_convective_transition_diag``
(because of 1). These can be installed by passing ``base``, ``NCL_base``, and ``convective_transition_diag``
to the ``--env`` flag one at a time (:ref:`ref-conda-install`).


Testing with a new Conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you've updated an existing environment or created a new environment (with corresponding changes to the YAML file),
verify that your POD works.

Recall how the framework finds a proper Conda environment for a POD. First, it searches for an environment matching
the POD's short name. If this fails, it then looks into the POD's ``settings.jsonc`` and prepares a generic environment
depending on the language(s). Therefore, no additional steps are needed to specify the environment if your new
YAML file follows the naming conventions above (in case of a new environment) or your ``settings.jsonc``
correctly lists the language(s) (in case of updating an existing environment).

- For an updated environment, first, uninstall it by deleting the corresponding directory under ``$CONDA_ENV_DIR``.

- Re-install the environment using the ``conda_env_setup.sh`` script as described in the
  :ref:`installation instructions <ref-conda-install>`, or create the new environment for you POD:

    .. code-block:: console

        % cd $CODE_ROOT
        % ./src/conda/conda_env_setup.sh --env $your_POD_short_name --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR

    Or, if using micromamba:

    .. code-block:: console

        % cd $CODE_ROOT
        % ./src/conda/conda_env_setup.sh --env $your_POD_short_name --micromamba_root $MICROMAMBA_ROOT --env_dir $CONDA_ENV_DIR

Have the framework run your POD on suitable test data.

    1. Add your POD's short name to the ``pod_list`` section of the configuration input file
       (template: ``templates/runtime_config.[jsonc | yml]``).

    2. Prepare the test data as described in :doc:`start_config`.
