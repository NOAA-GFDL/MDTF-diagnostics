# MDTF-diagnostics [![Documentation Status](https://readthedocs.org/projects/mdtf-diagnostics/badge/?version=latest)](https://mdtf-diagnostics.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.com/NOAA-GFDL/MDTF-diagnostics.svg?branch=main)](https://travis-ci.com/NOAA-GFDL/MDTF-diagnostics) [![Total alerts](https://img.shields.io/lgtm/alerts/g/NOAA-GFDL/MDTF-diagnostics.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/NOAA-GFDL/MDTF-diagnostics/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/NOAA-GFDL/MDTF-diagnostics.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/NOAA-GFDL/MDTF-diagnostics/context:python)

The MDTF diagnostics package is a portable framework for running process-oriented diagnostics (PODs) on climate model data. Each POD script targets a specific physical process or emergent behavior, with the goals of determining how accurately the model represents that process, ensuring that models produce the right answers for the right reasons, and identifying gaps in the understanding of phenomena.

The MDTF Diagnostic Framework consists of multiple process-oriented diagnostic (POD) modules, each of which is developed by an individual research group or user. PODs are independent of each other, each POD:

1. Produces its own html file (webpage) as the final product
2. Consists of a set of diagnostics targeting specific physical processes
3. Produces a figure or multiple figures that can be displayed by the html in a browser

![MDTF_logo](<./doc/img/CPO_MAPP_MDTF_Logo.jpg>)

## Diagnostics in Package
Follow the links in the table below to view sample output, including a brief description
and a link to the full documentation for each diagnostic.

| Diagnostic | Contributor |
| :-------- | :-------- |
| [Convective Transition Diagnostics](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/convective_transition_diag/convective_transition_diag.html)  | J. David Neelin (UCLA)  |
|[MJO Teleconnections](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_teleconnection/MJO_teleconnection.html)   | Eric Maloney (CSU)   |
| [Extratropical Variance (EOF 500hPa Height)](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/EOF_500hPa/EOF_500hPa.html)   |CESM/AMWG (NCAR)  |
| [Wavenumber-Frequency Spectra](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/Wheeler_Kiladis/Wheeler_Kiladis.html) | CESM/AMWG (NCAR) |
| [MJO Spectra and Phasing](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_suite/MJO_suite.html)  | CESM/AMWG (NCAR)  |
| [Diurnal Cycle of Precipitation](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/precip_diurnal_cycle/precip_diurnal_cycle.html)  | Rich Neale (NCAR)   |
| Soil Moisture-Evapotranspiration coupling | Eric Wood (Princeton) |
| [MJO Propagation and Amplitude ](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL.CM4.c96L32.am4g10r8/MJO_prop_amp/MJO_prop_amp.html) (example with GFDL CM4 data)  | Xianan Jiang (UCLA)  |
| [AMOC 3D structure ](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL-CM2p1/transport_onto_TS/transport_onto_TS.html) (implementation in progress, example with GFDL CM2 model data)  | Xiaobiao Xu (FSU/COAPS)   |
| [ENSO Moist Static Energy budget](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_CCSM4/MSE_diag/MSE_diag.html) (implementation in progress, example with CCSM4 data)  | Hariharasubramanian Annamalai (U. Hawaii)  |
| [Warm Rain Microphysics](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/warm_rain_microphysics/documentation) (implementation in progress) | Kentaroh Suzuki (AORI, U. Tokyo)  |

### Examples of package output

- [Historical run of NOAA-GFDL ESM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-ESM4/), 1980-2014 ([Krasting et al. 2018](#citations))
- [Historical run of NOAA-GFDL CM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-CM4/), 1980-2014 ([Guo et al. 2018](#citations))
- [Historical run of NCAR CESM2/CAM4](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/) 1977-1981, from an earlier version of the package.

# Quickstart installation instructions

This document provides basic directions for downloading, installing and running a test of the MDTF framework using sample model data. See the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/) for all other information. The MDTF package has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

Throughout this document, `%` indicates the UNIX/LINUX command line prompt and is followed by commands to be executed in a terminal in `fixed-width font`, and `$` indicates strings to be substituted, e.g., the string `$CODE_ROOT` in section 1.1 should be substituted by the actual path to the MDTF-diagnostics directory.

### Summary of steps for running the package

You will need to download a) the source code, b) digested observational data, and c) two sets of sample model data (section 1). Afterwards, we describe how to install necessary Conda environments and languages (section 2) and run the framework on the default test case (sections 3 and 4). While the package contains quite a few scripts, the most relevant for present purposes are:

- `conda_env_setup.sh`: automated script for installing necessary Conda environments.
- `default_tests.jsonc`: configuration file for running the framework.

Consult the [Getting started](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/start_toc.html) for how to run the framework on your own data and configure general settings.

## 1. Download the package code and sample data for testing

### 1.1 Obtaining the code

The official repo for the MDTF code is hosted at the GFDL [GitHub account](https://github.com/NOAA-GFDL/MDTF-diagnostics). We recommend that all users test the [latest official release](https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.3).

To install the MDTF package on a local machine, open a terminal and create a directory named `mdtf`. Instructions for end-users and new developers is as follows:
- end users:
  1. `cd mdtf`, then clone your fork of the MDTF repo on your machine: `git clone https://github.com/[your fork name]/MDTF-diagnostics`
  2. Verify that you are on the main branch: `git branch` 
  (this is the default, but it never hurts to get in the habit of running git branch before you start working)
  3. Check out the latest official release: `git checkout tags/[version name]`
  4. Proceed with the installation process described in [section 2](#2.)
  5. Check out a new branch that will contain your edited config files: `git checkout -b [branch name]`
  6. Update the config files, then commit the changes: `git commit -m "description of your changes"`
  7. Push the changes on your branch to your remote fork: `git push -u origin [branch name]`
- new developers:
  1. `cd mdtf`, then clone your fork of the MDTF repo on your machine: `git clone https://github.com/[your fork name]/MDTF-diagnostics`
  2. Check out the develop branch: `git checkout develop`
  3. Proceed with the installation process described in [section 2](#2.)
  4. Check out a new branch for you POD: `git checkout feature/[POD name]`
  5. Edit existing files/create new files, then commit the changes: `git commit -m "description of your changes"`
  6. Push the changes on your branch to your remote fork: `git push -u origin feature/[POD name]`]

 Below we refer to this MDTF-diagnostics directory as `$CODE_ROOT`. It contains the following subdirectories:

- `diagnostics/`: directory containing source code and documentation of individual PODs.
- `doc/`: directory containing documentation (a local mirror of the documentation site).
- `src/`: source code of the framework itself.
- `tests/`: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the `main` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.

### 1.2 Obtaining supporting data

Supporting observational data and sample model data are available via anonymous FTP at [ftp://ftp.cgd.ucar.edu/archive/mdtf](ftp://ftp.cgd.ucar.edu/archive/mdtf). The observational data is required for the PODs’ operation, while the sample model data is provided for default test/demonstration purposes. The files most relevant for package installation and default tests are:

- Digested observational data (159 Mb): MDTF_v2.1.a.obs_data.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar).
- NCAR-CESM-CAM sample data (12.3 Gb): model.QBOi.EXP1.AMIP.001.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar).
- NOAA-GFDL-CM4 sample data (4.8 Gb): model.GFDL.CM4.c96L32.am4g10r8.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar).

Note that the above paths are symlinks to the most recent versions of the data and will be reported as zero bytes in an FTP client.

Download these three files and extract the contents in the following hierarchy under the `mdtf` directory:

```
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
```

The default test case uses the QBOi.EXP1.AMIP.001 sample. The GFDL.CM4.c96L32.am4g10r8 sample is only for testing the MJO Propagation and Amplitude POD. Note that `mdtf` now contains both `MDTF-diagnostics` and `inputdata` directories.

You can put the observational data and model output in different locations (e.g., for space reasons) by changing the values of `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` as described below in section 3.

## 2. Install the necessary programming languages and modules

*For users unfamiliar with Conda, section 2.1 can be skipped if Conda has been installed, but section 2.2 CANNOT be skipped regardless.*

