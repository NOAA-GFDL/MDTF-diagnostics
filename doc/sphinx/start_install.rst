Installation instructions
=========================

This section provides basic directions for downloading, installing and running a test of the Model Diagnostics Task Force (MDTF)  package using sample model data. The package has been tested on Linux, Mac OS, and the Windows Subsystem for Linux.

You will need to download the source code, digested observational data, and sample model data (:numref:`ref-download`). Afterwards, we describe how to install software dependencies using the `conda <https://docs.conda.io/en/latest/>`__ package manager (:numref:`ref-conda-install`) and run the framework on sample model data (:numref:`ref-configure` and :numref:`ref-execute`).

Throughout this document, ``%`` indicates the shell prompt and is followed by commands to be executed in a terminal in ``fixed-width font``. Variable values are denoted by angle brackets, e.g. <*HOME*> is the path to your home directory returned by running ``% echo $HOME``. 

.. _ref-download:

Obtaining the code
------------------

The official repo for the package's code is hosted at the NOAA-GFDL `GitHub account <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. We recommend that end users download the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.3>`__.

To install the MDTF package, create a directory named ``mdtf`` and unzip the code downloaded from the `release page <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.3>`__ there. This will create a directory titled ``MDTF-diagnostics-3.0-beta.3`` containing the files listed on the GitHub page. Below we refer to the path to this MDTF-diagnostics directory as <*CODE_ROOT*>. It contains the following subdirectories:

- ``diagnostics/``: directory containing source code and documentation of individual PODs.
- ``doc/``: source code for the documentation website.
- ``shared/``: shared code and resources for use by both the framework and PODs.
- ``sites/``: site-specific code and configuration files.
- ``src/``: source code of the framework itself.
- ``tests/``: general tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the ``main`` branch of the GitHub repo contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.

For POD developers, the ``develop`` branch of the GitHub repo is the “beta test” version of the framework. POD developers should begin by locally cloning the repo and checking out this branch, as described in :doc:`dev_git_intro`.

.. _ref-supporting-data:

Obtaining supporting data
-------------------------

Supporting observational data and sample model data are available via anonymous FTP from ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is optional and only needed for test and demonstration purposes. The files you will need to download are:

- Digested observational data (159 Mb): `MDTF_v2.1.a.obs_data.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar>`__.
- NCAR-CESM-CAM sample data (12.3 Gb): `model.QBOi.EXP1.AMIP.001.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar>`__.
- NOAA-GFDL-CM4 sample data (4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.

The default test case uses the ``QBOi.EXP1.AMIP.001`` sample dataset, and the ``GFDL.CM4.c96L32.am4g10r8`` sample dataset is only for testing the MJO Propagation and Amplitude POD. Note that the above paths are symlinks to the most recent versions of the data, and will be reported as having a size of zero bytes in an FTP client.

Download these files and extract the contents in the following directory hierarchy under the ``mdtf`` directory:

::

   mdtf
   ├── MDTF-diagnostics ( = <CODE_ROOT>)
   ├── inputdata
       ├── model ( = <MODEL_DATA_ROOT>)
       │   ├── GFDL.CM4.c96L32.am4g10r8
       │   │   └── day
       │   │       ├── GFDL.CM4.c96L32.am4g10r8.precip.day.nc
       │   │       └── (... other .nc files )
       │   └── QBOi.EXP1.AMIP.001
       │       ├── 1hr
       │       │   ├── QBOi.EXP1.AMIP.001.PRECT.1hr.nc
       │       │   └── (... other .nc files )
       │       ├── 3hr
       │       │   └── QBOi.EXP1.AMIP.001.PRECT.3hr.nc
       │       ├── day
       │       │   ├── QBOi.EXP1.AMIP.001.FLUT.day.nc
       │       │   └── (... other .nc files )
       │       └── mon
       │           ├── QBOi.EXP1.AMIP.001.PS.mon.nc
       │           └── (... other .nc files )
       └── obs_data ( = <OBS_DATA_ROOT>)
           ├── (... supporting data for individual PODs )

Note that ``mdtf`` now contains both the ``MDTF-diagnostics`` and ``inputdata`` directories. 

You can put the observational data and model output in different locations, e.g. for space reasons, by changing the paths given in ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` as described below in :numref:`ref-configure`.

.. _ref-conda-install:

Installing dependencies via the conda package manager
-----------------------------------------------------

The MDTF framework code is written in Python 3.7, but supports running PODs written in a variety of scripting languages and combinations of libraries. To ensure that the correct versions of these dependencies are installed and available, we use `conda <https://docs.conda.io/en/latest/>`__, a free, open-source package manager. Conda is one component of the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ and `Anaconda <https://www.anaconda.com/>`__ python distributions, so having Miniconda/Anaconda is sufficient but not necessary.

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda using the steps below, even if they have independent installations of the required languages. A complete installation of all dependencies will take roughly 5 Gb, less if you've already installed some of the dependencies through conda. The location of this installation can be changed with the ``--conda_root`` and ``--env_dir`` flags described below.

If these space requirements are prohibitive, we provide an alternate method of installation which makes no use of conda and instead assumes the user has installed the required external dependencies, at the expense of portability. This is documented in a :doc:`separate section <start_nonconda>`.

Installing the conda package manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section, we install the conda package manager if it's not already present on your system.

- To determine if conda is installed, run ``% conda info`` as the user who will be using the package. The package has been tested against versions of conda >= 4.7.5. If a pre-existing conda installation is present, continue to the following section to install the package's environments. These environments will co-exist with any existing installation.

  .. note::
     **Do not** reinstall Miniconda/Anaconda if it's already installed for the user who will be running the package: the installer will break the existing installation (if it's not managed with, e.g., environment modules.) 

