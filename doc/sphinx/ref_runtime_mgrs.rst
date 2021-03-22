Runtime configuration reference
===============================

This section details how to configure the way the package runs the PODs: how to direct the code of each POD to the libraries and other software it needs, and how to control how that code gets executed. The main command-line option for this functionality is the ``--environment-manager`` flag, which selects a ":ref:`data source<ref-runtime-mgrs-environments>`": a code plug-in that implements the functionality of managing the script interpreters, third-party libraries, and any other executables needed by each POD. The plug-in may define its own specific command-line options, which are documented here. 

In the future, we plan to offer analogous functionality that gives the user control over how PODs are executed through a similar ``--runtime-manager`` flag.

If you're using site-specific functionality (``--site`` flag), additional options may be available beyond what is listed here. See the :doc:`site-specific documentation <site_toc>` for your site.

.. _ref-runtime-mgrs-environments:

Environment managers
--------------------

.. note::
   The values used for this option and its settings must be compatible with how the package was set up during :doc:`installation<start_install>`. Missing code dependencies are not installed at runtime; instead any POD with missing dependencies is not run, and an error is logged.

Conda-based environment manager
+++++++++++++++++++++++++++++++

Selected via ``--environment-manager="Conda"``. This is the default value for <*environment-manager*>.

This option should always be used if the package was installed according to the :ref:`standard instructions<ref-conda-install>`. This environment manager uses `Conda <https://docs.conda.io/en/latest/>`__, a multi-language, open-source package manager. Conda is one component of the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ and `Anaconda <https://www.anaconda.com/>`__ python distributions, so having Miniconda/Anaconda is sufficient but not necessary. It is the recommended and best-supported means of installing the package's dependencies.

**Command-line options**

The following command-line options should be set to the same values used when :ref:`installing the conda environments<ref-conda-env-install>`:

* ``--conda-root`` <*DIR*>: Path to the Conda installation. Set equal to ``""`` to use the conda that's been configured to .
* ``--conda-env-root`` <*DIR*>: Optional. Root directory where the conda environments used by the PODs have been installed. Omit or set equal to ``""`` if this flag was not used during the installation process (which installs the environments in the system's default location).

Virtualenv-based environment manager
++++++++++++++++++++++++++++++++++++

Selected via ``--environment-manager="Virtualenv"``.

This option should only be used if installation was done via the alternative instructions at :doc:`start_nonconda`. This option is provided for users who wish to use the python, NCL, R, etc. executables already present on their system instead of  maintaining a conda installation. 

**Command-line options**

* ``--venv-root`` <*DIR*>: Root directory to use for installing python virtual environments. Set equal to ``""`` to install in your system's default location.
* ``--r-lib-root`` <*DIR*>: Root directory to use for installing R packages requested by PODs. Set equal to ``""`` to install in your system's R package library.

.. _ref-runtime-mgrs-runtimes:

Runtime managers
----------------

The runtime manager is responsible for beginning the execution of each POD's code, and for returning control back to the framework when the PODs have finished running or raised an error. Because only one value for this option has currently been implemented, we don't provide a command-line option to change it.

There are currently two data sources implemented in the package, described below. If you would like the package to support obtaining data from a source that hasn't currently been implemented, please make a request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/176>`__.

Local subprocess runtime manager
++++++++++++++++++++++++++++++++

Currently, we've only implemented the functionality to run PODs as parallel subprocesses on the local machine (i.e., the same machine from which the framework was started). After the model data is obtained and it's verified that each diagnostic has the code dependencies needed to run, the package spawns a separate subprocess for each POD, which execute in parallel: management of CPU and memory is left to the local machine's OS.

After the subprocesses are spawned, further execution of the package (processing the PODs' output) is blocked until all subprocesses exit, either successfully or unsuccessfully. All console output from each subprocess is captured to the log file for the corresponding POD.

Since this is the only option available, it's always selected, and there's no way to change it with the CLI.

**Command-line options**

There are no command-line options associated with this functionality.