The MDTF framework code is written in Python 2.7, but supports running PODs written in a variety of scripting languages and combinations of libraries. We use [Conda](https://docs.conda.io/en/latest/), a free, open-source package manager to install and manage these dependencies. Conda is one component of the [Miniconda](https://docs.conda.io/en/latest/miniconda.html) and [Anaconda](https://www.anaconda.com/) python distribution, so having Miniconda/Anaconda is sufficient but not necessary.

For maximum portability and ease of installation, we recommend that all users manage dependencies through Conda using the provided script `src/conda/conda_env_setup.sh`, even if they have independent installations of the required languages. A complete installation of all dependencies will take roughly 5 Gb, less if you've already installed some of the dependencies through Conda. The location of this installation can be changed with the `$CONDA_ENV_DIR` setting described below.

### 2.1 Conda installation

Here we are checking that the Conda command is available on your system. We recommend doing this via Miniconda or Anaconda installation. You can proceed directly to section 2.2 if Conda is already installed.

- To determine if Conda is installed, run `% conda --version` as the user who will be using the framework. The framework has been tested against versions of Conda >= 4.7.5.

- If the command doesn't return anything, i.e., you do not have a pre-existing Conda on your system, we recommend using the Miniconda installer available [here](https://docs.conda.io/en/latest/miniconda.html). Any version of Miniconda/Anaconda (2 or 3) released after June 2019 will work. Installation instructions [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html).

- Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda2 by running conda init?” (or similar) prompt. This will allow the installer to add the Conda path to the user's shell login script (e.g., `~/.bashrc` or `~/.cshrc`).

- Restart the terminal to reload the updated shell login script.

The framework’s environments will co-exist with an existing Miniconda/Anaconda installation. *Do not* reinstall Miniconda/Anaconda if it's already installed for the user who will be running the framework: the installer will break the existing installation (if it's not managed with, eg., environment modules.)

### 2.2 Framework-specific environment installation

Here we set up the necessary environments needed for running the framework and individual PODs via the provided script. These are sometimes referred to as "Conda environments" conventionally.

After making sure that Conda is available, run `% conda info --base` as the user who will be using the framework to determine the location of your Conda installation. This path will be referred to as `$CONDA_ROOT` below.

- If this path points to `/usr/` or a subdirectory therein, we recomnend having a separate Miniconda/Anaconda installation of your own following section 2.1.

Next, run
```
% cd $CODE_ROOT
% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR
```
to install all necessary environments (and create an executable; section 4.1), which takes ~10 min. The names of all framework-created environments begin with “_MDTF”, so as not to conflict with any other environments.

- Substitute the actual paths for `$CODE_ROOT`, `$CONDA_ROOT`, and `$CONDA_ENV_DIR`.

- The `--env_dir` flag allows you to put the program files in a designated location `$CONDA_ENV_DIR` (for space reasons, or if you don’t have write access). You can omit this flag, and the environments will be installed within `$CONDA_ROOT/envs/` by default.

- The `--all` flag makes the script install all environments prescribed by the YAML (.yml) files under `src/conda/` (one YAML for one environment). You can install the environments selectively by using the `--env` flag instead. For instance, `% ./src/conda/conda_env_setup.sh --env base --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR` will install the "_MDTF_base" environment prescribed by `env_base.yml`, and so on. With `--env`, the current script can install one environment at a time. Repeat the command for multiple environments.

- Note that _MDTF_base is mandatory for the framework's operation, and the other environments are optional, see section 4.3.

After installing the framework-specific Conda environments, you shouldn't manually alter them (i.e., never run `conda update` on them). To update the environments after updating the framework code, re-run the above commands. These environments can be uninstalled by simply deleting "_MDTF" directories under `$CONDA_ENV_DIR` (or `$CONDA_ROOT/envs/` for default setting).

## 4. Configure framework paths

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the configuration file format is provided at [src/default_tests.jsonc](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc). We recommend configuring the following settings by editing a copy of this file:

- If you've saved the supporting data in the directory structure described in section 1.2, the default values for `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` given in `src/default_tests.jsonc` (`../inputdata/obs_data` and `../inputdata/model`, respectively) will be correct. If you put the data in a different location, these paths should be changed accordingly.
- `WORKING_DIR` is used as a scratch location for files generated by the PODs, and should have sufficient quota to handle the full set of model variables you plan to analyze. No files are saved here, so your system's temp directory would be a good choice.
- `OUTPUT_DIR` should be set to the desired location for output files. The output of each run of the framework will be saved in a different subdirectory in this location.
- `conda_root` should be set to the value of `$CONDA_ROOT` used above in :ref:`ref-conda-env-install`.
- If you specified a non-default conda environment location with `$CONDA_ENV_DIR`, set `conda_env_root` to that value; otherwise, leave it blank.

`src/default_tests.jsonc` is a template/example for configuration options that will be passed to the executable as an input. Open it in an editor (we recommend working on a copy). The following adjustments are necessary before running the framework:

- If you've saved the supporting data in the directory structure described in section 1.2, the default values for `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` pointing to `mdtf/inputdata/obs_data/` and `mdtf/inputdata/model/` will be correct. If you put the data in a different location, these values should be changed accordingly.

- `OUTPUT_DIR` should be set to the location you want the output files to be written to (default: `mdtf/wkdir/`; will be created by the framework). The output of each run of the framework will be saved in a different subdirectory in this location.

- `conda_root` should be set to the value of `$CONDA_ROOT` used above in section 2.2.

- If you specified a custom environment location with `$CONDA_ENV_DIR`, set `conda_env_root` to that value; otherwise, leave it blank.

We recommend using absolute paths in `default_tests.jsonc`, but relative paths are also allowed and should be relative to `$CODE_ROOT`.

## 4. Execute the MDTF package with default test settings

The MDTF framework is run via a wrapper script at `$CODE_ROOT/mdtf`. 

The setup script (section 2.2) will have created an executable at `$CODE_ROOT/mdtf` which sets the correct Conda environments before running the framework and individual PODs. To test the installation, `% $CODE_ROOT/mdtf --help` will print help text on the command-line options. Note that, if your current working directory is `$CODE_ROOT`, you will need to run `% ./mdtf --help`.

For interested users, the `mdtf` executable is also a script, which calls `src/conda/conda_init.sh` and `src/mdtf.py`.

This should print the current version of the framework.

If you've installed the Conda environments using the `--all` flag (section 2.2), you can now run the framework on the CESM sample model data:
```
% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc
```
Run time may be 10-20 minutes, depending on your system.

- If you edited/renamed `default_tests.jsonc`, pass that file instead.

- The output files for this test case will be written to `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981`. When the framework is finished, open `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html` in a web browser to view the output report.

- The above command will execute PODs included in `pod_list` of `default_tests.jsonc`. Skipping/adding certain PODs by uncommenting/commenting out the POD names (i.e., deleting/adding `//`). Note that entries in the list must be separated by `,`. Check for missing or surplus `,` if you encounter an error (e.g., "ValueError: No closing quotation").

- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in "caselist" of `default_tests.jsonc`, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.

If you re-run the above command,  the result will be written to another subdirectory under `$OUTPUT_DIR`, i.e., output files saved previously will not be overwritten unless you change `overwrite` in the configuration file to `true`.

### 4.3 Framework interaction with Conda environments

As just described in section 4.2, when you run the `mdtf` executable, among other things, it reads `pod_list` in the configuration file and executes POD codes accordingly. For a POD included in the list (referred to as $POD_NAME):

1. The framework will first try to determine whether there is a Conda environment named `_MDTF_$POD_NAME` under `$CONDA_ENV_DIR`. If yes, the framework will switch to this environment and run the POD.

2. If not, the framework will then look into the POD's `settings.jsonc` file in `$CODE_ROOT/diagnostics/$POD_NAME`. `runtime_requirements` in the settings file specifies the programming language(s) adopted by the POD:

      a. If purely Python, the framework will switch to `_MDTF_python_base` and run the POD.

      b. If NCL is used, then `_MDTF_NCL_base`.

