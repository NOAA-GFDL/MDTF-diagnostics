Quickstart installation instructions
====================================

This document provides basic directions for downloading, installing and running a test of the Model Diagnostics Task Force (MDTF) Process-Oriented Diagnostics package using sample model data. The current MDTF package has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

You will need to download a) the source code, b) digested observational data, and c) two sets of sample model data (Section 1). Afterwards, we describe how to install necessary Conda environments and languages (Section 2) and run the framework on the default test case (Section 3). Consult the `documentation site <https://mdtf-diagnostics.readthedocs.io/en/latest/>`__ for how to run the framework on your own data and configure general settings.

Download the package code and sample data for testing
-----------------------------------------------------

Throughout this document, ``%`` indicates the UNIX/LINUX command line prompt and is followed by commands to be executed in a terminal in ``fixed-width font``, and ``$`` indicates strings to be substituted, e.g., the string ``$CODE_ROOT`` in :numref:`test-ref` should be substituted by the actual path to the MDTF-diagnostics directory. 

.. _test-ref:

Obtaining the code
^^^^^^^^^^^^^^^^^^

The official repo for the MDTF code is hosted at the GFDL `GitHub account <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. We recommend that end users download and test the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1>`__. 

To install the MDTF package on a local machine, create a directory named ``mdtf``, and unzip the code downloaded from the `release page <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1>`__ there. This will create a directory titled ``MDTF-diagnostics-3.0-beta.1`` containing the files listed on the GitHub page. Below we refer to this MDTF-diagnostics directory as ``$CODE_ROOT``. It contains the following subdirectories:

- ``diagnostics/``: directories containing source code of individual PODs.
- ``doc/``: directory containing documentation (a local mirror of the documentation site).
- ``src/``: source code of the framework itself.
- ``tests/``: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the ``master`` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.  

For POD developers, the ``develop`` branch is the “beta test” version of the framework. POD developers should begin work on this branch as described in the Developer’s’ Walkthrough.

.. _ref-supporting-data:

Obtaining supporting data
^^^^^^^^^^^^^^^^^^^^^^^^^

Supporting observational data and sample model data are available via anonymous FTP at ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is provided for default test/demonstration purposes. The files most relevant for package installation and default tests are:

