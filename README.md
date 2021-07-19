# MDTF-diagnostics: A Portable Framework for Weather and Climate Model Data Analysis

[![Documentation Status](https://readthedocs.org/projects/mdtf-diagnostics/badge/?version=latest)](https://mdtf-diagnostics.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.com/NOAA-GFDL/MDTF-diagnostics.svg?branch=main)](https://travis-ci.com/NOAA-GFDL/MDTF-diagnostics) [![Total alerts](https://img.shields.io/lgtm/alerts/g/NOAA-GFDL/MDTF-diagnostics.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/NOAA-GFDL/MDTF-diagnostics/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/NOAA-GFDL/MDTF-diagnostics.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/NOAA-GFDL/MDTF-diagnostics/context:python)

The MDTF-diagnostics package is a portable framework for running process-oriented diagnostics (PODs) on weather and climate model data.

## What is a POD?
![MDTF_logo](<./doc/img/CPO_MAPP_MDTF_Logo.jpg>)
Each process-oriented diagnostic [POD; [Maloney et al.(2019)](#citations)] targets a specific physical process or emergent behavior to determine how well one or more models represent the process, ensure that models produce the right answers for the right reasons, and identify gaps in the understanding of phenomena. Each POD is independent of other PODs. PODs generate diagnostic figures that can be viewed as an html file using a web browser.

The links in the table below show sample output, a brief description,
and a link to the full documentation for each currently-supported POD.

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

## Example POD Analysis Results

- [Historical run of NOAA-GFDL ESM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-ESM4/), 1980-2014 ([Krasting et al. 2018](#citations))
- [Historical run of NOAA-GFDL CM4](https://extranet.gfdl.noaa.gov/~John.Krasting/mdtf/GFDL-CM4/), 1980-2014 ([Guo et al. 2018](#citations))
- [Historical run of NCAR CESM2/CAM4](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/) 1977-1981, from an earlier version of the package.

# Quickstart installation instructions

See the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/) for all other information, including more in-depth installation instructions.

## Prerequisites
- [Anaconda3](https://docs.anaconda.com/anaconda/install/) or [Miniconda3](https://docs.conda.io/en/latest/miniconda.html). Installation instructions are available [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html).
- MDTF-diagnositics is developed for macOS and Linux systems. The package has been tested on, but is not fully supported for, the Windows Subsystem for Linux.
## Notes
- `$` indicates strings to be substituted, e.g., the string `$CODE_ROOT` should be substituted by the actual path to the MDTF-diagnostics directory.
- Consult the [Getting started](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/start_toc.html) section to learn how to run the framework on your own data and configure general settings.
- POD contributors can consult the **[Developer Cheatsheet](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/dev_cheatsheet.rst)** for brief instructions and useful tips

## 1. Install MDTF-diagnostics

- Open a terminal and create a directory named `mdtf`, then `$ cd mdtf`

- Clone your fork of the MDTF repo on your machine: `git clone https://github.com/[your fork name]/MDTF-diagnostics`

- Check out the latest official release: `git checkout tags/[version name]`
- Run `% conda info --base` to determine the location of your Conda installation. This path will be referred to as `$CONDA_ROOT`.
- `cd $CODE_ROOT`, then run
`% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR`
  - Substitute the actual paths for `$CODE_ROOT`, `$CONDA_ROOT`, and `$CONDA_ENV_DIR`.

  - The `--env_dir` flag allows you to put the program files in a designated location `$CONDA_ENV_DIR` (for space reasons, or if you don’t have write access). You can omit this flag, and the environments will be installed within `$CONDA_ROOT/envs/` by default.

## 2. Download the sample data

Supporting observational data and sample model data are available via anonymous FTP at [ftp://ftp.cgd.ucar.edu/archive/mdtf](ftp://ftp.cgd.ucar.edu/archive/mdtf).
- Digested observational data (159 Mb): MDTF_v2.1.a.obs_data.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.1.a.obs_data.tar).
- NCAR-CESM-CAM sample data (12.3 Gb): model.QBOi.EXP1.AMIP.001.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar).
- NOAA-GFDL-CM4 sample data (4.8 Gb): model.GFDL.CM4.c96L32.am4g10r8.tar (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar).

Note that the above paths are symlinks to the most recent versions of the data and will be reported as zero bytes in an FTP client.

Running `tar -xvf [filename].tar` will extract the contents in the following hierarchy under the `mdtf` directory:

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

The default test case uses the QBOi.EXP1.AMIP.001 sample data. The GFDL.CM4.c96L32.am4g10r8 sample data is only needed to test the MJO Propagation and Amplitude POD.

You can put the observational data and model output in different locations (e.g., for space reasons) by changing the values of `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` as described below in section 3.

## 3. Configure framework paths

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the configuration file format is provided at [src/default_tests.jsonc](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/default_tests.jsonc). We recommend configuring the following settings by editing a copy of this file.

- If you've saved the supporting data in the directory structure described in section 2, the default values for `OBS_DATA_ROOT` and `MODEL_DATA_ROOT` given in `src/default_tests.jsonc` (`../inputdata/obs_data` and `../inputdata/model`, respectively) will be correct. If you put the data in a different location, these paths should be changed accordingly.
- `WORKING_DIR` is used as a scratch location for files generated by the PODs, and **should have sufficient quota to handle the full set of model variables you plan to analyze. This includes the sample model and observational data (approx. 19 GB) PLUS data required for the POD(s) you are developing.** No files are saved here, so your system's temp directory would be a good choice.
- `OUTPUT_DIR` should be set to the desired location for output files. `OUTPUT_DIR` and `WORKING_DIR` are set to the same locations by default. The output of each run of the framework will be saved in a different subdirectory in this location. **As with the WORKING_DIR, ensure that OUTPUT_DIR has sufficient space for all POD output**.
- `conda_root` should be set to the value of `$CONDA_ROOT` used in section 2.
- If you specified a non-default conda environment location with `$CONDA_ENV_DIR`, set `conda_env_root` to that value; otherwise, leave it blank.

We recommend using absolute paths in `default_tests.jsonc`, but relative paths are also allowed and should be relative to `$CODE_ROOT`.`$CODE_ROOT` contains the following subdirectories:

- `diagnostics/`: directory containing source code and documentation of individual PODs.
- `doc/`: directory containing documentation (a local mirror of the documentation site).
- `src/`: source code of the framework itself.
- `tests/`: unit tests for the framework.

## 4. Execute the MDTF package with default test settings

The MDTF framework is run via the wrapper script `$CODE_ROOT/mdtf` that is generated conda_env_install.sh. To test the installation, `% $CODE_ROOT/mdtf --help` will print help text on the command-line options. Note that, if your current working directory is `$CODE_ROOT`, you will need to run `% ./mdtf --help`.

This should print the current version of the framework.

To run the code on the test data using the version of default_tests.jsonc you modified:
```
% cd $CODE_ROOT
% ./mdtf -f src/default_tests.jsonc -v
```
-v is the "verbose" flag, and will print additional information that may help with debugging if you have issues

Run time may be 10-20 minutes, depending on your system.

- If you edited/renamed `default_tests.jsonc`, pass that file instead.

- The output files for this test case will be written to `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981`. When the framework is finished, open `$OUTPUT_DIR/QBOi.EXP1.AMIP.001_1977_1981/index.html` in a web browser to view the output report.

- The above command will execute PODs included in `pod_list` of `default_tests.jsonc`.

- Currently the framework only analyzes data from one model run at a time. To run the MJO_prop_amp POD on the GFDL.CM4.c96L32.am4g10r8 sample data, delete or comment out the section for QBOi.EXP1.AMIP.001 in "caselist" of `default_tests.jsonc`, and uncomment the section for GFDL.CM4.c96L32.am4g10r8.

- If you re-run the above command,  the result will be written to another subdirectory under `$OUTPUT_DIR`, i.e., output files saved previously will not be overwritten unless you change `overwrite` in the configuration file to `true`.

## 5. Next steps

For more detailed information, consult the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/latest/). The ["Getting Started"](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/start_toc.html) section has more detailed information on customizing your installation and running the framework on your own data. Users interested in contributing a POD should consult the ["Developer Information"](https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/dev_toc.html) section.

# Acknowledgements

![MDTF_funding_sources](<./doc/img/mdtf_funding.jpg>)

Development of this code framework for process-oriented diagnostics was supported by the [National Oceanic and Atmospheric Administration](https://www.noaa.gov/) (NOAA) Climate Program Office [Modeling, Analysis, Predictions and Projections](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP) (MAPP) Program (grant # NA18OAR4310280). Additional support was provided by [University of California Los Angeles](https://www.ucla.edu/), the [Geophysical Fluid Dynamics Laboratory](https://www.gfdl.noaa.gov/), the [National Center for Atmospheric Research](https://ncar.ucar.edu/), [Colorado State University](https://www.colostate.edu/), [Lawrence Livermore National Laboratory](https://www.llnl.gov/) and the US [Department of Energy](https://www.energy.gov/).

Many of the process-oriented diagnostics modules (PODs) were contributed by members of the NOAA [Model Diagnostics Task Force](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP/MAPP-Task-Forces/Model-Diagnostics-Task-Force) under MAPP support. Statements, findings or recommendations in these documents do not necessarily reflect the views of NOAA or the US Department of Commerce.

## Citations

Guo, Huan; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna; Rand, Kristopher; Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas; Underwood, Seth; Vahlenkamp, Hans; Bushuk, Mitchell; Dunne, Krista A.; Dussin, Raphael; Gauthier, Paul PG; Ginoux, Paul; Griffies, Stephen M.; Hallberg, Robert; Harrison, Matthew; Hurlin, William; Lin, Pu; Malyshev, Sergey; Naik, Vaishali; Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Reichl, Brandon G; Schwarzkopf, Daniel M; Seman, Charles J; Shao, Andrew; Silvers, Levi; Wyman, Bruce; Yan, Xiaoqin; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.; Held, Isaac M; Krasting, John P.; Horowitz, Larry W.; Milly, P.C.D; Shevliakova, Elena; Winton, Michael; Zhao, Ming; Zhang, Rong (2018). NOAA-GFDL GFDL-CM4 model output historical. Version YYYYMMDD[1].Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.8594

Krasting, John P.; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna; Rand, Kristopher; Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas; Underwood, Seth; Vahlenkamp, Hans; Dunne, Krista A.; Gauthier, Paul PG; Ginoux, Paul; Griffies, Stephen M.; Hallberg, Robert; Harrison, Matthew; Hurlin, William; Malyshev, Sergey; Naik, Vaishali; Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Schwarzkopf, Daniel M; Seman, Charles J; Silvers, Levi; Wyman, Bruce; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.; Dussin, Raphael; Guo, Huan; He, Jian; Held, Isaac M; Horowitz, Larry W.; Lin, Pu; Milly, P.C.D; Shevliakova, Elena; Stock, Charles; Winton, Michael; Xie, Yuanyu; Zhao, Ming (2018). NOAA-GFDL GFDL-ESM4 model output prepared for CMIP6 CMIP historical. Version YYYYMMDD[1].Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.8597

E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate and Weather Forecasting Models. BAMS, 100 (9), 1665–1686, [doi:10.1175/BAMS-D-18-0042.1](https://doi.org/10.1175/BAMS-D-18-0042.1).

## Disclaimer

This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
