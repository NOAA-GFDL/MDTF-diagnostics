# MDTF-diagnostics [![Build Status](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics.svg?branch=develop)](https://travis-ci.org/tsjackson-noaa/MDTF-diagnostics)

The MDTF diagnostic package is portable, extensible, usable, and open for contribution from the community. A goal is to allow diagnostics to be repeatable inside, or outside, of modeling center workflows. These are diagnostics focused on model improvement, and as such a slightly different focus from other efforts. The code runs on CESM model output, as well as on GFDL and CF-compliant model output.


The MDTF Diagnostic Framework consists of multiple modules, each of which is developed by an individual research group or user. Modules are independent of each other, each module:

1. Produces its own html file (webpage) as the final product
2. Consists of a set of process-oriented diagnostics
3. Produces a figures or multiple figures that can be displayed by the html in a browser

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


## Sample Output Webpage
[Latest complete package based on a CESM-CAM run](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save)


## Downloading and Running

- See the wiki for [installation instructions](https://github.com/NOAA-GFDL/MDTF-diagnostics/wiki/Detailed-installation-instructions).

- [Getting Started](http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/Getting_started_v2.0.pdf) (in the process of being updated)

- Observational and sample model data can be obtained by FTP from ftp://ftp.cgd.ucar.edu/archive/mdtf/ :

    - Pre-digested observational data: [MDTF_v2.0.obs_data.tar](ftp://ftp.cgd.ucar.edu/archive/mdtf/MDTF_v2.0.obs_data.tar) (160 MB) 

    - NCAR-CESM-CAM sample data: [model.QBOi.EXP1.AMIP.001.tar](ftp://ftp.cgd.ucar.edu/archive/mdtf/model.QBOi.EXP1.AMIP.001.tar) (13G)

    - NOAA-GFDL-CM4 sample data: [model.GFDL.CM4.c96L32.am4g10r8.tar](ftp://ftp.cgd.ucar.edu/archive/mdtf/model.GFDL.CM4.c96L32.am4g10r8.tar) (5G)

## Developer's Information
[Developer's Walk-through (v2.0)](http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/Developers_walkthrough_v2.0.pdf) (in the process of being updated)

## Disclaimer
This repository is a scientific product and is not an official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
