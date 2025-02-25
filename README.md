# MDTF-diagnostics: A Portable Framework for Weather and Climate Model Data Analysis
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

[![MDTF_test](https://github.com/NOAA-GFDL/MDTF-diagnostics/actions/workflows/mdtf_tests.yml/badge.svg)](https://github.com/NOAA-GFDL/MDTF-diagnostics/actions/workflows/mdtf_tests.yml) [![CodeQL](https://github.com/NOAA-GFDL/MDTF-diagnostics/actions/workflows/codeql.yml/badge.svg)](https://github.com/NOAA-GFDL/MDTF-diagnostics/actions/workflows/codeql.yml) [![Documentation Status](https://readthedocs.org/projects/mdtf-diagnostics/badge/?version=main)](https://mdtf-diagnostics.readthedocs.io/en/main/?badge=main)

The MDTF-diagnostics package is a portable framework for running process-oriented diagnostics (PODs) on weather and
climate model data.

## What is a POD?
![MDTF_logo](<./doc/img/logo_MDTF.png>)
Each process-oriented diagnostic [POD; [Maloney et al.(2019)](#citations)] targets a specific physical process or
emergent behavior to determine how well one or more models represent the process, ensure that models produce the right
answers for the right reasons, and identify gaps in the understanding of phenomena. Each POD is independent of other
PODs. PODs generate diagnostic figures that can be viewed as an html file using a web browser.

## Available Diagnostics
The links in the table below show sample output, a brief description,
and a link to the full documentation for each currently-supported POD.

| Diagnostic                                                                                                                                                                                             | Contributor                                                                                        |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------|                                      
| [Blocking Neale](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/blocking_neale/doc/blocking_neale.rst)                                                                            | Rich Neale (NCAR), Dani Coleman (NCAR)                                                             |
| [Convective Transition Diagnostics](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/convective_transition_diag/convective_transition_diag.html) | J. David Neelin (UCLA)                                                                             |
| [Diurnal Cycle of Precipitation](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/precip_diurnal_cycle/precip_diurnal_cycle.html)                | Rich Neale (NCAR)                                                                                  |
| [Eulerian Storm Track](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/eulerian_storm_track/doc/eulerian_storm_track.rst)                                                          | James Booth (CUNY), Jeyavinoth Jeyaratnam                                                          |
| [Extratropical Variance (EOF 500hPa Height)](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/EOF_500hPa/EOF_500hPa.html)                        | CESM/AMWG (NCAR)                                                                                   |
| [Forcing Feedback Diagnostic](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/forcing_feedback/doc/forcing_feedback.rst)                                                           | Brian Soden (U. Miami), Ryan Kramer                                                                |
| [Mean Dynamic Sea Level Package](https://github.com/wrongkindofdoctor/MDTF-diagnostics/blob/main/diagnostics/MDSL/doc/MDSL.rst)                                             | C.Little (AER, Inc.), N. Etige, S. Vannah, M. Zhao                                                 |
| [Mixed Layer Depth](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/mixed_layer_depth/doc/mixed_layer_depth.rst)                                                                   | Cecilia Bitz (U. Washington), Lettie Roach                                                         |
| [MJO Propagation and Amplitude ](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_GFDL.CM4.c96L32.am4g10r8/MJO_prop_amp/MJO_prop_amp.html)                               | Xianan Jiang (UCLA)                                                                                |
| [MJO Spectra and Phasing](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_suite/MJO_suite.html)                                             | CESM/AMWG (NCAR)                                                                                   |
| [MJO Teleconnections](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/MJO_teleconnection/MJO_teleconnection.html)                               | Eric Maloney (CSU)                                                                                 |
| [Moist Static Energy Diagnostic Package](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/ENSO_MSE/doc/ENSO_MSE.rst)                                                                | H. Annamalai (U. Hawaii), Jan Hafner (U. Hawaii)                                      |
| [Ocean Surface Flux Diagnostic](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/ocn_surf_flux_diag/doc/ocn_surf_flux_diag.rst)                                                     | Charlotte A. DeMott (Colorado State University), Chia-Weh Hsu (GFDL)                               |
| [Precipitation Buoyancy Diagnostic](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/precip_buoy_diag/doc/precip_buoy_diag.rst)                                                     | J. David Neelin (UCLA), Fiaz Ahmed                                                                 |
| [Rossby Wave Sources Diagnostic Package](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/ENSO_RWS/doc/ENSO_RWS.rst)                                                                | H. Annamalai (U. Hawaii), Jan Hafner (U. Hawaii)                                     |
| [Sea Ice Suite](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/seaice_suite/doc/seaice_suite.rst)                                                                                 | Cecilia Bitz (U. Washington), Lettie Roach                                                         |
| [Soil Moisture-Evapotranspiration coupling](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/SM_ET_coupling/doc/SM_ET_coupling.rst)                                                 | Eric Wood (Princeton)                                                                              |
| [Stratosphere-Troposphere Coupling: Annular Modes](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_annular_modes/doc/stc_annular_modes.rst)                                    | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL)                                     |
| [Stratosphere-Troposphere Coupling: Eddy Heat Fluxes](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_eddy_heat_fluxes/doc/stc_eddy_heat_fluxes.rst)                           | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL)                                     |
| [Stratosphere-Troposphere Coupling: QBO and ENSO stratospheric teleconnections](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_qbo_enso/doc/stc_qbo_enso.rst)                 | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL), Dillon Elsbury (NOAA)              |
| [Stratosphere-Troposphere Coupling: Stratospheric Ozone and Circulation](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_eddy_heat_fluxes/doc/stc_ozone.rst)                   | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL)                                     |
| [Stratosphere-Troposphere Coupling: Stratospheric Polar Vortex Extremes](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_spv_extremes/doc/stc_spv_extremes.rst)                | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL)                                     |
| [Stratosphere-Troposphere Coupling: Vertical Wave Coupling](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/stc_vert_wave_coupling/doc/stc_vert_wave_coupling.rst)                 | Amy H. Butler (NOAA CSL), Zachary D. Lawrence (CIRES/NOAA PSL)                                     |
| [Surface Albedo Feedback](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/albedofb/doc/surface_albedo_feedback.rst)                                                                | Cecilia Bitz (U. Washington), Aaron Donahoe (U. Washington), Ed Blanchard, Wei Cheng, Lettie Roach |
| [Surface Temperature Extremes and Distribution Shape](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/temp_extremes_distshape/doc/temp_extremes_distshape.rst)                     | J. David Neelin (UCLA), Paul C Loikith (PSU), Arielle Catalano (PSU)                               |
| [TC MSE Variance Budget Analysis](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/TC_MSE/doc/TC_MSE.rst)                                                                           | Allison Wing (Florida State University), Jarrett Starr (Florida State University)                  |
| [Top Heaviness Metric](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/top_heaviness_metric/doc/top_heaviness_metric.rst)                                                          | Zhuo Wang (U.Illinois Urbana-Champaign), Jiacheng Ye (U.Illinois Urbana-Champaign)                 |
| [Tropical Cyclone Rain Rate Azimuthal Average](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/TC_Rain/doc/TC_Rain.rst)                                                            | Daehyun Kim (U. Washington), Nelly Emlaw (U.Washington)                                            |
| [Tropical Pacific Sea Level](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/tropical_pacific_sea_level/doc/tropical_pacific_sea_level.rst)                                        | Jianjun Yin (U. Arizona), Chia-Weh Hsu (GFDL)                                                      |
| [Wavenumber-Frequency Spectra](https://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/Wheeler_Kiladis/Wheeler_Kiladis.html)                            | CESM/AMWG (NCAR)                                                                                   |

## Example POD Analysis Results

- [Historical run of NOAA-GFDL ESM4](https://extranet.gfdl.noaa.gov/~oar.gfdl.mdtf/mdtf/diagnostic_output/MDTF_ESM4_historical_D1_1996_1999/), 1980-2014 ([Krasting et al. 2018](#citations))
- [Historical run of NOAA-GFDL CM4](https://extranet.gfdl.noaa.gov/~oar.gfdl.mdtf/mdtf/diagnostic_output/MDTF_CM4_historical_LONG_1980_2014/), 1980-2014 ([Guo et al. 2018](#citations))
- [Historical run of NCAR CESM2/CAM4](https://extranet.gfdl.noaa.gov/~oar.gfdl.mdtf/mdtf/diagnostic_output/MDTF_QBOi.EXP1.AMIP.001_1977_1981/), 1977-1981

# Quickstart installation instructions

#### See the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/main/) for all other information, including more in-depth installation instructions.

#### Visit the [GFDL Youtube Channel](https://www.youtube.com/channel/UCCVFLbjYix7RCz1GgKG2QxA) for tutorials on package installation and other MDTF-diagnostics-related topics

## Prerequisites
- [Anaconda3](https://docs.anaconda.com/anaconda/install/), [Miniconda3](https://docs.conda.io/en/latest/miniconda.html), 
or [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html). 

- Installation instructions are available [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html).
- MDTF-diagnositics is developed for macOS and Linux systems. The package has been tested on, but is not fully supported
for, the Windows Subsystem for Linux.
- **Attention macOS M-series chip users**: the MDTF-diagnostics base and python3 conda environments will only build with
  micromamba on machines running Apple M-series chips. The NCL and R environments will NOT build on M-series machines
  because the conda packages do not support them at this time.
## Notes
- `$` indicates strings to be substituted, e.g., the string `$CODE_ROOT` should be substituted by the actual path to the
  MDTF-diagnostics directory.
- Consult the [Getting started](https://mdtf-diagnostics.readthedocs.io/en/main/sphinx/start_toc.html) section to learn how to run the framework on your own data and configure general
  settings.
- POD contributors can consult the **[Developer Cheatsheet](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/doc/sphinx/dev_cheatsheet.rst)** for brief instructions and useful tips


## 1. Install MDTF-diagnostics

- Open a terminal and create a directory named `mdtf`, then `$ cd mdtf`

- Clone your fork of the MDTF repo on your machine: `git clone https://github.com/[your fork name]/MDTF-diagnostics`

- Check out the latest official release: `git checkout tags/[version name]`
- Run `% conda info --base` to determine the location of your Conda installation. This path will be referred to as
  `$CONDA_ROOT`.
- `cd $CODE_ROOT`, then run
### ANACONADA/MINICONDA
`% ./src/conda/conda_env_setup.sh --all --conda_root $CONDA_ROOT --env_dir $CONDA_ENV_DIR`
### MICROMAMBA on machines that do NOT have Apple M-series chips
`% ./src/conda/micromamba_env_setup.sh --all --micromamba_root $MICROMAMBA_ROOT --micromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR`
### MICROMAMBA on machines with Apple M-series chips
`% ./src/conda/micromamba_env_setup.sh -e base --micromamba_root $MICROMAMBA_ROOT --micromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR`

`% ./src/conda/micromamba_env_setup.sh -e python3_base --micromamba_root $MICROMAMBA_ROOT --micromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR`

  - Substitute the actual paths for `$CODE_ROOT`, `$CONDA_ROOT`, `$MICROMAMBA_ROOT`, `MICROMAMBA_EXE`, and
    `$CONDA_ENV_DIR`.
  - `$MICROMAMBA_ROOT` is the path to micromamba installation on your system
     (e.g., /home/${USER}/micromamba). This is defined by the `$MAMBA_ROOT_PREFIX` environment variable on your system 
     when micromamba is installed
  - `$MICROMAMBA_EXE` is full path to the micromamba executable on your system
     (e.g., /home/${USER}/.local/bin/micromamba). This is defined by the `MAMBA_EXE` environment variable on your system
  - All flags noted for your system above must be supplied for the script to work.

  #### NOTE: The micromamba environments may differ from the conda environments because of package compatibility discrepancies between solvers `% ./src/conda/micromamba_env_setup.sh --all --micromamba_root $MICROMAMBA_ROOT --micromamba_exe $MICROMAMBA_EXE --env_dir $CONDA_ENV_DIR` builds the **base** environment, **NCL_base** environment, and the **python3_base** environment.
  
  #### NOTE: If you are trying to install environments with a Conda package managed by your institution, you will need to set your environment directory to a location with write access, and symbolically link $CONDA_ROOT/envs to this environment directory: `% ln -s [ROOT_DIR]/miniconda3/envs [path to your environment directory]`

## 2. Download the sample data

Supporting observational data and sample model data are available via 
Globus.
-  [Digested observational data](https://app.globus.org/file-manager?origin_id=87726236-cbdd-4a91-a904-7cc1c47f8912)
- NOAA-GFDL-CM4 sample data (4.8 Gb): model.GFDL.CM4.c96L32.am4g10r8.tar
  (ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar)
- [CESM2-CAM6 Coupled model timeslice data, individual files]
  (https://app.globus.org/file-manager?origin_id=200c3a02-0c49-4e3c-ad24-4a24db9b1c2d&origin_path=%2F)
- [CESM2-CAM4 Atmosphere timeslice data (QBOi case) tar or individual files] 
  (https://app.globus.org/file-manager?origin_id=52f097f5-b6ba-4cbb-8c10-8e17fa2b9bf4&origin_path=%2F)

For tar files tranfered over ftp, please note that the above paths are symlinks to the most recent versions of the data and will be reported as zero bytes in an FTP client.
Running `tar -xvf [filename].tar` will extract the contents in the following hierarchy under the `mdtf` directory:

```
mdtf
 ├── MDTF-diagnostics
 ├── inputdata
     ├── model
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

The default test case uses the QBOi.EXP1.AMIP.001 sample data. The GFDL.CM4.c96L32.am4g10r8 sample data is only
needed to test the MJO Propagation and Amplitude POD.

You can put the observational data and model output in different locations (e.g., for space reasons) by changing the
values of `OBS_DATA_ROOT`as described below in section 3.

## 3. Generate a data catalog for the sample input data

The MDTF-diagnostics package provides a basic catalog generator to assist users with building data catalogs in
the [tools/catalog_builder directory](https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/tools/catalog_builder) 

## 4. Configure framework paths

The MDTF framework supports setting configuration options in a file as well as on the command line. An example of the
configuration file format is provided at [templates/runtime_config.[jsonc | yml]](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/templates).
We recommend configuring the following settings by editing a copy of this file.

- `CATALOG_DIR`: path to the ESM-intake data catalog
- If you've saved the supporting data in the directory structure described in section 2, and use observational input data
  the default value for `OBS_DATA_ROOT` (`../inputdata/obs_data`) will be correct. If you put the data in a different
  location, the path should be changed accordingly.
- `WORK_DIR` is used as a scratch location for files generated by the PODs, and **should** have sufficient quota to
   handle the full set of model variables you plan to analyze. This includes the sample model and observational data
   (approx. 19 GB) PLUS data required for the POD(s) you are developing.** No files are saved here unless you set
   `OUTPUT_DIR` to the same location as `WORK_DIR`, so a temporary directory would be a good choice.
- `OUTPUT_DIR` should be set to the desired location for output files. `OUTPUT_DIR` and `WORK_DIR` are set to the same
  locations by default. The output of each run of the framework will be saved in a different subdirectory in this
  location. **As with the `WORK_DIR`, ensure that `OUTPUT_DIR` has sufficient space for all POD output**.
- `conda_root` should be set to the value of `$CONDA_ROOT` used in section 2.
- Likewise, set `conda_env_root` to the same location as `$CONDA_ENV_DIR` in section 2

We recommend using absolute paths in `runtime_config.[jsonc | yml]`, but relative paths are also allowed and should be
relative to `$CODE_ROOT`.`$CODE_ROOT` contains the following subdirectories:

- `diagnostics/`: directory containing source code and documentation of individual PODs
- `doc/`: directory containing documentation (a local mirror of the documentation site)
- `src/`: source code of the framework itself
- `submodules/`: location to place 3rd-party submodules to run as part of the MDTF-diagnostics workflow
- `tests/`: unit tests for the framework
- `templates/`: runtime configuration template files
- `tools/`: helper scripts for building ESM-intake catalogs, and other utilities
- `user_scripts/`: directory where users can place custom preprocessing scripts

## 5. Run the framework
The framework runs PODs that analyze one or more model datasets (cases), along with optional observational datasets,
using. To run the framework on the **[example_multicase](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/diagnostics/example_multicase)** POD, modify the example configuration file and run
```commandline
cd $CODE_ROOT
./mdtf -f templates/[runtime_config.[jsonc | yml]
```

The above command will execute PODs included in `pod_list` block of `runtime_config.[jsonc | yml]`.

If you re-run the above command, the result will be written to another subdirectory under `$OUTPUT_DIR`, 
i.e., output files saved previously will not be overwritten unless you change `overwrite` in the configuration file
to `true`.

The output files for the test case will be written to `$OUTPUT_DIR/MDTF_Output/` (_[v(number)] will be appended
output directories if an existing MDTF_Output directory is present in the `$OUTPUT_DIR`). 
When the framework is finished, open `$OUTPUT_DIR/MDTF_Output/[POD NAME]/index.html` in a web browser to view 
the output report.

You can specify your own datasets in the `caselist` block of the runtime config file and provide a catalog with
the model data, 
or run the example_multicase POD on the synthetic data and associated test catalog specified in the configuration file.
To generate the synthetic CMIP data, run:
```commandline
mamba env create --force -q -f ./src/conda/_env_synthetic_data.yml
conda activate _MDTF_synthetic_data
pip install mdtf-test-data
mkdir mdtf_test_data && cd mdtf_test_data
mdtf_synthetic.py -c CMIP --startyear 1980 --nyears 5 --freq day
mdtf_synthetic.py -c CMIP --startyear 1985 --nyears 5 --freq day
```
Then, modify the ``path`` entries in diagnostic/example_multicase/esm_catalog_CMIP_synthetic_r1i1p1f1_gr1.csv, and
the `"catalog_file":` path in diagnostic/example_multicase/esm_catalog_CMIP_synthetic_r1i1p1f1_gr1.json to include the
root directory locations on your file system. Full paths must be specified.

Depending on the POD(s) you run, the size of your input datasets, and your system hardware, run time may be 10--20
minutes.

## 6. Next steps

For more detailed information, consult the [documentation site](https://mdtf-diagnostics.readthedocs.io/en/main/). Users interested in
contributing a POD should consult the ["Developer Information"](https://mdtf-diagnostics.readthedocs.io/en/main/sphinx/pod_dev_toc.html) section.

# Acknowledgements

![MDTF_funding_sources](<./doc/img/mdtf_funding.jpg>)

Development of this code framework for process-oriented diagnostics was supported by the
[National Oceanic and Atmospheric Administration](https://www.noaa.gov/)
(NOAA) Climate Program Office [Modeling, Analysis, Predictions and Projections](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP)
(MAPP) Program (grant # NA18OAR4310280). Additional support was provided by [University of California Los Angeles](https://www.ucla.edu/),
the [Geophysical Fluid Dynamics Laboratory](https://www.gfdl.noaa.gov/), the [National Center for Atmospheric Research](https://ncar.ucar.edu/),
[Colorado State University](https://www.colostate.edu/), [Lawrence Livermore National Laboratory](https://www.llnl.gov/) and the US [Department of Energy](https://www.energy.gov/).

Many of the process-oriented diagnostics modules (PODs) were contributed by members of the NOAA
[Model Diagnostics Task Force](https://cpo.noaa.gov/Meet-the-Divisions/Earth-System-Science-and-Modeling/MAPP/MAPP-Task-Forces/Model-Diagnostics-Task-Force) under MAPP support. Statements, findings or recommendations in these documents do
not necessarily reflect the views of NOAA or the US Department of Commerce.

## Citations

Guo, Huan; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna; Rand, Kristopher;
Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas; Underwood, Seth;
Vahlenkamp, Hans; Bushuk, Mitchell; Dunne, Krista A.; Dussin, Raphael; Gauthier, Paul PG; Ginoux, Paul; Griffies,
Stephen M.; Hallberg, Robert; Harrison, Matthew; Hurlin, William; Lin, Pu; Malyshev, Sergey; Naik, Vaishali;
Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Reichl, Brandon G; Schwarzkopf, Daniel M; Seman, Charles J;
Shao, Andrew; Silvers, Levi; Wyman, Bruce; Yan, Xiaoqin; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.;
Held, Isaac M; Krasting, John P.; Horowitz, Larry W.; Milly, P.C.D; Shevliakova, Elena; Winton, Michael; Zhao, Ming;
Zhang, Rong (2018). NOAA-GFDL GFDL-CM4 model output historical. Version YYYYMMDD[1].Earth System Grid Federation.
https://doi.org/10.22033/ESGF/CMIP6.8594

Krasting, John P.; John, Jasmin G; Blanton, Chris; McHugh, Colleen; Nikonov, Serguei; Radhakrishnan, Aparna;
Rand, Kristopher; Zadeh, Niki T.; Balaji, V; Durachta, Jeff; Dupuis, Christopher; Menzel, Raymond; Robinson, Thomas;
Underwood, Seth; Vahlenkamp, Hans; Dunne, Krista A.; Gauthier, Paul PG; Ginoux, Paul; Griffies, Stephen M.;
Hallberg, Robert; Harrison, Matthew; Hurlin, William; Malyshev, Sergey; Naik, Vaishali;
Paulot, Fabien; Paynter, David J; Ploshay, Jeffrey; Schwarzkopf, Daniel M; Seman, Charles J; Silvers, Levi;
Wyman, Bruce; Zeng, Yujin; Adcroft, Alistair; Dunne, John P.; Dussin, Raphael; Guo, Huan; He, Jian; Held, Isaac M;
Horowitz, Larry W.; Lin, Pu; Milly, P.C.D; Shevliakova, Elena; Stock, Charles; Winton, Michael; Xie, Yuanyu;
Zhao, Ming (2018). NOAA-GFDL GFDL-ESM4 model output prepared for CMIP6 CMIP historical.
Version YYYYMMDD[1].Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.8597

E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate and Weather Forecasting Models. BAMS, 100 (9),
1665–1686, [doi:10.1175/BAMS-D-18-0042.1](https://doi.org/10.1175/BAMS-D-18-0042.1).

## Disclaimer

This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric
Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’
basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or
Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable
Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark,
manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the
Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be
used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

## Contributors ✨
Thanks goes to [our code contributors](https://github.com/NOAA-GFDL/MDTF-diagnostics/graphs/contributors). <br>
Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/bitterbark"><img src="https://avatars.githubusercontent.com/u/30841536?v=4?s=100" width="100px;" alt="Dani Coleman"/><br /><sub><b>Dani Coleman</b></sub></a><br /><a href="https://github.com/NOAA-GFDL/MDTF-diagnostics/commits?author=bitterbark" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.gfdl.noaa.gov/john-krasting-homepage"><img src="https://avatars.githubusercontent.com/u/6594675?v=4?s=100" width="100px;" alt="John Krasting"/><br /><sub><b>John Krasting</b></sub></a><br /><a href="https://github.com/NOAA-GFDL/MDTF-diagnostics/pulls?q=is%3Apr+reviewed-by%3Ajkrasting" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/aradhakrishnanGFDL"><img src="https://avatars.githubusercontent.com/u/26334954?v=4?s=100" width="100px;" alt="Aparna Radhakrishnan"/><br /><sub><b>Aparna Radhakrishnan</b></sub></a><br /><a href="#ideas-aradhakrishnanGFDL" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

