# MDTF-diagnostics [![Build Status](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics.svg?branch=develop)](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics)

The MDTF diagnostics package is a portable framework for running process-oriented diagnostics (PODs) on climate model data. Each POD module targets a specific physical process or emergent behavior, with the goals of determining how accurately the model represents that process, ensuring that models produce the right answers for the right reasons, and identifying gaps in the understanding of phenomena.

The package provides an extensible, portable and reproducible means for running these diagnostics as part of the model development workflow. The framework handles software dependency and data handling tasks, meaning that POD developers can focus on science instead of “reinventing the wheel”. Development is community-driven and built on open-source technologies. Documentation for users and contributors is hosted on <a href="https://mdtf-diagnostics.readthedocs.io/en/latest/">readthedocs.io</a>.

![MDTF_logo](<./doc/img/CPO_MAPP_MDTF_Logo.jpg>)

## Diagnostics in Package
Follow the links in the table below to view sample output, including a brief description
and a link to the full documentation for each diagnostic.

| Diagnostic | Contributor |
| :-------- | :-------- |
| [Convective Transition Diagnostics](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/convective_transition_diag/convective_transition_diag.html)  | J. David Neelin (UCLA)  |
|[MJO Teleconnections](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_teleconnection/MJO_teleconnection.html)   | Eric Maloney (CSU)   |
| [Extratropical Variance (EOF 500hPa Height)](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/EOF_500hPa/EOF_500hPa.html)   |CESM/AMWG (NCAR)  |
| [Wavenumber-Frequency Spectra](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/Wheeler_Kiladis/Wheeler_Kiladis.html) | CESM/AMWG (NCAR) |
| [MJO Spectra and Phasing](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_suite/MJO_suite.html)  | CESM/AMWG (NCAR)  |
| [Diurnal Cycle of Precipitation](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/precip_diurnal_cycle/precip_diurnal_cycle.html)  | Rich Neale (NCAR)   |
| Soil Moisture-Evapotranspiration coupling | Eric Wood (Princeton) |
| [MJO Propagation and Amplitude ](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL.CM4.c96L32.am4g10r8/MJO_prop_amp/MJO_prop_amp.html) (example with GFDL CM4 data)  | Xianan Jiang (UCLA)  |
| [AMOC 3D structure ](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL-CM2p1/transport_onto_TS/transport_onto_TS.html) (implementation in progress, example with GFDL CM2 model data)  | Xiaobiao Xu (FSU/COAPS)   |
| [ENSO Moist Static Energy budget](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_CCSM4/MSE_diag/MSE_diag.html) (implementation in progress, example with CCSM4 data)  | Hariharasubramanian Annamalai (U. Hawaii)  |
| [Warm Rain Microphysics](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/warm_rain_microphysics/documentation) (implementation in progress) | Kentaroh Suzuki (AORI, U. Tokyo)  |

### Sample Output Webpage
[Version 2.0 output](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save),  based on a CESM-CAM run.


# Quickstart installation instructions

This document provides basic directions for downloading, installing and running a test of the MDTF diagnostic framework package using sample model data. See the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/) for all other information. The current MDTF package has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

Throughout this document, `%` indicates the UNIX/LINUX command line prompt and is followed by commands to be executed in a terminal in `fixed-width font`, and `$` indicates strings to be substituted, e.g., the string `$CODE_ROOT` in section 1.1 should be substituted by the actual path to the MDTF-diagnostics directory.

### Summary of steps for running the package

You will need to download a) the source code, b) digested observational data, and c) two sets of sample model data (section 1). Afterwards, we describe how to install necessary Conda environments and languages (section 2) and run the framework on the default test case (sections 3 and 4). While the package contains quite a few scripts, the most relevant for present purposes are:

- `conda_env_setup.sh`: automated script for installing necessary Conda environments.
- `default_tests.jsonc`: configuration file for running the framework.

Consult the [Getting started](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/start_toc.html) for how to run the framework on your own data and configure general settings.

## 1. Download the package code and sample data for testing

### 1.1 Obtaining the code

