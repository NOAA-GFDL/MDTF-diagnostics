Sea Ice Suite
================================

Last update: 1/27/2021

This POD calculates maps of the sea ice concentration (SIC)  for the period 1979-2014 for one ensemble member from a model compared to observations for the following quantities:

- **mean**: the mean (obviously) by month :math:`\%`.

- **trend**: the linear trend by month :math:`\% s^{-1}`.

- **standard deviation**: the standard deviation by month :math:`\%`.

- **standard deviation after detrending**: the standard deviation of detrended data by month :math:`\%`.

- **one-lag correlation**: the correlation at a lag of one month and one year of detrended data by month :math:`\fraction`.  For a one-month lag, the map for January shows the correlation of January and February. The map for February shows the correlation of February and March. And so forth. For a one-year lag, the map for January shows the correlation of January and January a year later. And so forth.

All calculated are maps shown for each month. Observations of sea ice concentration are from HadISST1.1 (Rayner et al, 2003).

Version & Contact info
----------------------

- Version 1 (1/26/2021)
- PI (Cecilia Bitz, University of Washington, bitz@uw.edu)
- Developer/point of contact (Cecilia Bitz, University of Washington, bitz@uw.edu)
- Other contributors: Lettie Roach  

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

The current package consists of two files:

1. seaice_suite_sic_mean_sigma.py which loads data, calculates statistics, regrids to grid of observations and plots everything.

2. seaice_MLD_stats.py contains functions for computing the linear regression and lagged correlation used in this POD and also our mixed-layer depth POD. 


Required programming language and libraries
-------------------------------------------

Python version 3, numpy, pandas, scipy, netCDF4, cftime, xarray, dask, esmpy, xesmf, matplotlib, cartopy

Required model output variables
-------------------------------

Monthly mean sea ice concentration on the original model grid for 1979-2014 from a historical simulation. 


References
----------

1. Roach, L., C.M. Bitz, et al. In preparation.

2. Rayner, N. A.; Parker, D. E.; Horton, E. B.; Folland, C. K.; Alexander, L. V.; Rowell, D. P.; Kent, E. C.; Kaplan, A. (2003) Global analyses of sea surface temperature, sea ice, and night marine air temperature since the late nineteenth century J. Geophys. Res.Vol. 108, No. D14, 4407 10.1029/2002JD002670  (pdf ~9Mb)