- Digested observational data (159 Mb): `MDTF_v2.1.a.20200410.obs_data.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.20200410.obs_data.tar>`__.
- NCAR-CESM-CAM sample data (12.3 Gb): `model.QBOi.EXP1.AMIP.001.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar>`__.
- NOAA-GFDL-CM4 sample data (4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.

Users installing on Mac OS should use the Finder’s Archive Utility instead of the command-line tar command to extract the files. Download these three files and extract the contents in the following hierarchy under the ``mdtf`` directory:

- ``mdtf/inputdata/obs_data/...``
- ``mdtf/inputdata/model/QBOi.EXP1.AMIP.001/...``
- ``mdtf/inputdata/model/GFDL.CM4.c96L32.am4g10r8/...``

The default test case uses the QBOi.EXP1.AMIP.001 sample. The GFDL.CM4.c96L32.am4g10r8 sample is only for testing the MJO Propagation and Amplitude POD. Note that ``mdtf`` now contains both ``MDTF-diagnostics`` and ``inputdata`` directories. 

Install the necessary programming languages and modules
-------------------------------------------------------

The MDTF framework code is written in Python 2.7, but supports running PODs written in a variety of scripting languages and combinations of libraries. To handle this, the framework provides an automated script for setting up and maintaining the necessary environments through the `Conda package manager <https://docs.conda.io/en/latest/). Conda is a free, open source software which is one component of the `Anaconda <https://www.anaconda.com/) python distribution. Note that the framework only makes use of Conda, thus having Anaconda is sufficient but not necessary. For maximum portability and ease of installation, we recommend that all users manage these necessary languages and libraries through this script, even if they have independent installations of these languages on their machine.

Conda installation
^^^^^^^^^^^^^^^^^^

The framework’s environments can co-exist within an existing Conda or Anaconda installation. Run ``% conda --version`` as the user who will be using the framework to determine if Conda is installed; the framework has been tested against versions of Conda >= 4.7.5.

Do not install miniconda/Anaconda again if Conda is already installed for this user: the installer will break the existing installation (if it's not managed with, eg., environment modules.)

If you do not have a pre-existing Conda installation on your system, we recommend using the miniconda2 (python 2.7) installer available `here <https://docs.conda.io/en/latest/miniconda.html>`__, but any version of miniconda or Anaconda released after June 2019 will work. Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda2 by running conda init?” prompt. This will allow the installer to add the Conda path to the user's shell login script (e.g., ``~/.bashrc`` or ``~/.cshrc``). 

Conda environment installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``% $CODE_ROOT/src/conda/conda_init.sh -v`` to see where the install script will put the Conda environments by default. 

- If the script returns an error or finds the wrong Conda executable (eg. you want to use a local installation of Conda instead of a site-wide installation), the correct location can be passed to the install script as ``$CONDA_ROOT`` below. ``$CONDA_ROOT`` should be the base directory containing the Conda installation you want to use (returned by ``% conda info --base``).
- By default, Conda will install program files in the "active env location" listed by ``% conda info``. To use a different location (for space reasons, or if you don't have write access), pass the desired directory as ``$CONDA_ENV_DIR`` below.

Once the correct paths have been determined, all Conda environments used by the framework can be installed by running ``% $CODE_ROOT/src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR``. The last two flags only need to be included if you want to override the default values, as described above.

 The installation may take ~10min and requires ~4.5 Gb for the default case. After installing the framework-specific Conda environments, one should not manually alter them (i.e., never run ``conda update`` on them). The names of all framework-created environments begin with “_MDTF”, so as not to conflict with any other environments that are defined. 

Non-Conda installation
^^^^^^^^^^^^^^^^^^^^^^

If you're unable to use the Conda-based installation, the framework can use existing dependencies installed without using Conda. Because this mode of operation is dependent on the details of each user’s system, we don't recommend it and can only support it at a secondary priority. The following software is used by the framework and needs to be available on your ``$PATH``:

- `Python <https://www.python.org/>`__ version 2.7: the framework will attempt to create virtualenvs for each POD.
- `NCO utilities <http://nco.sourceforge.net/>`__ version 4.7.6.
- `ImageMagick <https://imagemagick.org/index.php>`__.
- `NCL <https://www.ncl.ucar.edu/>`__, version 6.5.0 or newer.
- `R <https://www.r-project.org/>`__, for the SM_ET_coupling POD only.


Execute the MDTF package with default test settings
---------------------------------------------------

Location of the MDTF executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Following section 2.2, the installation script will have created an executable at ``$CODE_ROOT/mdtf`` which sets the correct Conda environment before running the framework. To test the installation, ``% $CODE_ROOT/mdtf --help`` will print help on the command-line options. Note that, if your current working directory is ``$CODE_ROOT``, you will need to run ``% ./mdtf --help``.

Run the framework on sample data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the framework on the first test case, execute

::

% cd $CODE_ROOT
% ./mdtf --OUTPUT_DIR $OUTPUT_DIR src/default_tests.jsonc


``$OUTPUT_DIR`` should be a directory you want the results to be written to. The output files for this test case will be written to ``$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981``. 

Run time may be 20 minutes or more, depending on your system. When the framework is finished, open ``file://$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html`` in a web browser to view the output report.

The settings for default test cases are included in ``$CODE_ROOT/src/default_tests.jsonc``. Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the entry for QBOi.EXP1.AMIP.001 in the "caselist" section of that file.

Next steps
----------

Consult the `documentation site <https://mdtf-diagnostics.readthedocs.io/en/latest/>`__ for how to run the framework on your own data and configure general settings.