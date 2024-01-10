.. role:: console(code)
   :language: console
   :class: highlight

Installation instructions
=========================

This section provides basic directions for downloading, installing and running a test of the
Model Diagnostics Task Force (MDTF) package using sample model data. The package has been tested on Linux,
Mac OS, and the Windows Subsystem for Linux.

You will need to download the source code, digested observational data, and sample model data (:numref:`ref-download`).
Afterwards, we describe how to install software dependencies using the `conda <https://docs.conda.io/en/latest/>`__
package manager (:numref:`ref-conda-install`) or `micromamba <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>`__ (:numref:`ref-micromamba-install`) and run the framework on sample model data (:numref:`ref-configure` and
:numref:`ref-execute`).

Throughout this document, :console:`%` indicates the shell prompt and is followed by commands to be executed in a
terminal in ``fixed-width font``. Variable values are denoted by angle brackets, e.g. <*HOME*> is the path to your
home directory returned by running :console:`% echo $HOME`.

.. _ref-download:

Obtaining the code
------------------

The official repo for the package's code is hosted at the NOAA-GFDL
`GitHub account <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__.
To simplify updating the code, we recommend that all users obtain the code using git.
For more in-depth instructions on how to use git, see :doc:`dev_git_intro`.

To install the MDTF package on a local machine, open a terminal and create a directory named `mdtf`.
Instructions for end-users and new developers are then as follows:

- For end users:
  
  1. | :console:`% cd mdtf`, then clone your fork of the MDTF repo on your machine:
     | :console:`% git clone https://github.com/<your GitHub account name>/MDTF-diagnostics`.
  2. Verify that you are on the main branch: :console:`% git branch`.
  3. | Check out the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0>`__:
     | :console:`% git checkout tags/v3.0`.
  4. Proceed with the installation process described below.
  5. | Check out a new branch that will contain your edited config files: 
     | :console:`% git checkout -b <branch name>`.
  6. | Update the config files, then commit the changes: 
     | :console:`% git commit -m \"description of your changes\"`.
  7. | Push the changes on your branch to your remote fork: 
     | :console:`% git push -u origin <branch name>`.
   
- For new POD developers:
  
  1. | :console:`% cd mdtf`, then clone your fork of the MDTF repo on your machine:
     | :console:`% git clone https://github.com/<your GitHub account name>/MDTF-diagnostics`.
  2. Check out the ``main`` branch: :console:`% git checkout main`.
  3. Proceed with the installation process described below.
  4. | Check out a new branch for your POD: 
     | :console:`% git checkout -b <POD branch name>`.
  5. | Edit existing files/create new files, then commit the changes:
     | :console:`% git commit -m \"description of your changes\"`.
  6. | Push the changes on your branch to your remote fork:
     | :console:`% git push -u origin <POD branch name>`.

The path to the code directory (``.../mdtf/MDTF-diagnostics``) is referred to as <*CODE_ROOT*>.
It contains the following subdirectories:

- ``diagnostics/``: directory containing source code and documentation of individual PODs.
- ``doc/``: source code for the documentation website.
- ``shared/``: shared code and resources for use by both the framework and PODs.
- ``sites/``: site-specific code and configuration files.
- ``src/``: source code of the framework itself.
- ``tests/``: general tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback,
the ``main`` branch of the GitHub repo contains features that haven’t yet been incorporated into an official release,
which are less stable or thoroughly tested.

.. _ref-supporting-data:

Obtaining supporting data
-------------------------

Supporting observational data and sample model data are available via anonymous FTP from ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is optional and only needed for test and demonstration purposes. The files you will need to download are:

