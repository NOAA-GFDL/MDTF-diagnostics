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
package manager (:numref:`ref-conda-install`) or
`micromamba <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html>`__ (:numref:`ref-micromamba-install`)
and run the framework on sample model data (:numref:`ref-configure` and :numref:`ref-execute`).

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
  
  #. | :console:`% cd mdtf`, then clone your fork of the MDTF repo on your machine:
     | :console:`% git clone https://github.com/<your GitHub account name>/MDTF-diagnostics`.
  #. Verify that you are on the main branch: :console:`% git branch`.
  #. | Check out the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v4.0.alpha>`__:
     | :console:`% git checkout tags/v4.0.alpha`.
  #. Proceed with the installation process described below.
  #. | Check out a new branch that will contain your edited config files:
     | :console:`% git checkout -b <branch name>`.
  #. | Update the config files, then commit the changes:
     | :console:`% git commit -m \"description of your changes\"`.
  #. | Push the changes on your branch to your remote fork:
     | :console:`% git push -u origin <branch name>`.
   
- For new POD developers:
  
  #. | :console:`% cd mdtf`, then clone your fork of the MDTF repo on your machine:
     | :console:`% git clone https://github.com/<your GitHub account name>/MDTF-diagnostics`.
  #. Check out the ``main`` branch: :console:`% git checkout main`.
  #. Proceed with the installation process described below.
  #. | Check out a new branch for your POD:
     | :console:`% git checkout -b <POD branch name>`.
  #. | Edit existing files/create new files, then commit the changes:
     | :console:`% git commit -m \"description of your changes\"`.
  #. | Push the changes on your branch to your remote fork:
     | :console:`% git push -u origin <POD branch name>`.

The path to the code directory (``.../mdtf/MDTF-diagnostics``) is referred to as <*CODE_ROOT*>.
It contains the following subdirectories:

- ``diagnostics/``: directory containing source code and documentation of individual PODs.
- ``doc/``: source code for the documentation website.
- ``shared/``: shared code and resources for use by both the framework and PODs.
- ``src/``: source code of the framework itself.
- ``submodules/``: 3rd party software included in the framework workflow as submodules
- ``templates/``: runtime configuration template files
- ``tests/``: general tests for the framework.
- ``tools/``: helper scripts for building data catalogs and data management
- ``user_scripts/``: directory for POD developers to place custom preprocessing scripts

For advanced users interested in keeping more up-to-date on project development and contributing feedback,
the ``main`` branch of the GitHub repo contains features that haven’t yet been incorporated into an official release,
which are less stable or thoroughly tested.

.. _ref-conda-install:

Installing dependencies
-----------------------

Installing XQuartz on MacOS
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're installing on an MacOS system with Intel processors, you will need to install
`XQuartz <https://www.xquartz.org/>`__.
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
`Anaconda <https://www.anaconda.com/>`__ python distributions, so having Miniconda/Anaconda is sufficient but not
necessary.

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
  We recommend doing so using the Miniconda installer
  (available `here <https://docs.conda.io/en/latest/miniconda.html>`__) for the most recent version of python 3.

- Follow the conda
  `installation instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__
  appropriate to your system.

- Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda3 by
  running conda init?” (or similar) prompt. This will allow the installer to add the conda path to the user's shell
  login script (e.g., ``~/.bashrc`` or ``~/.cshrc``). It's necessary to modify your login script due to the way conda is
  implemented.

- Start a new shell to reload the updated shell login script.


.. _ref-micromamba-install:
Installing micromamba
^^^^^^^^^^^^^^^^^^^^^

`Micromamaba installation instructions <https://mamba.readthedocs.io/en/latest/micromamba-installation.html#>`__

Installing the package's conda environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we use conda to install the versions of the language interpreters and third-party libraries required
by the package's diagnostics.

- First, determine the location of your conda/micromamba installation by running :console:`% conda info --base` or
  :console:`% micromamba info` as the user who will be using the package. This path will be referred to as
  ``<CONDA_ROOT>`` or ``<MICROMAMBA_ROOT>`` below.

.. Note::

   Users working on machines (e.g., Derecho, Casper) using centrally-managed Conda distributions
   will need to symlink the Conda binaries to a writeable location to use as
   ``CONDA_ROOT``. A contributor provided the following solution:

     #. Create a directory ``[CONDA_LINK_DIR]`` in a writeable location.
     #. :console:`cd [CONDA_LINK_DIR] && mkdir bin && mkdir envs`
     #. Create symbolic links to the CISL Conda binary in ``bin``

        .. code-block:: console

          % ln -s /glade/u/apps/opt/conda/condabin/conda bin/conda

     #. If your ``CONDA_ENV_DIR`` is defined in a different location, create a symbolic link for the
        Conda environments

        .. code-block:: console

          % mkdir envs
          % ln -s [CONDA_ENV_DIR] envs


