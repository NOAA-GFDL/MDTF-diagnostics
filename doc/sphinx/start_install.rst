Quickstart installation instructions
====================================

This section provides instructions for downloading, installing and running a test of the MDTF framework using sample model data. The MDTF framework has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

Throughout this document, ``%`` indicates the command line prompt and is followed by commands to be executed in a terminal in ``fixed-width font``. ``$`` indicates strings to be substituted, e.g., the string ``$CODE_ROOT`` below should be replaced by the actual path to the ``MDTF-diagnostics`` directory.

**Summary of steps for installing the framework**

You will need to download the source code, digested observational data, and sample model data (:numref:`ref-download`). Afterwards, we describe how to install software dependencies using the `conda <https://docs.conda.io/en/latest/>`__ package manager (:numref:`ref-install`, :numref:`ref-conda-env-install`) and run the framework on sample model data (:numref:`ref-configure` and :numref:`ref-execute`).

.. _ref-download:

Download the framework code and supporting data
-----------------------------------------------

Obtaining the code
^^^^^^^^^^^^^^^^^^

The official repo for the MDTF code is hosted at the NOAA-GFDL `GitHub account <https://github.com/NOAA-GFDL/MDTF-diagnostics>`__. We recommend that end users download and test the `latest official release <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.2>`__.

To install the MDTF framework, create a directory named ``mdtf`` and unzip the code downloaded from the `release page <https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.2>`__ there. This will create a directory titled ``MDTF-diagnostics-3.0-beta.2`` containing the files listed on the GitHub page. Below we refer to this MDTF-diagnostics directory as ``$CODE_ROOT``. It contains the following subdirectories:

- ``diagnostics/``: directory containing source code and documentation of individual PODs.
- ``doc/``: directory containing documentation (a local mirror of the documentation site).
- ``src/``: source code of the framework itself.
- ``tests/``: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the ``main`` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.

For POD developers, the ``develop`` branch is the “beta test” version of the framework. POD developers should begin by locally cloning the repo and checking out this branch, as described in :ref:`ref-dev-git-intro`.

.. _ref-supporting-data:

Obtaining supporting data
^^^^^^^^^^^^^^^^^^^^^^^^^

Supporting observational data and sample model data are available via anonymous FTP at ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is provided for default test/demonstration purposes. The required files are:

- Digested observational data (159 Mb): `MDTF_v2.1.a.obs_data.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar>`__.
- NCAR-CESM-CAM sample data (12.3 Gb): `model.QBOi.EXP1.AMIP.001.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar>`__.
- NOAA-GFDL-CM4 sample data (4.8 Gb): `model.GFDL.CM4.c96L32.am4g10r8.tar <ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar>`__.

Note that the above paths are symlinks to the most recent versions of the data and will be reported as zero bytes in an FTP client.

Download these three files and extract the contents in the following hierarchy under the ``mdtf`` directory:

::

   mdtf
   ├── MDTF-diagnostics
   ├── inputdata
       ├── model ( = $MODEL_DATA_ROOT)
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
       └── obs_data ( = $OBS_DATA_ROOT)
           ├── (... supporting data for individual PODs )


The default test case uses the QBOi.EXP1.AMIP.001 data. The GFDL.CM4.c96L32.am4g10r8 data is only for testing the MJO Propagation and Amplitude POD.

You can put the observational data and model output in different locations (e.g., for space reasons) by changing the values of ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` as described in :numref:`ref-configure`.

.. _ref-install:

Install the conda package manager, if needed
--------------------------------------------

The MDTF framework code is written in Python 3, but supports running PODs written in a variety of scripting languages and combinations of libraries. We use `conda <https://docs.conda.io/en/latest/>`__, a free, open-source package manager, to install and manage these dependencies. Conda is one component of the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ and `Anaconda <https://www.anaconda.com/>`__ Python distributions, so having Miniconda or Anaconda is sufficient but not required.

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda, even if they have a pre-existing installations of the required languages. A complete installation of all dependencies requires roughly 5 Gb, and the location of this installation can be set with the ``$CONDA_ENV_DIR`` setting described below. Note that conda does not create duplicates of dependencies that are already installed (instead using hard links by default). 

If these space requirements are prohibitive, we provide an alternate method of operation which makes no use of conda and relies on the user to install external dependencies, at the expense of portability. This is documented in a :doc:`separate section <start_nonconda>`.

Conda installation
^^^^^^^^^^^^^^^^^^

Users with an existing conda installation should skip this section and proceed to :numref:`ref-conda-env-install`.

- To determine if conda is installed, run ``% conda --version`` as the user who will be using the framework. The framework has been tested against versions of conda >= 4.7.5.

  .. warning::
     Do not install a new copy of Miniconda/Anaconda if it's already installed for the user who will be running the framework: the installer will break the existing installation (if it's not managed with, e.g., environment modules.) The framework’s environments are designed to coexist with an existing Miniconda/Anaconda installation. 