Note that for the six existing PODs depending on NCL (EOF_500hPa, MJO_prop_amp, MJO_suite, MJO_teleconnection, precip_diurnal_cycle, and Wheeler_Kiladis), Python is also used but merely as a wrapper. Thus the framework will switch to `_MDTF_NCL_base` when seeing both NCL and Python in the settings file.

If you choose to selectively install Conda environments using the `--env` flag (section 2.2), remember to install all the environments needed for the PODs you're interested in, and that `_MDTF_base` is mandatory for the framework's operation.

- For instance, the minimal installation for running the `EOF_500hPa` and `convective_transition_diag` PODs requres `_MDTF_base` (mandatory), `_MDTF_NCL_base` (because of b), and `_MDTF_convective_transition_diag` (because of 1). These can be installed by passing `base`, `NCL_base`, and `convective_transition_diag` to the `--env` flag one at a time (section 2.2).


## 5. Next steps

This quickstart installation instructions is part of the "Getting started" in the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/). Consult the rest of Getting started for more detailed information, including how to run the framework on your own data and configure general settings. For users interested in contributing a POD module, see "Developer information" or [Developer's Walkthrough](https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_walkthrough.pdf).

# Acknowledgements

![MDTF_funding_sources](<./doc/img/mdtf_funding.jpg>)

Development of this code framework for process-oriented diagnostics was supported by the [National Oceanic and Atmospheric Administration](https://www.noaa.gov/) (NOAA) Climate Program Office [Modeling, Analysis, Predictions and Projections](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP) (MAPP) Program (grant # NA18OAR4310280). Additional support was provided by [University of California Los Angeles](https://www.ucla.edu/), the [Geophysical Fluid Dynamics Laboratory](https://www.gfdl.noaa.gov/), the [National Center for Atmospheric Research](https://ncar.ucar.edu/), [Colorado State University](https://www.colostate.edu/), [Lawrence Livermore National Laboratory](https://www.llnl.gov/) and the US [Department of Energy](https://www.energy.gov/).  

Many of the process-oriented diagnostics modules (PODs) were contributed by members of the NOAA [Model Diagnostics Task Force](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP/MAPP-Task-Forces/Model-Diagnostics-Task-Force) under MAPP support. Statements, findings or recommendations in these documents do not necessarily reflect the views of NOAA or the US Department of Commerce.

## Citations

Guo, Huan; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna; Rand, Kristopher; Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas; Underwood, Seth; Vahlenkamp, Hans; Bushuk, Mitchell; Dunne, Krista A.; Dussin, Raphael; Gauthier, Paul PG; Ginoux, Paul; Griffies, Stephen M.; Hallberg, Robert; Harrison, Matthew; Hurlin, William; Lin, Pu; Malyshev, Sergey; Naik, Vaishali; Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Reichl, Brandon G; Schwarzkopf, Daniel M; Seman, Charles J; Shao, Andrew; Silvers, Levi; Wyman, Bruce; Yan, Xiaoqin; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.; Held, Isaac M; Krasting, John P.; Horowitz, Larry W.; Milly, P.C.D; Shevliakova, Elena; Winton, Michael; Zhao, Ming; Zhang, Rong (2018). NOAA-GFDL GFDL-CM4 model output historical. Version YYYYMMDD[1].Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.8594

Krasting, John P.; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna; Rand, Kristopher; Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas; Underwood, Seth; Vahlenkamp, Hans; Dunne, Krista A.; Gauthier, Paul PG; Ginoux, Paul; Griffies, Stephen M.; Hallberg, Robert; Harrison, Matthew; Hurlin, William; Malyshev, Sergey; Naik, Vaishali; Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Schwarzkopf, Daniel M; Seman, Charles J; Silvers, Levi; Wyman, Bruce; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.; Dussin, Raphael; Guo, Huan; He, Jian; Held, Isaac M; Horowitz, Larry W.; Lin, Pu; Milly, P.C.D; Shevliakova, Elena; Stock, Charles; Winton, Michael; Xie, Yuanyu; Zhao, Ming (2018). NOAA-GFDL GFDL-ESM4 model output prepared for CMIP6 CMIP historical. Version YYYYMMDD[1].Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.8597

## Disclaimer

This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
