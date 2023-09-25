.. role:: console(code)
   :language: console
   :class: highlight

Runtime configuration
=====================

This section details how to configure the way the package runs the PODs: how to direct the code of each POD to the libraries and other software it needs, and how to control how that code gets executed. The main command-line option for this functionality is the ``--environment-manager`` flag, which selects an ":ref:`environment manager<ref-runtime-mgrs-environments>`": a code plug-in that implements the functionality of managing the script interpreters, third-party libraries, and any other executables needed by each POD. The plug-in may define its own specific command-line options, which are documented here. 

In the future, we plan to offer analogous functionality that gives the user control over how PODs are executed through a similar ``--runtime-manager`` flag.

If you're using site-specific functionality (via the ``--site`` flag), additional options may be available beyond what is listed here. See the :doc:`site-specific documentation <site_toc>` for your site.

.. _ref-runtime-mgrs-environments:

Environment managers
--------------------

.. note::
   The values used for this option and its settings must be compatible with how the package was set up during :doc:`installation<start_install>`. Missing code dependencies are not installed at runtime; instead any POD with missing dependencies raises an error and is not run.

Conda-based environment manager
+++++++++++++++++++++++++++++++

Selected via ``--environment-manager="Conda"``. This is the default value for <*environment-manager*>.

This option should always be used if the package was installed according to the :ref:`standard instructions<ref-conda-install>`. This environment manager uses `conda <https://docs.conda.io/en/latest/>`__, a multi-language, open-source package manager. Conda is one component of the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ and `Anaconda <https://www.anaconda.com/>`__ python distributions, so having Miniconda/Anaconda is sufficient but not necessary. It is the recommended and best-supported means of installing the package's dependencies.

**Command-line options**

The following command-line options should be set to the same values used when :ref:`installing the conda environments<ref-conda-install>`:

--conda-root <CONDA_ROOT>    Path to the conda installation. This should always be set to the path specified by the ``--conda_root`` flag when the ``conda_env_setup.sh`` was run as part of the :ref:`installation process<ref-conda-install>`. Omit or set to ``""`` to use the conda that's been configured for the current user (run :console:`% conda info` to determine its location.)
--conda-env-root <CONDA_ENV_DIR>    Optional. Root directory where the conda environments used by the PODs have been installed. This should always be set to the path specified by the ``--env_dir`` flag when the ``conda_env_setup.sh`` was run as part of the :ref:`installation process<ref-conda-install>`. If that setting was not used, this flag should be omitted or set to ``""`` (which sets this directory to the user's conda's default location).

Virtualenv-based environment manager
++++++++++++++++++++++++++++++++++++

Selected via ``--environment-manager="Virtualenv"``.

This option should only be used if installation was done via the alternative instructions at :doc:`start_nonconda`. This option is provided for users who wish to use the python, NCL, R, etc. executables already present on their system instead of maintaining a conda installation. 

**Command-line options**

--venv-root <DIR>   Root directory to use for installing python virtual environments. Set equal to ``""`` to install in the default location for your system's python.
--r-lib-root <DIR>    Root directory to use for installing R packages requested by PODs. Set equal to ``""`` to install in your system's R package library.

.. _ref-runtime-mgrs-runtimes:

Runtime managers
----------------

The runtime manager is responsible for beginning the execution of each POD's code, and for returning control back to the framework when the PODs have finished running or raised an error.
Two runtime managers are implemented: `single_run` (default) or `multi_run`. The framework determines the runtime
manager based on the `data_type` option specified at runtime. Both runtime managers launch PODs via the subprocess
manager.

The `single_run` implementation passes information from a `case` structure to several PODs that analyze a single model
dataset, and an observational dataset if required. The `multi_run` implementation passes information from a `POD` structure to a single
POD that analyzes data from multiple model and/or observational datasets. Users can run more than one multi_run POD in a
single ``./mdtf`` call. At this time, the framework does not support running a mix of `single_run` and `multi_run` PODs at
once. If you would like the package to support a method of running PODs that hasn't currently been implemented,
please make a request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/176>`__.

Local subprocess runtime manager
++++++++++++++++++++++++++++++++

Currently, we've only implemented the functionality to run PODs as parallel subprocesses on the local machine (i.e., the same machine from which the framework was started). After the model data is obtained and it's verified that each diagnostic has the code dependencies needed to run, the package spawns a separate POSIX subprocess for each POD, which execute in parallel: management of CPU and memory is left to the local machine's OS.

After the subprocesses are spawned, further execution of the framework (processing the PODs' output) is blocked until all subprocesses exit, either successfully or unsuccessfully. All console output from each subprocess is captured to the log file for the corresponding POD.

Since this is the only option available, it's always selected, and there's no way to change it with the CLI.

**Command-line options**

There are no command-line options associated with this functionality.
