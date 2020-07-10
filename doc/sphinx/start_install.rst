Quickstart installation instructions
====================================

This document provides basic directions for downloading, installing and running a test of the Model Diagnostics Task Force (MDTF) Process-Oriented Diagnostics package using sample model data. The current MDTF package has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

You will need to download a) the source code, b) digested observational data, and c) two sets of sample model data (:numref:`ref-download`). Afterwards, we describe how to install necessary Conda environments and languages (:numref:`ref-install`) and run the framework on the default test case (:numref:`ref-execute`). 

.. _ref-download:

Download the package code and sample data for testing
-----------------------------------------------------

Throughout this document, ``%`` indicates the UNIX/LINUX command line prompt and is followed by commands to be executed in a terminal in ``fixed-width font``, and ``$`` indicates strings to be substituted, e.g., the string ``$CODE_ROOT`` below should be substituted by the actual path to the MDTF-diagnostics directory. 

Obtaining the code
^^^^^^^^^^^^^^^^^^

The official repo for the MDTF code is hosted at the GFDL `GitHub account <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. We recommend that end users download and test the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1>`__. 

To install the MDTF package on a local machine, create a directory named ``mdtf``, and unzip the code downloaded from the `release page <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1>`__ there. This will create a directory titled ``MDTF-diagnostics-3.0-beta.1`` containing the files listed on the GitHub page. Below we refer to this MDTF-diagnostics directory as ``$CODE_ROOT``. It contains the following subdirectories:

- ``diagnostics/``: directories containing source code of individual PODs.
- ``doc/``: directory containing documentation (a local mirror of the documentation site).
- ``src/``: source code of the framework itself.
- ``tests/``: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the ``main`` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.  

For POD developers, the ``develop`` branch is the “beta test” version of the framework. POD developers should begin work on this branch as described in :ref:`ref-dev-git`.

.. _ref-supporting-data:

Obtaining supporting data
^^^^^^^^^^^^^^^^^^^^^^^^^

Supporting observational data and sample model data are available via anonymous FTP at ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is provided for default test/demonstration purposes. The files needed for package installation and default tests are:

- Digested observational data (159 Mb): `MDTF_v2.1.a.20200410.obs_data.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.20200410.obs_data.tar>`__.
- NCAR-CESM-CAM sample data (12.3 Gb): `model.QBOi.EXP1.AMIP.001.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar>`__.
- NOAA-GFDL-CM4 sample data (4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.

Users installing on Mac OS should use the Finder’s Archive Utility instead of the command-line tar command to extract the files. Download these three files and extract the contents in the following hierarchy under the ``mdtf`` directory:

- ``mdtf/inputdata/obs_data/...``
- ``mdtf/inputdata/model/QBOi.EXP1.AMIP.001/...``
- ``mdtf/inputdata/model/GFDL.CM4.c96L32.am4g10r8/...``

The default test case uses the QBOi.EXP1.AMIP.001 sample. The GFDL.CM4.c96L32.am4g10r8 sample is only for testing the MJO Propagation and Amplitude POD. Note that ``mdtf`` now contains both ``MDTF-diagnostics`` and ``inputdata`` directories. 

.. _ref-install:

Install the necessary programming languages and modules
-------------------------------------------------------

The MDTF framework code is written in Python 2.7, but supports running PODs written in a variety of scripting languages and combinations of libraries. We use `conda <https://docs.conda.io/en/latest/>`__, a free, open-source package manager to install and manage these dependencies. Conda is one component of the `Anaconda <https://www.anaconda.com/>`__ python distribution, so having Anaconda is sufficient but not necessary. 

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda using the provided script, even if they have independent installations of the required languages. A complete installation of all dependencies will take roughly 5 Gb, less if you've already installed some of the dependencies through conda. The location of this installation can be changed with the ``$CONDA_ENV_DIR`` setting described below. 

If these space requirements are prohibitive, we provide an alternate method of operation which makes no use of conda and relies on the user to install external dependencies, at the expense of portability. This is documented in a :doc:`separate section <start_nonconda>`.

Conda installation
^^^^^^^^^^^^^^^^^^

The framework’s environments will co-exist with an existing Anaconda or miniconda installation. *Do not* reinstall miniconda/Anaconda if it's already installed for the user who will be running the framework: the installer will break the existing installation (if it's not managed with, eg., environment modules.)

To determine if conda is installed, run ``% conda --version`` as the user who will be using the framework. The framework has been tested against versions of conda >= 4.7.5. 

If you do not have a pre-existing Anaconda or miniconda installation on your system, we recommend using the miniconda2 (python 2.7) installer available `here <https://docs.conda.io/en/latest/miniconda.html>`__. Any version of miniconda/Anaconda (2 or 3) released after June 2019 will work: the only differences are the modules that are pre-installed by default. Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda2 by running conda init?” prompt. This will allow the installer to add the conda path to the user's shell login script (e.g., ``~/.bashrc`` or ``~/.cshrc``). 

.. _ref-conda-env-install:

Conda environment installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``% conda info --base`` as the user who will be using the framework to determine the location of your conda installation. This path will be referred to as ``$CONDA_ROOT`` below. After determining this path, run

::

% cd $CODE_ROOT
% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT

to install all needed environments. This takes ~10 min. The names of all framework-created environments begin with “_MDTF”, so as not to conflict with any other environments that are defined. 

By default, Conda will install program files within ``$CONDA_ROOT`` (the "active env location" listed by ``% conda info``). To use a different location (for space reasons, or if you don't have write access), pass the desired directory as ``$CONDA_ENV_DIR`` below:

:: 

% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR

After installing the framework-specific conda environments, you shouldn't manually alter them (i.e., never run ``conda update`` on them). To update the environments after updating the framework code, re-run the above commands.

.. _ref-configure:

Configure package paths
-----------------------

Open ``src/default_tests.jsonc`` in an editor (we recommend working on a copy). This is a template/example of an input file you can use to define configuration options instead of re-typing them on the command line every time you run the framework.

- If you've installed the supporting data in the directory structure described in :ref:`ref-supporting-data`, the existing values for ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` will be correct. If you put the data in a different location, these values should be changed accordingly.
- ``OUTPUT_DIR`` should be set to the location you want the output files to be written to. The output of each run of the framework will be saved in a different subdirectory in this location.
- ``conda_root`` should be set to the value of ``$CONDA_ROOT`` you used above.
- If you specified a custom environment location with ``$CONDA_ENV_DIR``, set ``conda_env_root`` to that value; otherwise, leave it blank.

.. _ref-execute:

Run the MDTF package with test settings
---------------------------------------

Location of the MDTF executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Following :ref:`ref-conda-env-install`, the setup script will have created an executable at ``$CODE_ROOT/mdtf`` which sets the correct conda environment before running the framework. To test the installation, run

::

% cd $CODE_ROOT
% ./mdtf --help

This should print help text on the command-line options.

Run the framework on sample data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the framework on the CESM sample model data, run

::

% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc

If you edited a copy of ``default_tests.jsonc``, pass that file instead. Run time may be 10-20 minutes, depending on your system. 

The output files for this test case will be written to ``$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981``. When the framework is finished, open ``file://$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html`` in a web browser to view the output report.

Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the entry for QBOi.EXP1.AMIP.001 in the "caselist" section of the input file.

Next steps
----------

Consult the :doc:`following section <start_config>` for how to run the framework on your own data and configure general settings.