- If you do not have a pre-existing conda installation, we recommend installing Miniconda 3.x, available `here <https://docs.conda.io/en/latest/miniconda.html>`__. This version is not required: any version of Miniconda/Anaconda (2 or 3) released after June 2019 will work equally well.

  + Follow the `installation instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__ appropriate for your system. Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda3 by running conda init?” (or similar) prompt. This will allow the installer to add the conda path to the user's shell startup script (e.g., ``~/.bashrc`` or ``~/.cshrc``).

  + Restart the terminal to reload the updated shell startup script.

  + Mac OS users may encounter a message directing them to install the Java JDK. This can be ignored.


.. _ref-conda-env-install:

Install framework dependencies with conda
-----------------------------------------

As described above, all software dependencies for the framework and PODs are managed through conda environments. 

Run ``% conda info --base`` as the user who will be using the framework to determine the location of your conda installation. This path will be referred to as ``$CONDA_ROOT`` below. If you don't have write access to this location (eg, on a multi-user system), you'll need to tell conda to install files in a non-default location ``$CONDA_ENV_DIR``, as described below.

Next, run
::

% cd $CODE_ROOT
% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR

to install all dependencies, which takes ~10 min (depending on machine and internet connection). The names of all framework-created environments begin with “_MDTF”, so as not to conflict with user-created environments in a preexisting conda installation.

- Substitute the actual paths for ``$CODE_ROOT``, ``$CONDA_ROOT``, and ``$CONDA_ENV_DIR``.

- The optional ``--env_dir`` flag directs conda to install framework dependencies in ``$CONDA_ENV_DIR`` (for space reasons, or if you don’t have write access). If this flag is omitted, the environments will be installed in ``$CONDA_ROOT/envs/`` by default.

- The ``--all`` flag makes the script install all dependencies for all PODs. To selectively update individual conda environments after installation, use the ``--env`` flag instead. For instance, ``% ./src/conda/conda_env_setup.sh --env base --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR`` will update the environment named "_MDTF_base" defined in ``src/conda/env_base.yml``, and so on.

.. note::
   After installing the framework-specific conda environments, you shouldn't manually alter them (eg, never run ``conda update`` on them). To update the environments after updating the framework code, re-run the above commands. These environments can be uninstalled by simply deleting the "_MDTF" directories under ``$CONDA_ENV_DIR`` (or ``$CONDA_ROOT/envs/`` by default).


.. _ref-configure:

Configure framework paths
-------------------------

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the configuration file format is provided at `src/default_tests.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc>`__. We recommend configuring the following settings by editing a copy of this file. 

Relative paths in the configuration file will be interpreted relative to ``$CODE_ROOT``. The following settings need to be configured before running the framework:

- If you've saved the supporting data in the directory structure described in :ref:`ref-supporting-data`, the default values for ``OBS_DATA_ROOT`` and ``MODEL_DATA_ROOT`` given in ``src/default_tests.jsonc`` (``../inputdata/obs_data`` and ``../inputdata/model``, respectively) will be correct. If you put the data in a different location, these paths should be changed accordingly.

- ``OUTPUT_DIR`` should be set to the desired location for output files. The output of each run of the framework will be saved in a different subdirectory in this location.

- ``conda_root`` should be set to the value of ``$CONDA_ROOT`` used above in :ref:`ref-conda-env-install`.

- If you specified a non-default conda environment location with ``$CONDA_ENV_DIR``, set ``conda_env_root`` to that value; otherwise, leave it blank.

.. _ref-execute:

Run the MDTF framework on sample data
-------------------------------------

Location of the MDTF executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is run via a wrapper script at ``$CODE_ROOT/mdtf``. 

This is created by the conda environment setup script used in :numref:`ref-conda-env-install`. The wrapper script activates the framework's conda environment before calling the framework's code (and individual PODs). To verify that the framework and environments were installed successfully, run

::

% cd $CODE_ROOT
% ./mdtf --version

This should print the current version of the framework.

Run the framework on sample data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you've downloaded the NCAR-CESM-CAM sample data (described in :ref:`ref-supporting-data` above), you can now perform a trial run of the framework:

::

% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc

Run time may be 10-20 minutes, depending on your system.

- If you edited or renamed ``src/default_tests.jsonc``, as recommended in the previous section, pass the path to that configuration file instead.

- The output files for this test case will be written to ``$OUTPUT_DIR/MDTF_QBOi.EXP1.AMIP.001_1977_1981``. When the framework is finished, open ``$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html`` in a web browser to view the output report.

- The framework defaults to running all available PODs, which is overridden by the ``pod_list`` option in the ``src/default_tests.jsonc`` configuration file. Individual PODs can be specified as a comma-delimited list of POD names.

- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in ``caselist`` section of the configuration file, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.