To display information about all of the options in the ``conda_env_setup.sh`` and
``micromamba_env_setup.sh`` environment installation scripts, run

    .. code-block:: console

        % cd <CODE_ROOT>
        % ./src/conda/conda_env_setup.sh [-h|--help]
        % ./src/conda/micromamba_env_setup.sh [-h|--help]

Install all the package's conda environments with anaconda/miniconda by running

    .. code-block:: console

        % cd <CODE_ROOT>
        % ./src/conda/conda_env_setup.sh --all --conda_root <CONDA_ROOT> --env_dir <CONDA_ENV_DIR>

The names of all conda environments used by the package begin with “_MDTF”, so as not to conflict with other
environments in your conda installation. The installation process should finish within ten minutes.

Substitute the paths identified above for ``<CONDA_ROOT>`` and ``<CONDA_ENV_DIR>``.

Install all the package's conda environments with micromamba by running

    .. code-block:: console

        % cd <CODE_ROOT>
        % ./src/conda/micromamba_env_setup.sh --all --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>

``<MICROMAMBA_ROOT>`` is the path to the micromamba installation on your system (e.g., /home/${USER}/micromamba)

``<MICROMAMBA_EXE>`` is the path to the micromamba executable on your system (e.g., /home/${USER}/.local/bin/micromamba)

.. note::

    Micromamba is required to install the conda environments on machines with Apple M-series chips.
    NCL and R do not provide package support these systems, and only
    python-based environments and PODs will work. Install the base and python3_base environments individually on
    M-series Macs by running

    .. code-block:: console

        % cd <CODE_ROOT>
        % ./src/conda/micromamba_env_setup.sh -e base --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>
        % ./src/conda/micromamba_env_setup.sh -e python3_base --micromamba_root <MICROMAMBA_ROOT> --micromamba_exe <MICROMAMBA_EXE> --env_dir <CONDA_ENV_DIR>

.. note::

    After installing the framework-specific conda environments, you shouldn't alter them manually
    (i.e., never run ``conda update`` on them). To update the environments after an update to a new release
    of the framework code, re-run the above commands.

    These environments can be uninstalled by deleting their corresponding directories under `<CONDA_ENV_DIR>`.

.. note::
    The micromamba environments may differ from the conda environments because of package compatibility discrepancies
    between solvers. The micromamba installation script only builds the **base** environment, and a limited version of
    the **python3_base** enviroment that excludes some packages and dependencies that may be required by the
    POD(s) you want to run.

Location of the installed executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script used to install the conda environments in the previous section creates a script named ``mdtf`` in
the MDTF-diagnostics directory. This script is the executable you'll use to run the package and its diagnostics.
To test the installation, run

.. code-block:: console

    % cd <CODE_ROOT>
    % ./mdtf --help

The output should be

.. code-block:: console

    Usage: MDTF-diagnostics [OPTIONS]

    A community-developed package to run Process Oriented Diagnostics on weather
    and climate data

    Options:
        -v, --verbose          Enables verbose mode.
        -f, --configfile PATH  Path to the runtime configuration file  [required]
        --help                 Show this message and exit.

.. _ref-supporting-data:

Creating synthetic data for example_multicase and other 4th generation and newer PODs that use ESM-intake catalogs
------------------------------------------------------------------------------------------------------------------
To generate synthetic data for functionality testing, create the Conda environment from the _env_sythetic_data.yml
file in src/conda, activate the environment, and install the
`mdtf-test-data <https://pypi.org/project/mdtf-test-data/>`__ package. Then run the driver script with the
desired data convention, start year, and time span. The example below generates two CMIP datasets spanning 5 years
that start in 1980 and 1985. The sample data can be used to run the
`example_multicase POD <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/diagnostics/example_multicase>`__
using the configuration in the
`multirun_config_template file <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example_multicase/multirun_config_template.jsonc>`__.

.. code-block:: console

    % mamba env create --force -q -f ./src/conda/_env_synthetic_data.yml
    % conda activate _MDTF_synthetic_data
    % pip install mdtf-test-data
    % mkdir mdtf_test_data && cd mdtf_test_data
    % mdtf_synthetic.py -c CMIP --startyear 1980 --nyears 5 --freq day
    % mdtf_synthetic.py -c CMIP --startyear 1985 --nyears 5 --freq day

Obtaining supporting data for 3rd-generation and older single-run PODs
-------------------------------------------------------------------------

Supporting observational data and sample model data for second and third generation single-run PODs are available
via globus. The observational data is required for the PODs’ operation,
while the sample model data is optional and only needed for test and demonstration purposes. The files you will need
to download are:

