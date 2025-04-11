Surface Albedo Feedback
=======================

Last update: 9/10/2022

This POD calculates the top of atmosphere radiative impact of surface albedo changes associated with Arctic sea ice
loss under global warming. Four quantities are calculated:

- **Climatological surface albedo**: the ratio of upwelling to downwelling shortwave radiation at the surface expressed
  as a :math:`\%`.

- **Radiative sensitivity**: the change in reflected shortwave radiation at the top of the atmosphere
  (in :math:`W m^{-2}`) per  0.01 increase in surface albedo. This quantity, akin to a surface albedo radiative kernel,
  is calculated from the climatological radiative fluxes at the top of atmosphere and surface using a simplified
  shortwave radiation model. Higher values generally correspond to less cloudy mean states. The pattern is therefore
  similar to the all-sky radiative kernel, with higher values over Greenland, intermediate values over land and sea ice
  and lowest values over ocean. An advantage of this quantity is that it can be readily computed from the CERES EBAF
  data products. Models tend to reproduce the overall patteren but with an overall bias of +/-0.7 :math:`W m^{-2}`.
  The observational uncertainty is about 0.15 :math:`W m^{-2}`.

- **Ice sensitivity (also called Surface sensitivity)** : For the model this quantity is the change in monthly surface
  albedo normalized by the change in global mean monthly surface temperature change. For observations, this quantity is
  equal the change in sea ice concentration times the average albedo contrast between ocean and sea ice, normalized by
  the change in global mean temperature. Donohoe et al (2020) explains that these are comparable quantities. Both
  quantities have units that are in :math:`\% K^{-1}`. Arctic sea ice loss in the last few decades has rendered an
  observational estimate of this quantity that is strongly negative in coastal regions of the Arctic Ocean with typical
  values of -15 :math:`\% K^{-1}`. Most models look similar, but often the region of strongest sea ice declines is
  offset to the nouth or south of the correct location.

- **Radiative impact of sea ice loss** : the change in top of atmosphere radiation (positive downward) due to changes
  in surface albedo normalized by global mean surface temperature change, in :math:`W m^{-2} K^{-1}`. This quantity is
  equal to the product of the **Radiative sensitivity** and **Ice sensitivity**. The global and annual average of this
  quantity is equal to the ice albedo feedback of the Arctic. Like the ice sensitivity, the magnitude is greatest at the
  sea ice edge where sea ice loss has been most substantial with typical values of -30  :math:`W m^{-2} K^{-1}`.
  Most models look similar to observations, though sometimes the most negative values are offset to the north or south
  of the correct location.

All calculated quantities are averages over the boreal summer, defined as May, June, July and August. Change refers to
a trend over the time period of the data.

Version & Contact info
----------------------

- Version 1 (1/26/2021)
- PI (Cecilia Bitz, University of Washington, bitz@uw.edu)
- Developer/point of contact (Aaron Donohoe, University of Washington, adonohoe@u.washington.edu)
- Other contributors: Ed Blanchard, Wei Cheng, Lettie Roach  

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

Model climatological albedo and radiative sensitivity is calculated from the pre-industrial control simulation
climatological radiative fluxes at the top of atmosphere and surface. Observational calculations use the CERES EBAF
top of atmosphere and surface radiative fluxes (version 4.0) from <https://ceres.larc.nasa.gov/data/data-product-dois/>

Model ice sensitivity is calculated from the ratio of trends in the historical monthly mean spatial fields of surface
albedo (ratio of upwelling to downwelling surface shortwave fluxes) and global mean surface temperature. Observational
ice sensitivity estimates are from a developer provided file and are a blended product of historical trends in sea ice
concentrations provided by the National Snow and surface albedo provided by the Advanced Very High Resolution
Radiometer (AVHRR) Polar Pathfinder (APP-X).

The radiative sensitivity is the local product of the radiative sensitivity and surface sensitivity. 


Required programming language and libraries
-------------------------------------------


Python version 3, numpy, pandas, scipy, netCDF4, cftime, xarray, dask, esmpy, xesmf, matplotlib, cartopy

Required model output variables
-------------------------------

Monthly mean shortwave radiative fluxes at the top of atmosphere and surface (rsdt, rsut, rsds, rsus) and surface air
temperature (tas) from historical (1996-2014) integrations.

**IMPORTANT NOTE**

If the model dataset does not include a cell area file with the CMIP standard name `areacella`, or the
cell area file name does not have the format **{CASENAME}.{VARIABLE NAME}.{OUTPUT FREQUENCY}.nc**,
the user must define the pod_env_vars ``area_file_path`` with the **full path** to a file with a cell area,
and the ``area_var_name`` with the cell area variable name in the albedofb settings.jsonc file.

References
----------

1. A. Donohoe, E. Blanchard-Wrigglesworth, A. Schweiger and P.J. Rasch (2020): The Effect of Atmospheric
Transmissivity on Model and Observational Estimates of the Sea Ice Albedo Feedback.
*J. Climate*, **33** (12), 5743-5765,  <https://journals.ametsoc.org/view/journals/clim/33/13/jcli-d-19-0674.1.xml>
