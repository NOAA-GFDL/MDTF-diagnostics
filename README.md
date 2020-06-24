# MDTF-diagnostics [![Build Status](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics.svg?branch=develop)](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics)

The MDTF diagnostics package is a portable framework for running process-oriented diagnostics (PODs) on climate model data. Each POD script targets a specific physical process or emergent behavior, with the goals of determining how accurately the model represents that process, ensuring that models produce the right answers for the right reasons, and identifying gaps in the understanding of phenomena.

The MDTF Diagnostic Framework consists of multiple process-oriented diagnostic (POD) modules, each of which is developed by an individual research group or user. PODs are independent of each other, each POD:

1. Produces its own html file (webpage) as the final product
2. Consists of a set of diagnostics targeting process-level performance
3. Produces a figure or multiple figures that can be displayed by the html in a browser

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

### Examples of package output

- [Historical run of NOAA-GFDL ESM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-ESM4/), 1980-2014
- [Historical run of NOAA-GFDL CM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-CM4/), 1980-2014
- [Historical run of NCAR CESM2/CAM4](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/) 1977-1981, from an earlier version of the package.

# Quickstart installation instructions

This document provides basic directions for downloading, installing and running a test of the MDTF framework using sample model data. See the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/) for all other information. The MDTF package has been tested on UNIX/LINUX, Mac OS, and Windows Subsystem for Linux.

Throughout this document, `%` indicates the UNIX/LINUX command line prompt and is followed by commands to be executed in a terminal in `fixed-width font`, and `$` indicates strings to be substituted, e.g., the string `$CODE_ROOT` in Section 1.1 should be substituted by the actual path to the MDTF-diagnostics directory.

### Summary of steps for running the package

You will need to download a) the source code, b) digested observational data, and c) two sets of sample model data (Section 1). Afterwards, we describe how to install necessary Conda environments and languages (Section 2) and run the framework on the default test case (Section 3). While the package contains quite a few scripts, the most relevant for present purposes are:

- `conda_env_setup.sh`: automated script for installing necessary Conda environments.
- `default_tests.jsonc`: configuration file for running the framework.

Consult the [Getting started](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/start_toc.html) for how to run the framework on your own data and configure general settings.

## 1. Download the package code and sample data for testing

### 1.1 Obtaining the code

