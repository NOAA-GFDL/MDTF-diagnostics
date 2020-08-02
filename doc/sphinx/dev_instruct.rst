Language choice and managing library dependencies
=================================================

In this section, we discuss restrictions on coding languages and how to manage library dependencies. These are important points to be aware of when developing your POD, and may require you to modify existing code.

You **must** manage your POD's language/library dependencies through `Conda <https://docs.conda.io/en/latest/>`__, since the dependencies of the framework are so managed by design, and this is also how the end-users are instructed to set up and manage their own environments for the framework. Note that Conda is not Python-specific, but allows coexisting versioned environments of most scripting languages, including, `R <https://anaconda.org/conda-forge/r-base>`__, `NCL <https://anaconda.org/conda-forge/ncl>`__, `Ruby <https://anaconda.org/conda-forge/ruby>`__, `PyFerret <https://anaconda.org/conda-forge/pyferret>`__, and more.

To prevent the proliferation of dependencies, we suggest that new POD development use existing Conda environments whenever possible, e.g., `python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_python3_base.yml>`__, `NCL_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_NCL_base.yml>`__, and `R_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_R_base.yml>`__ for Python, NCL, and R, respectively.

Choice of language(s)
---------------------

The framework itself is written in Python, and can call PODs written in any scripting language. However, Python support by the lead team will be “first among equals” in terms of priority for allocating developer resources, etc.

- To achieve portability, the MDTF **cannot** accept PODs written in closed-source languages (e.g., MATLAB and IDL; try `Octave <https://www.gnu.org/software/octave/>`__ and `GDL <https://github.com/gnudatalanguage/gdl>`__ if possible). We also **cannot** accept PODs written in compiled languages (e.g., C or Fortran): installation would rapidly become impractical if users had to check compilation options for each POD.

- Python is strongly encouraged for new PODs; PODs funded through the CPO grant are requested to be developed in Python. Python version >= 3.6 is required (official support for Python 2 was discontinued as of January 2020).

- If your POD was previously developed in NCL or R (and development is *not* funded through a CPO grant), you do not need to re-write existing scripts in Python 3 if doing so is likely to introduce new bugs into stable code, especially if you’re unfamiliar with Python.

- If scripts were written in closed-source languages, translation to Python 3.6 or above is required.

POD development using exiting Conda environment
-----------------------------------------------

We assume that you've followed the :ref:`instructions <ref-install>` in the Getting Started to set up the Conda environments for the framework. We recommend developing POD and managing POD's dependencies following the same approach.

Developers working with Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework provides the `_MDTF_python3_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_pythone3_base.yml>`__ Conda environment (recall the ``_MDTF`` prefix for framework-specific environment) as the generic Python environment, which you can install following the :ref:`instructions <ref-install>`. You can then activate this environment by running in a terminal:

::

% source activate $CONDA_ENV_DIR/_MDTF_python3_base

where ``$CONDA_ENV_DIR`` is the path you used to install the Conda environments.

- For developers' convenience, `JupyterLab <https://jupyterlab.readthedocs.io/en/stable/>`__ (including `Jupyter Notebook <https://jupyter-notebook.readthedocs.io/en/stable/>`__) has been included in python3_base. Run ``% jupyter lab`` or ``% jupyter notebook``, and you can start working on development.

- If there are any `commonly used Python libraries <https://conda-forge.org/feedstocks/>`__ that you'd like to add to python3_base, e.g., ``jupyterlab``, run ``% conda install -c conda-forge jupyterlab``.

   a. Only add libraries when necessary. We'd like to keep the environment small.

   b. Include the ``-c`` flag and specify using the `conda-forge <https://anaconda.org/conda-forge>`__ channel as the library source. Combining packages from different channels (in particular, conda-forge and anaconda's channel) may create incompatibilities. Consult with the lead team if encounter any problem.

   c. After installation, run ``% conda clean --a`` to clear cache.

   d. *DO NOT* forget to update ``src/conda/env_python3_base.yml`` accordingly.

After you've finished working under this environment, run ``% conda deactivate`` or simply close the terminal.

In case you need any exotic third-party libraries, e.g., a storm tracker, consult with the lead team and create your own Conda environment following :ref:`instructions <ref-create-conda-env>` below.

Developers working with NCL or R
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework also provides the `_MDTF_NCL_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_NCL_base.yml>`__ and `_MDTF_R_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/develop/src/conda/env_R_base.yml>`__ Conda environments as the generic NCL and R environments. You can install, activate/deactivate or add common NCL-/R-related libraries (or ``jupyterlab``) to them using commands similar to those listed above.

.. _ref-create-conda-env:

Create a new Conda environment
------------------------------

If your POD requires languages that aren't available in an existing environment or third-party libraries unavailable through the common `conda-forge <https://conda-forge.org/feedstocks/>`__ and `anaconda <https://docs.anaconda.com/anaconda/packages/pkg-docs/>`__ channels, we ask that you notify us (since this situation may be relevant to other developers) and submit a `YAML (.yml) file <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually>`__ that creates the environment needed for your POD.

- The new YAML file should be added to ``src/conda/``, where you can find templates for existing environments from which you can create your own.

- The YAML filename should be ``env_$your_POD_short_name.yml``.

- The first entry of the YAML file, name of the environment, should be ``_MDTF_$your_POD_short_name``.

- We recommend listing conda-forge as the first channel to search, as it's entirely open source and has the largest range of packages. Note that combining packages from different channels (in particular, conda-forge and anaconda channels) may create incompatibilities.

- We recommend constructing the list of packages manually, by simply searching your POD's code for ``import`` statements referencing third-party libraries. Please do *not* exporting your development environment with ``% conda env export``, which gives platform-specific version information and will not be fully portable in all cases; it also does so for every package in the environment, not just the "top-level" ones you directly requested.

- We recommend specifying versions as little as possible, out of consideration for end-users: if each POD specifies exact versions of all its dependencies, conda will need to install multiple versions of the same libraries. In general, specifying a version should only be needed in cases where backward compatibility was broken (e.g., Python 2 vs. 3) or a bug affecting your POD was fixed (e.g., postscript font rendering on Mac OS with older NCL). Conda installs the latest version of each package that's consistent with all other dependencies.

Testing with new Conda environment
----------------------------------

If you've updated an existing environment or created a new environment (with corresponding changes to the YAML file), verify that your POD works.

Recall :ref:`how <ref-interaction-conda-env>` the framework finds a proper Conda environment for a POD. First, it searches for an environment matching the POD's short name. If this fails, it then looks into the POD's ``settings.jsonc`` and prepares a generic environment depending on the language(s). Therefore, no additional steps are needed to specify the environment if your new YAML file follows the naming conventions above (in case of a new environment) or your ``settings.jsonc`` correctly lists the language(s) (in case of updating an existing environment).

- For an updated environment, first, uninstall it by deleting the corresponding directory under ``$CONDA_ENV_DIR``.

- Re-install the environment using the ``conda_env_setup.sh`` script as described in the :ref:`installation instructions <ref-conda-env-install>`, or create the new environment for you POD:

   ::

   % cd $CODE_ROOT
   % ./src/conda/conda_env_setup.sh --env $your_POD_short_name --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR

- Have the framework run your POD on suitable test data.

   1. Add your POD's short name to the ``pod_list`` section of the configuration input file (template: ``src/default_tests.jsonc``).

   2. Prepare the test data as described in :doc:`start_config`.