- If ``% conda info`` doesn't return anything, you will need to install conda. We recommend doing so using the Miniconda installer (available `here <https://docs.conda.io/en/latest/miniconda.html>`__) for the most recent version of python 3, although any version of Miniconda or Anaconda released after June 2019, using python 2 or 3, will work. 

- Follow the conda `installation instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__ appropriate to your system.

- Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda3 by running conda init?” (or similar) prompt. This will allow the installer to add the conda path to the user's shell login script (e.g., ``~/.bashrc`` or ``~/.cshrc``). It's necessary to modify your login script due to the way conda is implemented.

- Start a new shell to reload the updated shell login script.

Installing the package's conda environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this section we use conda to install the versions of the language interpreters and third-party libraries required by the package's diagnostics. 

- First, determine the location of your conda installation by running ``% conda info --base`` as the user who will be using the package. This path will be referred to as <*CONDA_ROOT*> below.

- If you don't have write access to <*CONDA_ROOT*> (for example, if conda has been installed for all users of a multi-user system), you will need to tell conda to install its files in a different, writable location. You can also choose to do this out of convenience, e.g. to keep all files and programs used by the MDTF package together in the ``mdtf`` directory for organizational purposes. This location will be referred to as <*CONDA_ENV_DIR*> below.

- Install all the package's conda environments by running

  ::

      % cd <CODE_ROOT>
      % ./src/conda/conda_env_setup.sh --all --conda_root <CONDA_ROOT> --env_dir <CONDA_ENV_DIR>

  The names of all conda environments used by the package begin with “_MDTF”, so as not to conflict with other environments in your conda installation. The installation process should finish within ten minutes.

  - Substitute the paths identified above for <*CONDA_ROOT*> and <*CONDA_ENV_DIR*>.

  - If the ``--env_dir`` flag is omitted, the environment files will be installed in your system's conda's default location (usually <*CONDA_ROOT*>/envs).

.. note::

   After installing the framework-specific conda environments, you shouldn't alter them manually (i.e., never run ``conda update`` on them). To update the environments after an update to a new release of the framework code, re-run the above commands. 
   
   These environments can be uninstalled by deleting their corresponding directories under <*CONDA_ENV_DIR*> (or <*CONDA_ROOT*>/envs/).


Location of the installed executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script used to install the conda environments in the previous section creates a script named ``mdtf`` in the MDTF-diagnostics directory. This script is the executable you'll use to run the package and its diagnostics. To test the installation, run

::

   % cd <CODE_ROOT>
   % ./mdtf --version

The output should be

::

   === Starting <...>/MDTF-diagnostics/mdtf_framework.py

   mdtf 3.0 beta 3

.. _ref-configure:

Configuring framework paths
---------------------------

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the configuration file format is provided at `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__. We recommend configuring the following settings by editing a copy of this file:

``src/default_tests.jsonc`` is a template/example for configuration options that will be passed to the executable as an input. Open it in an editor (we recommend working on a copy). The following adjustments are necessary before running the framework:

- If you've saved the supporting data in the directory structure described in :numref:`ref-supporting-data`, the default values for ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` pointing to ``mdtf/inputdata/obs_data/`` and ``mdtf/inputdata/model/`` will be correct. If you put the data in a different location, these values should be changed accordingly.

- ``OUTPUT_DIR`` should be set to the location you want the output files to be written to (default: ``mdtf/wkdir/``; will be created by the framework). The output of each run of the framework will be saved in a different subdirectory in this location.

- ``conda_root`` should be set to the value of ``$CONDA_ROOT`` used above in :numref:`ref-conda-install`.

- If you specified a custom environment location with ``$CONDA_ENV_DIR``, set ``conda_env_root`` to that value; otherwise, leave it blank.

We recommend using absolute paths in ``default_tests.jsonc``, but relative paths are also allowed and should be relative to ``$CODE_ROOT``.

.. _ref-execute:

Running the package on sample model data
-----------------------------------------------

If you've installed the Conda environments using the ``--all`` flag (:numref:`ref-conda-install`), you can now run the framework on the CESM sample model data:

::

   % cd <CODE_ROOT>
   % ./mdtf -f src/default_tests.jsonc

Run time may be 10-20 minutes, depending on your system.

- If you edited/renamed ``default_tests.jsonc``, pass that file instead.

- The output files for this test case will be written to ``$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981``. When the framework is finished, open ``$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html`` in a web browser to view the output report.

- The above command will execute PODs included in ``pod_list`` of ``default_tests.jsonc``. Skipping/adding certain PODs by uncommenting/commenting out the POD names (i.e., deleting/adding ``//``). Note that entries in the list must be separated by ``,``. Check for missing or surplus ``,`` if you encounter an error (e.g., "ValueError: No closing quotation").

- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in "caselist" of ``default_tests.jsonc``, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.


