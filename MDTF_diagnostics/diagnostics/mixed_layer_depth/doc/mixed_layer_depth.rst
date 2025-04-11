Mixed layer depth
================================

Last update: 1/27/2021

This POD calculates maps of the mean mixed layer depth (MLD) for the period 2000-2014 for one model ensemble member.

Some CMIP6 models provide the variable ``mlotst``, which is the mixed layer depth calculated instantaneously on the model timestep. To compare model output with monthly reanalysis products, we instead compute mixed layer depth from the monthly output salinity and temperature fields (``so`` and ``thetao``). We assume the salinity field ``so`` represents practical salinity.

We define the MLD as the depth where the density difference from the 10m depth value exceeds 0.03 kg m^-3 (de Boyer Montégut et al, 2004). Density is calculated from temperature and salinity using the Thermodynamic Equation Of Seawater - 2010 (TEOS-10) equation of state via the gsw package. The archived ``mlotst`` uses 0.125 kg m^-3 criterion according to the CMIP6 protocol for the instantaneous model fields, but we choose a higher criterion as the monthly fields are smoother than instantaneous fields. If this criteria is not exceeded in a given grid cell, we set the mixed layer depth to the ocean depth. 

We compare model results to the EN4 reanalysis (Good et al. 2013). This product provides practical salinity and potential temperature, and the mixed layer depth is computed using the same approach as the models. 

Version & Contact info
----------------------

- Version 1 (1/26/2021)
- PI (Cecilia Bitz, University of Washington, bitz@uw.edu)
- Developer/point of contact (Lettie Roach, University of Washington, lroach@uw.edu)
- Other contributors: Cecilia Bitz 

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

The current package consists of one file:

1. mixed_layer_depth.py which loads data, calculates MLD, regrids to grid of observations and plots monthly means.



Required programming language and libraries
-------------------------------------------

Python version 3, numpy, pandas, scipy, netCDF4, cftime, xarray, dask, esmpy, xesmf, matplotlib, cartopy, gsw

Required model output variables
-------------------------------

Monthly mean salinity and temperature on vertical levels on the original model grid for 1979-2014 from a historical simulation. The vertical coordinate must be in units of meters.


References
----------

1. Roach, L., C.M. Bitz, et al. In preparation.

2. de Boyer Montégut, C., G. Madec, A. S. Fisher, A. Lazar, and D. Ludicone (2004), Mixed layer depth over the global ocean: An examination of profile data and a profile-based climatology, J. Geophys. Res., 109, 20, doi: 10.1029/2004JC002378.

3. Good, S. A., M. J. Martin and N. A. Rayner, 2013. EN4: quality controlled ocean temperature and salinity profiles and monthly objective analyses with uncertainty estimates, Journal of Geophysical Research: Oceans, 118, 6704-6716, doi:10.1002/2013JC009067