- Digested observational data (159 Mb): `MDTF_v2.1.a.obs_data.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar>`__.
- NCAR-CESM-CAM sample data (12.3 Gb): `model.QBOi.EXP1.AMIP.001.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar>`__.
- NOAA-GFDL-CM4 sample data (4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.

The default test case uses the ``QBOi.EXP1.AMIP.001`` sample dataset, and the ``GFDL.CM4.c96L32.am4g10r8`` sample
dataset is only for testing the `MJO Propagation and Amplitude POD <../sphinx_pods/MJO_prop_amp.html>`__.
Note that the above paths are symlinks to the most recent versions of the data, and will be reported as having
a size of zero bytes in an FTP client.

Download these files and extract the contents in the following directory hierarchy under the ``mdtf`` directory:

::

   mdtf
   ├── MDTF-diagnostics ( = <CODE_ROOT>)
   ├── inputdata
   │   ├── model ( = <MODEL_DATA_ROOT>)
   │   │   ├── GFDL.CM4.c96L32.am4g10r8
   │   │   │   └── day
   │   │   │       ├── GFDL.CM4.c96L32.am4g10r8.precip.day.nc
   │   │   │       └── (... other .nc files )
   │   │   └── QBOi.EXP1.AMIP.001
   │   │       ├── 1hr
   │   │       │   ├── QBOi.EXP1.AMIP.001.PRECT.1hr.nc
   │   │       │   └── (... other .nc files )
   │   │       ├── 3hr
   │   │       │   └── QBOi.EXP1.AMIP.001.PRECT.3hr.nc
   │   │       ├── day
   │   │       │   ├── QBOi.EXP1.AMIP.001.FLUT.day.nc
   │   │       │   └── (... other .nc files )
   │   │       └── mon
   │   │           ├── QBOi.EXP1.AMIP.001.PS.mon.nc
   │   │           └── (... other .nc files )
   │   └── obs_data ( = <OBS_DATA_ROOT>)
   │       ├── (... supporting data for individual PODs )

Note that ``mdtf`` now contains both the ``MDTF-diagnostics`` and ``inputdata`` directories. 

You can put the observational data and model output in different locations, e.g. for space reasons, by changing
the paths given in ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` as described below in :numref:`ref-configure`.

.. _ref-conda-install:

Installing dependencies
-----------------------

Installing XQuartz on MacOS
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're installing on a MacOS system, you will need to install `XQuartz <https://www.xquartz.org/>`__.
If the XQuartz executable isn't present in ``/Applications/Utilities``, you will need to download and run the installer
from the previous link.

The reason for this requirement is that the X11 libraries are
`required dependencies <https://www.ncl.ucar.edu/Download/macosx.shtml#InstallXQuartz>`__
for the NCL scripting language, even when it's run non-interactively.
Because the required libraries cannot be installed through conda (next section),
this installation needs to be done as a manual step.

Managing dependencies with the conda package manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework code is written in Python 3.11,
but supports running PODs written in a variety of scripting languages and combinations of libraries.
To ensure that the correct versions of these dependencies are installed and available,
we use `conda <https://docs.conda.io/en/latest/>`__, a free, open-source package manager.
Conda is one component of the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ and
`Anaconda <https://www.anaconda.com/>`__ python distributions, so having Miniconda/Anaconda is sufficient but not necessary.

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda using
the steps below, even if they have independent installations of the required languages.
A complete installation of all dependencies will take roughly 5 Gb, less if you've already installed some of the
dependencies through conda. The location of this installation can be changed with the ``--conda_root`` and ``--env_dir``
flags described below.

Users may install their own copies of Anaconda/Miniconda on their machine, or use a
centrally-installed version managed by their institution. Note that installing your own copy of Anaconda/Miniconda
will re-define the default locations of the conda executable and environment directory defined in your `.bash_profile`,
.bashrc`, or `.cshrc` file if you have previously used a version of conda managed by your institution,
so you will have to re-create any environments made using central conda installations.

If these space requirements are prohibitive, we provide an alternate method of installation which makes
no use of conda and instead assumes the user has installed the required external dependencies,
at the expense of portability. This is documented in a :doc:`separate section <start_nonconda>`.

Installing the conda package manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section, we install the conda package manager if it's not already present on your system.

- To determine if conda is installed, run :console:`% conda info` as the user who will be using the package.
The package has been tested against versions of conda >= 4.11.0. If a pre-existing conda installation is present,
continue to the following section to install the package's environments.
These environments will co-exist with any existing installation.

  .. note::
     **Do not** reinstall Miniconda/Anaconda if it's already installed for the user who will be running the package:
the installer will break the existing installation (if it's not managed with, e.g., environment modules.)

- If :console:`% conda info` doesn't return anything, you will need to install conda.
We recommend doing so using the Miniconda installer (available `here <https://docs.conda.io/en/latest/miniconda.html>`__) for the most recent version of python 3, although any version of Miniconda or Anaconda released after June 2019, using python 2 or 3, will work.

- Follow the conda `installation instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__
appropriate to your system.

- Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda3 by
running conda init?” (or similar) prompt. This will allow the installer to add the conda path to the user's shell login
script (e.g., ``~/.bashrc`` or ``~/.cshrc``). It's necessary to modify your login script due to the way conda is
implemented.

- Start a new shell to reload the updated shell login script.

Installing micromamba
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. _ref-micromamba-install:

`Micromamaba installation instructions <https://mamba.readthedocs.io/en/latest/micromamba-installation.html#>`__


Installing the package's conda environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we use conda to install the versions of the language interpreters and third-party libraries required
by the package's diagnostics.

- First, determine the location of your conda/micromamba installation by running :console:`% conda info --base` or :console:`% micromamba info`
as the user who will be using the package. This path will be referred to as <*CONDA_ROOT*> or <*MICROMAMBA_ROOT*> below.

- If you don't have write access to <*CONDA_ROOT*>/<*MICROMAMBA_ROOT*>
(for example, if conda has been installed for all users of a multi-user system),
you will need to tell conda to install its files in a different, writable location.
You can also choose to do this out of convenience, e.g. to keep all files and programs used by the MDTF package together
in the ``mdtf`` directory for organizational purposes. This location will be referred to as <*CONDA_ENV_DIR*> below.

To display information about all of the options in the conda_env_setup.sh and
micromamba_env_setup.sh environment installation scripts, run

.. code-block:: console

      % cd <CODE_ROOT>
      % ./src/conda/conda_env_setup.sh [-h|--help]
      % ./src/conda/micromamba_env_setup.sh [-h|--help]

- Install all the package's conda environments with anaconda/miniconda by running

  .. code-block:: console

      % cd <CODE_ROOT>
      % ./src/conda/conda_env_setup.sh --all --conda_root <CONDA_ROOT> --env_dir <CONDA_ENV_DIR>

  The names of all conda environments used by the package begin with “_MDTF”, so as not to conflict with other environments in your conda installation. The installation process should finish within ten minutes.

  - Substitute the paths identified above for <*CONDA_ROOT*> and <*CONDA_ENV_DIR*>.

  - If the ``--env_dir`` flag is omitted, the environment files will be installed in your system's conda's default location (usually <*CONDA_ROOT*>/envs).

- Install all the package's conda environments with micromamba by running

  .. code-block:: console

      % cd <CODE_ROOT>
      % ./src/conda/micromamba_env_setup.sh --all --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>
  <*MICROMAMBA_ROOT*> is the path to the micromamba installation on your system (e.g., /home/${USER}/micromamba)

  <*MICROMAMBA_EXE*> is the path to the micromamba executable on your system (e.g., /home/${USER}/.local/bin/micromamba)
.. note::

   Micromamba is required to install the conda environments on machines with Apple M-series chips.
   NCL and R do not provide package support these systems, and only
   python-based environments and PODs will work. Install the base and python3_base environments individually on M-series
   Macs by running

   .. code-block:: console

      % cd <CODE_ROOT>
      % ./src/conda/micromamba_env_setup.sh -e base --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>
      % ./src/conda/micromamba_env_setup.sh -e python3_base --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>

.. note::

   After installing the framework-specific conda environments, you shouldn't alter them manually
(i.e., never run ``conda update`` on them). To update the environments after an update to a new release
of the framework code, re-run the above commands.
   
   These environments can be uninstalled by deleting their corresponding directories under <*CONDA_ENV_DIR*>
(or <*CONDA_ROOT*>/envs/).


Location of the installed executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script used to install the conda environments in the previous section creates a script named ``mdtf`` in
the MDTF-diagnostics directory. This script is the executable you'll use to run the package and its diagnostics.
To test the installation, run

.. code-block:: console

   % cd <CODE_ROOT>
   % ./mdtf --version

The output should be

.. code-block:: console

   === Starting <CODE_ROOT>/mdtf_framework.py

   mdtf [version number]

.. _ref-configure:

Configuring framework paths
---------------------------

In order to run the diagnostics in the package, it needs to be provided with paths to the data and code dependencies
installed above. In general, there are two equivalent ways to configure any setting for the package:

- All settings are configured with command-line flags. The full documentation for the command line interface is at
:doc:`ref_cli`.

- Long lists of command-line options are cumbersome, and many of the settings
(such as the paths to data that we set here) don't change between different runs of the package.
For this purpose, any command-line setting can also be provided in an input configuration file.

- The two methods of setting options can be freely combined. Any values set explicitly on the command line will
override those given in the configuration file.

For the remainder of this section, we describe how to edit and use configuration files,
since the paths to data, etc., we need to set won't change.

An example of the configuration file format is provided at
`src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__.
This is meant to be a template you can customize according to your purposes: save a copy of the file at
<*config_file_path*> and open it in a text editor.
The following paths need to be configured before running the framework:

- ``OBS_DATA_ROOT`` should be set to the location of the supporting data that you downloaded in
:numref:`ref-supporting-data`. If you used the directory structure described in that section,
the default value provided in the configuration file (``../inputdata/obs_data/``) will be correct.
If you put the data in a different location, this value should be changed accordingly.
Note that relative paths can be used in the configuration file, and are always resolved relative to the location of
the MDTF-diagnostics directory (<*CODE_ROOT*>).

- Likewise, ``MODEL_DATA_ROOT`` should be updated to the location of the NCAR-CESM-CAM sample data
(``model.QBOi.EXP1.AMIP.001.tar``)downloaded in :numref:`ref-supporting-data`.
This data is required to run the test in the next section. If you used the directory structure described
in :numref:`ref-supporting-data`, the default value provided in the configuration file (``../inputdata/model/``)
will be correct.

- ``conda_root`` should be set to the location of your conda installation: the value of <*CONDA_ROOT*>
that was used in :numref:`ref-conda-install`.

- Likewise, if you installed the package's conda environments in a non-default location by using the ``--env_dir``
flag in :numref:`ref-conda-install`, the option ``conda_env_root`` should be set to this path (<*CONDA_ENV_DIR*>).

- Finally, ``OUTPUT_DIR`` should be set to the location you want the output files to be written to
(default: ``mdtf/wkdir/``; will be created by the framework).
The output of each run of the framework will be saved in a different subdirectory in this location.

In :doc:`start_config`, we describe more of the most important configuration options for the package,
and in particular how you can configure the package to run on different data.
A complete description of the configuration options is at :doc:`ref_cli`, or can be obtained by running
:console:`% ./mdtf --help`.

.. _ref-execute:

Running the package on sample model data
----------------------------------------

You are now ready to run the package's diagnostics on the sample data from NCAR's CESM-CAM model.
which is saved at <*config_file_path*> as described in the previous section.

.. code-block:: console

   % cd <CODE_ROOT>
   % ./mdtf -f <config_file_path>

The first few lines of output will be

.. code-block:: console

   === Starting <CODE_ROOT>/mdtf_framework.py

   PACKAGE SETTINGS:
   case_list(0):
      CASENAME: QBOi.EXP1.AMIP.001
      model: CESM
      convention: CESM
      FIRSTYR: 1977
      LASTYR: 1981
   [...]

Run time may be up to 10-20 minutes, depending on your system. The final lines of output should be:

.. code-block:: console

   Exiting normally from <CODE_ROOT>/src/core.py
   Summary for QBOi.EXP1.AMIP.001:
      All PODs exited cleanly.
      Output written to <OUTPUT_DIR>/MDTF_QBOi.EXP1.AMIP.001_1977_1981

This shows that the output of the package has been saved to a directory named ``MDTF_QBOi.EXP1.AMIP.001_1977_1981``
in <*OUTPUT_DIR*>. The results are presented as a series of web pages, with the top-level page named index.html.
To view the results in a web browser (e.g., Google Chrome, Firefox) run

.. code-block:: console

   % google-chrome <OUTPUT_DIR>/MDTF_QBOi.EXP1.AMIP.001_1977_1981/index.html &

Currently the framework only analyzes one model dataset at a time.
To run another test for the the `MJO Propagation and Amplitude POD <../sphinx_pods/MJO_prop_amp.html>`__
on the sample data from GFDL's CM4 model, open the configuration file at <*config_file_path*>,
delete or comment out the section for ``QBOi.EXP1.AMIP.001`` in the ``caselist`` section of that file,
and uncomment the section for ``GFDL.CM4.c96L32.am4g10r8``.

In :doc:`start_config`, we describe further options to customize how the package is run.