- `Digested observational data (Globus) <https://app.globus.org/file-manager?origin_id=87726236-cbdd-4a91-a904-7cc1c47f8912>`__.
- NOAA-GFDL-CM4 sample data (FTP 4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.
- `NCAR-CESM2-CAM4 Atmosphere Model sample data MDTFv2 (Globus 12.6 Gb tar file, QBOi case) <https://app.globus.org/file-manager?origin_id=52f097f5-b6ba-4cbb-8c10-8e17fa2b9bf4&origin_path=%2F>`__.
- `NCAR-CESM2-CAM6 Coupled Model sample data MDTFv3 (Globus, individual files) <https://app.globus.org/file-manager?origin_id=200c3a02-0c49-4e3c-ad24-4a24db9b1c2d&origin_path=%2F>`__.

The default single-run test case uses the ``QBOi`` sample dataset, and the ``GFDL.CM4.c96L32.am4g10r8``
sample dataset is only for testing the `MJO Propagation and Amplitude POD <../sphinx_pods/MJO_prop_amp.html>`__.
Note that the above FTP paths are symlinks to the most recent versions of the data, and will be reported as having
a size of zero bytes in an FTP client.

Download these files and extract the contents in the following directory hierarchy under the ``mdtf`` directory:

::

   mdtf
   ├── MDTF-diagnostics ( = <CODE_ROOT>)
   ├── inputdata
   │   ├── model
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
the paths given in ``OBS_DATA_ROOT`` as described below in :numref:`ref-configure`.

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

Runtime configuration file json and yaml templates are located in the
`templates <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates>`__ directory.
You can customize either template depending on your preferences; save a copy of the file at
<*config_file_path*> and open it in a text editor.
The following paths need to be configured before running the framework:

- ``DATA_CATALOG``:
  set to the path of the ESM-intake data catalog with model input data

- ``OBS_DATA_ROOT``:
  set to the location of input observational data if you are running PODs that require observational
  datasets (e.g., ../inputdata/obs_data).

- ``conda_root``:
  should be set to the location of your conda installation: the value of <*CONDA_ROOT*>
  that was used in :numref:`ref-conda-install`

- ``conda_env_root``:
  set to the location of the conda environments (should be the same as <*CONDA_ENV_DIR*> in
  :numref:`ref-conda-install`)

- ``micromamba_exe``: Set to the full path to micromamba executable on your system if you are using micromamba
  to manage the conda environments

- ``OUTPUT_DIR``:
  should be set to the location you want the output files to be written to
  (default: ``mdtf/wkdir/``; will be created by the framework).
  The output of each run of the framework will be saved in a different subdirectory in this location.

In :doc:`start_config`, we describe more of the most important configuration options for the package,
and in particular how you can configure the package to run on different data.
A complete description of the configuration options is at :doc:`ref_cli`, or can be obtained by running
:console:`% ./mdtf --help`.

.. _ref-execute:

Running the package on the example_multicase POD with synthetic CMIP model data
-------------------------------------------------------------------------------

You are now ready to run the example_multicase POD on the synthetic CMIP data
that is saved at <*config_file_path*> as described in the previous section.
Make sure to the modify the path entries in
`diagnostic/example_multicase/esm_catalog_CMIP_synthetic_r1i1p1f1_gr1.csv`,
and the "catalog_file" path in `diagnostic/example_multicase/esm_catalog_CMIP_synthetic_r1i1p1f1_gr1.json`
to include the root directory locations on your file system. Full paths must be specified.

Next, run

.. code-block:: console

   % cd <CODE_ROOT>
   % ./mdtf -f <config_file_path>

The first few lines of output will be

.. code-block:: console

    POD convention and data convention are both no_translation. No data translation will be performed for case CMIP_Synthetic_r1i1p1f1_gr1_19800101-19841231.
    POD convention and data convention are both no_translation. No data translation will be performed for case CMIP_Synthetic_r1i1p1f1_gr1_19850101-19891231.
    Preprocessing data for example_multicase

Run time may be up to 10-20 minutes, depending on your system. The final lines of output should be:

.. code-block:: console

    SubprocessRuntimeManager: completed all PODs.
    Checking linked output files for <#O2Lr:example_multicase>.
    No files are missing.

Process finished with exit code 0


The output are written to a directory named ``MDTF_Output`` in <*OUTPUT_DIR*>. The results are presented as a series
of web pages, with the top-level page named index.html. To view the results in a web browser
(e.g., Google Chrome, Firefox) run

.. code-block:: console

   % firefox <OUTPUT_DIR>/MDTF_Output/example_multicase/index.html &

In :doc:`start_config`, we describe further options to customize how the package is run.