The official repo for the MDTF code is hosted at the GFDL [GitHub account](https://github.com/NOAA-GFDL/MDTF-diagnostics). We recommend that end users download and test the [latest official release](https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.1).

To install the MDTF package on a local machine, create a directory named `mdtf` and unzip the code downloaded from the [release page](https://github.com/NOAA-GFDL/MDTF-diagnostics/releases/tag/v3.0-beta.2) there. This will create a directory titled `MDTF-diagnostics-3.0-beta.2` containing the files listed on the GitHub page. Below we refer to this MDTF-diagnostics directory as `$CODE_ROOT`. It contains the following subdirectories:

- `diagnostics/`: directory containing source code and documentation of individual PODs.
- `doc/`: directory containing documentation (a local mirror of the documentation site).
- `src/`: source code of the framework itself.
- `tests/`: unit tests for the framework.

For advanced users interested in keeping more up-to-date on project development and contributing feedback, the `main` branch contains features that haven’t yet been incorporated into an official release, which are less stable or thoroughly tested.

### 1.2 Obtaining supporting data

Supporting observational data and sample model data are available via anonymous FTP at ftp://ftp.cgd.ucar.edu/archive/mdtf. The observational data is required for the PODs’ operation, while the sample model data is provided for default test/demonstration purposes. The required files are:

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

You can put the observational data and model output in different locations (e.g., for space reasons) by changing the values of `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` as described below in Section 3.

## 2. Install the necessary programming languages and modules

The MDTF framework code is written in Python 2.7, but supports running PODs written in a variety of scripting languages and combinations of libraries. We use [Conda](https://docs.conda.io/en/latest/), a free, open-source package manager to install and manage these dependencies. Conda is one component of the [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/) python distribution, so having Miniconda/Anaconda is sufficient but not necessary.

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda using the provided script `src/conda/conda_env_setup.sh`, even if they have independent installations of the required languages. A complete installation of all dependencies will take roughly 5 Gb, less if you've already installed some of the dependencies through conda. The location of this installation can be changed with the `$CONDA_ENV_DIR` setting described below.

For maximum portability and ease of installation, we recommend that all users manage dependencies through conda, even if they have a pre-existing installations of the required languages. A complete installation of all dependencies requires roughly 5 Gb, and the location of this installation can be set with the `$CONDA_ENV_DIR` setting described below.

### 2.1 Conda installation

The framework’s environments will co-exist with an existing Miniconda/Anaconda installation. *Do not* reinstall Miniconda/Anaconda if it's already installed for the user who will be running the framework: the installer will break the existing installation (if it's not managed with, eg., environment modules.)

To determine if Conda is installed, run `% conda --version` as the user who will be using the framework. The framework has been tested against versions of conda >= 4.7.5. If you do not have a pre-existing Conda on your system (i.e., the command doesn't return anything), we recommend using the Miniconda installer available [here](https://docs.conda.io/en/latest/miniconda.html). Any version of Miniconda/Anaconda (2 or 3) released after June 2019 will work. Toward the end of the installation process, enter “yes” at “Do you wish the installer to initialize Miniconda2 by running conda init?” prompt. This will allow the installer to add the Conda path to the user's shell login script (e.g., `~/.bashrc` or `~/.cshrc`).

## 3. Install framework dependencies with conda

Run `% conda info --base` as the user who will be using the framework to determine the location of your Conda installation. This path will be referred to as `$CONDA_ROOT` below. After determining this path, run

Run `% conda info --base` as the user who will be using the framework to determine the location of your conda installation. This path will be referred to as `$CONDA_ROOT` below. If you don't have write access to this location (eg, on a multi-user system), you'll need to tell conda to install files in a non-default location `$CONDA_ENV_DIR`, as described below.

Next, run
```
% cd $CODE_ROOT
% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR
```

to install all needed environments under. This takes ~10 min. The names of all framework-created environments begin with “_MDTF”, so as not to conflict with any other environments.

By default, Conda will install the environments within `$CONDA_ROOT/envs/`. To use a different location (for space reasons, or if you don't have write access), pass the desired directory as `$CONDA_ENV_DIR`: `% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR`.

The `--all` flag makes the script install all environments prescribed by the YAML (.yml) files under `src/conda/` (one YAML file for one environment). You can install the environments selectively by using the `--env` flag instead. For instance, `% ./src/conda/conda_env_setup.sh --env base --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR` will install the "_MDTF_base" environment prescribed by `env_base.yml`, and so on. With `--env`, the current script can install one environment at a time. Repeat the command for multiple environments. Note that _MDTF_base is mandatory for the framework's operation, and the other environments are optional, see Section 4.3.

After installing the framework-specific Conda environments, you shouldn't manually alter them (i.e., never run `conda update` on them). To update the environments after updating the framework code, re-run the above commands.

## 4. Configure framework paths

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the configuration file format is provided at [src/default_tests.jsonc](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc). We recommend configuring the following settings by editing a copy of this file:

- If you've saved the supporting data in the directory structure described in section 1.2, the default values for `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` given in `src/default_tests.jsonc` (`../inputdata/obs_data` and `../inputdata/model`, respectively) will be correct. If you put the data in a different location, these paths should be changed accordingly.
- `WORKING_DIR` is used as a scratch location for files generated by the PODs, and should have sufficient quota to handle the full set of model variables you plan to analyze. No files are saved here, so your system's temp directory would be a good choice.
- `OUTPUT_DIR` should be set to the desired location for output files. The output of each run of the framework will be saved in a different subdirectory in this location.
- `conda_root` should be set to the value of `$CONDA_ROOT` used above in :ref:`ref-conda-env-install`.
- If you specified a non-default conda environment location with `$CONDA_ENV_DIR`, set `conda_env_root` to that value; otherwise, leave it blank.

Relative paths in the configuration file will be interpreted relative to `$CODE_ROOT`, and shell environment variables (eg, `$HOME`) will be expanded when the framework is run. 

## 5. Run the MDTF framework on sample data

### 5.1 Location of the MDTF executable

The MDTF framework is run via a wrapper script at `$CODE_ROOT/mdtf`. 

This is created by the conda environment setup script used in section 3. The wrapper script activates the framework's conda environment before calling the framework's code (and individual PODs). To verify that the framework and environments were installed successfully, run
```
% cd $CODE_ROOT
% ./mdtf --version
```

This should print the current version of the framework.

### 5.2 Run the framework on sample data

If you've downloaded the NCAR-CESM-CAM sample data (described in section 1.2 above), you can now perform a trial run of the framework:
```
% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc
```

If you edited a copy of ``default_tests.jsonc``, pass that file instead. Run time may be 10-20 minutes, depending on your system.

- If you edited or renamed `src/default_tests.jsonc`, as recommended in the previous section, pass the path to that configuration file instead.
- The output files for this test case will be written to `$OUTPUT_DIR/MDTF_QBOi.EXP1.AMIP.001_1977_1981`. When the framework is finished, open `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html` in a web browser to view the output report.
- The framework defaults to running all available PODs, which is overridden by the `pod_list` option in the `src/default_tests.jsonc` configuration file. Individual PODs can be specified as a comma-delimited list of POD names.
- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in `caselist` section of the configuration file, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.

## 6. Next steps

This quickstart installation instructions is part of the "Getting started" in the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/). Consult the rest of Getting started for more detailed information, including how to run the framework on your own data and configure general settings. For users interested in contributing a POD module, see "Developer information" or [Developer's Walkthrough](https://mdtf-diagnostics.readthedocs.io/en/latest/_static/MDTF_walkthrough.pdf).

# Acknowledgements

![MDTF_funding_sources](<./doc/img/mdtf_funding.jpg>)

Development of this code framework for process-oriented diagnostics was supported by the [National Oceanic and Atmospheric Administration](https://www.noaa.gov/) (NOAA) Climate Program Office [Modeling, Analysis, Predictions and Projections](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP) (MAPP) Program (grant # NA18OAR4310280). Additional support was provided by [University of California Los Angeles](https://www.ucla.edu/), the [Geophysical Fluid Dynamics Laboratory](https://www.gfdl.noaa.gov/), the [National Center for Atmospheric Research](https://ncar.ucar.edu/), [Colorado State University](https://www.colostate.edu/), [Lawrence Livermore National Laboratory](https://www.llnl.gov/) and the US [Department of Energy](https://www.energy.gov/).  

Many of the process-oriented diagnostics modules (PODs) were contributed by members of the NOAA [Model Diagnostics Task Force](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP/MAPP-Task-Forces/Model-Diagnostics-Task-Force) under MAPP support. Statements, findings or recommendations in these documents do not necessarily reflect the views of NOAA or the US Department of Commerce.

## Dependencies

This code base makes use of the [six](https://github.com/benjaminp/six) library, copyright (c) 2010-2020 Benjamin Peterson and provided under an MIT license.

## Disclaimer

This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
