# Convective Transition Diagnostic Package

Last update: 5/31/2020

The convective transition diagnostic package computes statistics that relate precipitation to measures of tropospheric temperature and moisture, as an evaluation of the interaction of parameterized convective processes with the large-scale environment. Here the basic statistics include the conditional average and probability of precipitation, PDF of column water vapor (CWV) for all events and precipitating events, evaluated over tropical oceans. The critical values at which the conditionally averaged precipitation sharply increases as CWV exceeds the critical threshold are also computed (provided the model exhibits such an increase).

## Version & Contact info

- Version 2 31-May-2020 Yi-Hung Kuo (UCLA)
- PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
- Current developer: Yi-Hung Kuo (yhkuo@atmos.ucla.edu)
- Contributors: K. A. Schiro (UCLA), B. Langenbrunner (UCLA), F. Ahmed (UCLA), C. Martinez (UCLA), and C.-C. (Jack) Chen (NCAR)

### Open source copyright agreement

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

## Functionality

The currently package consists of following functionalities:

1. Convective Transition Basic Statistics (convecTransBasic.py)
2. Convective Transition Critical Collapse (convecTransCriticalCollape.py)
3. (\*) Precipitation Contribution Function (cwvPrecipContrib.py)

More on the way... (\* under development)

As a module of the MDTF code package, all scripts of this POD can be found under the [convective_transition_diag](https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/master/var_code/convective_transition_diag) directory and digested observational data under `inputdata/obs_data/convective_transition_diag`.

## Required programming language and libraries

The is POD is written in Python 2, and requires the following Python packages: os, glob, json, Dataset, numpy, scipy, matplotlib, networkx, warnings, numba, & netcdf4. The environment necessary for running this POD will be provided by the automated installation script for the MDTF Framework. Note that running this POD outside the provided environment may result in figures different from the [samples](http://www.cgd.ucar.edu/cms/bundy/Projects/diagnostics/mdtf/mdtf_figures/MDTF_QBOi.EXP1.AMIP.001.save/convective_transition_diag/convective_transition_diag.html) because of different matplotlib version.

## Required model output variables

The following three 3-D (lat-lon-time) high-frequency (at least 6-hrly) model fields are required:
1. Precipitation rate (units: mm s<sup>-1</sup> = kg m<sup>-2</sup>s<sup>-1</sup>; 6-hrly or shorter avg.)
2. Column-integrated water vapor (CWV, or precipitable water vapor; units: mm = kg m<sup>-2</sup>)
3. Mass-weighted column average temperature (units: K) or column-integrated saturation humidity (units: mm = kg m<sup>-2</sup>), column: 1000-200 hPa by default. Since these variables are not standard model output, this POD will automatically calculate them if the following 4-D (lat-lon-pressure-time) model field is available:
4. Air temperature (units: K)

## Reference

1. Kuo, Y.-H., J. D. Neelin, and C. R. Mechoso, 2017: Tropical Convective Transition Statistics and Causality in the Water Vapor-Precipitation Relation. *J. Atmos. Sci.*, **74**, 915-931, https://doi.org/10.1175/JAS-D-16-0182.1.
2. Kuo, Y.-H., K. A. Schiro, and J. D. Neelin, 2018: Convective transition statistics over tropical oceans for climate model diagnostics: Observational baseline. *J. Atmos. Sci.*, **75**, 1553-1570, https://doi.org/10.1175/JAS-D-17-0287.1.
3. Kuo, Y.-H., and Co-authors, 2020: Convective Transition Statistics over Tropical Oceans for Climate Model Diagnostics: GCM Evaluation. *J. Atmos. Sci.*, **77**, 379-403, https://doi.org/10.1175/JAS-D-19-0132.1.

## More about this diagnostic

In this section, you can go into more detail on the science behind your 
diagnostic. It's especially helpful if you're able to teach users how to use 
your diagnostic's output, by showing how to interpret example plots.

Instead of doing that here, we provide more examples of markdown syntax that 
you can customize as needed.

A good online editor that gives immediate feedback is at <https://dillinger.io/>. 
Also see this [cheat sheet](https://www.markdownguide.org/cheat-sheet/) and 
GitHub's [reference](https://guides.github.com/features/mastering-markdown/).

### Additional references

4. Sahany, S., J. D. Neelin, K. Hales, and R. B. Neale, 2012: Temperature–moisture dependence of the deep convective transition as a constraint on entrainment in climate models. *J. Atmos. Sci.*, **69**, 1340–1358, https://doi.org/10.1175/JAS-D-11-0164.1.
5. Wentz, F.J., C. Gentemann, K.A. Hilburn, 2015: Remote Sensing Systems TRMM TMI Daily, 3-Day Environmental Suite on 0.25 deg grid, Version 7.1. Remote Sensing Systems, Santa Rosa, CA. Available online at https://www.remss.com/missions/tmi.
6. Zhao., M., and Coauthors, 2018a: The GFDL Global Atmosphere and Land Model AM4.0/LM4.0 - Part I: Simulation Characteristics with Prescribed SSTs. *Journal of Advances in Modeling Earth Systems*, **10(3)**, https://doi.org/10.1002/2017MS001208.
7. Zhao., M., and Coauthors, 2018b: The GFDL Global Atmosphere and Land Model AM4.0/LM4.0 - Part II: Model Description, Sensitivity Studies, and Tuning Strategies. *Journal of Advances in Modeling Earth Systems*, **10(3)**, https://doi.org/10.1002/2017MS001209.