The official repo for the MDTF code is hosted at the GFDL [GitHub account](https://github.com/NOAA-GFDL/MDTF-diagnostics). We recommend that end users download and test the [latest official release](https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1).

To install the MDTF package on a local machine, create a directory named `mdtf`, and unzip the code downloaded from the [release page](https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1) there. This will create a directory titled `MDTF-diagnostics-3.0-beta.1` containing the files listed on the GitHub page. Below we refer to this MDTF-diagnostics directory as `$CODE_ROOT`. It contains the following subdirectories:

- `diagnostics/`: directory containing source code and documentation of individual PODs.
- `doc/`: directory containing documentation (a local mirror of the documentation site).
- `src/`: source code of the framework itself.
- `tests/`: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the `main` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.

### 1.2 Obtaining supporting data

Supporting observational data and sample model data are available via anonymous FTP (ftp://ftp.cgd.ucar.edu/archive/mdtf). The observational data is required for the PODs’ operation, while the sample model data is provided for test/demonstration purposes. For package installation and default tests, the most relevant files are:

- Digested observational data (159 Mb): MDTF_v2.1.a.obs_data.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar).
- NCAR-CESM-CAM sample data (12.3 Gb): model.QBOi.EXP1.AMIP.001.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar).
- NOAA-GFDL-CM4 sample data (4.8 Gb): model.GFDL.CM4.c96L32.am4g10r8.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar).

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

The default test case uses the QBOi.EXP1.AMIP.001 sample. The GFDL.CM4.c96L32.am4g10r8 sample is only for testing the MJO Propagation and Amplitude POD. More data for additional PODs (including those still under development) are available from the FTP.

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

- Mac OS users may encounter a benign Java warning pop-up: *To use the "java" command-line tool you need to install a JDK.* It's safe to ignore it.

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
to install all necessary environments (and create an executable; section 4.1), which takes ~10 min (depending on machine and internet connection). The names of all framework-created environments begin with “_MDTF”, so as not to conflict with any other environments.

- Substitute the actual paths for `$CODE_ROOT`, `$CONDA_ROOT`, and `$CONDA_ENV_DIR`.

- The `--env_dir` flag allows you to put the program files in a designated location `$CONDA_ENV_DIR` (for space reasons, or if you don’t have write access). You can omit this flag, and the environments will be installed within `$CONDA_ROOT/envs/` by default.

- The `--all` flag makes the script install all environments prescribed by the YAML (.yml) files under `src/conda/` (one YAML for one environment). You can install the environments selectively by using the `--env` flag instead. For instance, `% ./src/conda/conda_env_setup.sh --env base --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR` will install the "_MDTF_base" environment prescribed by `env_base.yml`, and so on. With `--env`, the current script can install one environment at a time. Repeat the command for multiple environments.

- Note that _MDTF_base is mandatory for the framework's operation, and the other environments are optional, see section 4.3.

After installing the framework-specific Conda environments, you shouldn't manually alter them (i.e., never run `conda update` on them). To update the environments after updating the framework code, re-run the above commands. These environments can be uninstalled by simply deleting "_MDTF" directories under `$CONDA_ENV_DIR` (or `$CONDA_ROOT/envs/` for default setting).

## 3. Configuring package paths

`src/default_tests.jsonc` is a template/example for configuration options that will be passed to the executable as an input. Open it in an editor (we recommend working on a copy). The following adjustments are necessary before running the framework:

- If you've saved the supporting data in the directory structure described in section 1.2, the default values for `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` pointing to `mdtf/inputdata/obs_data/` and `mdtf/inputdata/model/` will be correct. If you put the data in a different location, these values should be changed accordingly.

- `OUTPUT_DIR` should be set to the location you want the output files to be written to (default: `mdtf/wkdir/`; will be created by the framework). The output of each run of the framework will be saved in a different subdirectory in this location.

- `conda_root` should be set to the value of `$CONDA_ROOT` used above in section 2.2.

- If you specified a custom environment location with `$CONDA_ENV_DIR`, set `conda_env_root` to that value; otherwise, leave it blank.

We recommend using absolute paths in `default_tests.jsonc`, but relative paths are also allowed and should be relative to `$CODE_ROOT`.

## 4. Execute the MDTF package with default test settings

### 4.1 Location of the MDTF executable

The setup script (section 2.2) will have created an executable at `$CODE_ROOT/mdtf` which sets the correct Conda environments before running the framework and individual PODs. To test the installation, `% $CODE_ROOT/mdtf --help` will print help text on the command-line options. Note that, if your current working directory is `$CODE_ROOT`, you will need to run `% ./mdtf --help`.

For interested users, the `mdtf` executable is also a script, which calls `src/conda/conda_init.sh` and `src/mdtf.py`.

### 4.2 Run the framework on sample data

If you've installed the Conda environments using the `--all` flag (section 2.2), you can now run the framework on the CESM sample model data:
```
% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc
```
Run time may be 10-20 minutes, depending on your system.

