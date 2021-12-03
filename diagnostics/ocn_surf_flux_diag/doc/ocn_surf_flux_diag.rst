Ocean Surface Latent Heat Flux Diagnostic Documentation 
================================

Last update: 10/15/2021

Tropical intra-seasonal (20-100 day) convection regulates weather patterns 
globally through extratropical teleconnections. Surface latent heat fluxes 
help maintain tropical intra-seasonal convection and the Madden-Julian 
oscillation by replenishing column water vapor lost to precipitation. 
Latent heat fluxes estimated using surface meteorology from moorings or 
satellites and the COARE3.0 bulk flux algorithm suggest that latent heat 
fluxes contribute about 8% of the intra-seasonal precipitation anomaly over 
the Indian and western tropical Pacific Oceans [Dellaripa and Maloney, 2015, 
Bui et al., 2020].

we use in-situ data from TAO/TRITON/RAMA to create a location-based latent 
heat flux matrix determined by specific humidity deficiency at the surface layer 
(dq) and surface wind speed (sfcWind). By comparing the matrix between observation 
and models/reanalysis, we reveal where model/reanalysis latent heat flux biases are 
largest in dq-sfcWind space. The latent heat flux biases shown in the matrix 
demonstrate dependence on both sfcWind and dq. An offline latent heat bias correction
can be performed on model simulations based on the bias latent heat fluxes matrix 
as a function of dq and sfcWind.


Version & Contact info
----------------------

- Version/revision information: version 1 (10/15/2021)
- PI (Charlotte A. DeMott, Colorado State University, charlotte.demott@colostate.edu)
- Developer/point of contact (Chia-Wei Hsu, Colorado State University, Chia-Wei.Hsu@colostate.edu)


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

The main script generates the Latent heat flux matrix and bias matrix.

Python function used
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- groupby_variables.bin_2d : The function is written to bin the variable (target_var) in a xr.Dataset
                             based on two other variables (bin1_var, bin2_var) in the same xr.Dataset. 
                             The function calculate the mean, std, and count values of the target_var 
                             after binning.
                             
- model_read.regional_var  : The function is written to read the model output and required varaibles.
                             The function also crop the data based on the user set time period and 
                             region. Two varibales is calculated in this function 1) saturation specific  
                             humidity near surface (determined by surface temperature and surface pressure)
                             and 2) dq which represent the vertical difference of specific humidity 
                             near surface. 
                             
- obs_data_read.tao_triton : The function is written to read the observational data and required varaibles
                             from the TAO/TRITON array.
                             The function also crop the data based on the user set time period and 
                             region. Two varibales is calculated in this function 1) saturation specific  
                             humidity near surface (determined by surface temperature and surface pressure)
                             and 2) dq which represent the vertical difference of specific humidity 
                             near surface.
                             
- obs_data_read.rama       : The function is written to read the observational data and required varaibles
                             from the RAMA array.
                             The function also crop the data based on the user set time period and 
                             region. Two varibales is calculated in this function 1) saturation specific  
                             humidity near surface (determined by surface temperature and surface pressure)
                             and 2) dq which represent the vertical difference of specific humidity 
                             near surface.


Required programming language and libraries
-------------------------------------------

The programming language is python version 3 or up. The third-party libraries
include "matplotlib", "xarray", "metpy","numpy","scipy". The conda environment
need to be set to _MDTF_ocn_surf_flux_diag.

Required model output variables
-------------------------------

With daily frequency from the model output. This diagnostic needs

input atmosphere model variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    1. 'huss'    : Surface 2m Humidity (kg kg-1)
    2. 'ts'      : Skin Temperature (SST for open ocean; K)
    3. 'sfcWind' : Near-Surface Wind Speed (10 meter; m s-1)
    4. 'psl'     : Sea Level Pressure (Pa)
    5. 'hfls'    : Surface Upward Latent Heat Flux (W m-2 and positive upward)
    6. 'pr'      : Precipitation (kg m-2 s-1)

The script is written based on the CESM2-CMIP6 daily data download hosted by WCRP.

The dimension of all variable is 3-D with (time,lat,lon) in dimension and 2-D 
array for lat and lon as coordinate.


Required observational data 
-------------------------------

With daily frequency from the observational data. This diagnostic needs

input observational variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    1. 'RH'           : Relative Humidity (%)
    2. 'SST'          : Sea Surface Temperature (for open ocean; K)
    3. 'WindSpeed10m' : Near-Surface Wind Speed (10 meter; m s-1)
    4. 'SLP'          : Sea Level Pressure (Pa)
    5. 'Latent'       : Surface Upward Latent Heat Flux (W m-2 and positive upward)
    6. 'airT'         : Near Surface Temperature (K)
   

data access :
**********************
     
All variables can be downloaded from PMEL NOAA hosted website
`https://www.pmel.noaa.gov/tao/drupal/flux/index.html  <https://www.pmel.noaa.gov/tao/drupal/flux/index.html>`_
    


References
----------

.. _ref-Hsu: 
   
1. C.-W. Hsu et al. (2020): Ocean Surface Flux Algorithm Effects on Tropical 
    Indo-Pacific Intraseasonal Precipitation. *GRL*, under review.



More about this diagnostic
--------------------------

Surface latent heat flux from ocean to the atmosphere is one of the important processes that provides water vapor and energy to the daily tropical rainfall. A visually intuitive latent heat flux diagnostic is proposed to better understand the model shortfall on its latent heat flux representation. This diagnostic allows a simple assessment of model latent heat flux biases arising either from biases in water vapor or surface wind speed as well as other empirical coefficients in the model. Sample POD result shows that, compared to ''observed'' fluxes also estimated from water vapor and surface wind speed measured at tropical moorings, tropical latent heat fluxes in the NCAR CEMS2 models are significantly overestimated when extreme water vapor or surface wind speed happens.