- If you edited/renamed `default_tests.jsonc`, pass that file instead.

- The output files for this test case will be written to `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981`. When the framework is finished, open `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html` in a web browser to view the output report.

- The above command will execute PODs included in `pod_list` of `default_tests.jsonc`. Skipping/adding certain PODs by uncommenting/commenting out the POD names (i.e., deleting/adding `//`). Note that entries in the list must be separated by `,` properly. Check for missing or surplus `,` if you encounter an error (e.g., "ValueError: No closing quotation").

- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in "caselist" of `default_tests.jsonc`, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.

If you re-run the above command,  the result will be written to another subdirectory under `$OUTPUT_DIR`, i.e., output files saved previously will not be overwritten unless you change `overwrite` in `default_tests.jsonc` to `true`.

### 4.3 Framework interaction with Conda environments

As just described in section 4.2, when you run the `mdtf` executable, among other things, it reads `pod_list` in `default_tests.jsonc` and executes POD codes accordingly. For a POD included in the list (referred to as $POD_NAME):

1. The framework will first try to look for the YAML file `src/conda/env_$POD_NAME.yml`. If it exists, the framework will assume that the corresponding Conda environment `_MDTF_$POD_NAME` has been installed under `$CONDA_ENV_DIR`, and will switch to this environment and run the POD.

2. If not, the framework will then look into the POD's `settings.jsonc` file in `$CODE_ROOT/diagnostics/$POD_NAME/`. The `runtime_requirements` section in `settings.jsonc` specifies the programming language(s) adopted by the POD:

      a. If purely Python 3, the framework will look for `src/conda/env_python3_base.yml` and check its content to determine whether the POD's requirements are met, and then switch to `_MDTF_python3_base` and run the POD.

      b. Similarly, if NCL or R is used, then `NCL_base` or `R_base`.

Note that for the 6 existing PODs depending on NCL (EOF_500hPa, MJO_prop_amp, MJO_suite, MJO_teleconnection, precip_diurnal_cycle, and Wheeler_Kiladis), Python is also used but merely as a wrapper. Thus the framework will switch to `_MDTF_NCL_base` when seeing both NCL and Python in `settings.jsonc`.

The framework verifies PODs' requirements via looking for the YAML files and their contents. Thus if you choose to selectively install Conda environments using the `--env` flag (section 2.2), remember to install all the environments needed for the PODs you're interested in, and that `_MDTF_base` is mandatory for the framework's operation.

- For instance, the minimal installation for running the `EOF_500hPa` and `convective_transition_diag` PODs requres `_MDTF_base` (mandatory), `_MDTF_NCL_base` (because of b), and `_MDTF_convective_transition_diag` (because of 1). These can be installed by passing `base`, `NCL_base`, and `convective_transition_diag` to the `--env` flag one at a time (section 2.2).


## 5. Next steps

This quickstart installation instructions is part of the "Getting started" in the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/). Consult the rest of Getting started for more detailed information, including how to run the framework on your own data and configure general settings. For users interested in contributing a POD module, see "Developer information" or [Developer's Walkthrough](https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_walkthrough.pdf).

# Acknowledgements

![MDTF_funding_sources](<./doc/img/mdtf_funding.jpg>)

Development of this code framework for process-oriented diagnostics was supported by the [National Oceanic and Atmospheric Administration](https://www.noaa.gov/) (NOAA) Climate Program Office [Modeling, Analysis, Predictions and Projections](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP) (MAPP) Program (grant # NA18OAR4310280). Additional support was provided by [University of California Los Angeles](https://www.ucla.edu/), the [Geophysical Fluid Dynamics Laboratory](https://www.gfdl.noaa.gov/), the [National Center for Atmospheric Research](https://ncar.ucar.edu/), [Colorado State University](https://www.colostate.edu/), [Lawrence Livermore National Laboratory](https://www.llnl.gov/) and the US [Department of Energy](https://www.energy.gov/).  

Many of the process-oriented diagnostics modules (PODs) were contributed by members of the NOAA [Model Diagnostics Task Force](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP/MAPP-Task-Forces/Model-Diagnostics-Task-Force) under MAPP support. Statements, findings or recommendations in these documents do not necessarily reflect the views of NOAA or the US Department of Commerce.

## Dependencies

This code base makes use of the [six](https://github.com/benjaminp/six) library, copyright (c) 2010-2020 Benjamin Peterson and provided under an MIT license.

## Disclaimer

This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
