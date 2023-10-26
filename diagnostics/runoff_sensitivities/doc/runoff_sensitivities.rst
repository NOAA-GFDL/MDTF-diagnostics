Runoff Sensitivities Diagnostic Documentation
=============================================

Last update: 10/31/2023

Runoff projections are essential for future water security. The Earth System Models (ESMs) are increasingly being utilized for future water resource risk assessment. However, the runoff projections based on ESMs are highly uncertain, in part due to differences in the land process representation among ESMs.

In this diagnostics, we try to measure the land process biases in ESMs. First, the land processes related to runoff projections in each ESM can be statistically emulated by quantifying the inter-annual sensitivity of runoff to temperature (temperature sensitivity) and precipitation (precipitation sensitivity) using multiple linear regression (:ref:`Lehner et al., 2019 <ref-Lehner>`). To represent the land process biases, the runoff senstivities for each ESM are compared to observational estimations, which is pre-calculated using same regression method. For the observational estimation, we used the GRUN-ENSEMBLE data - global reanalysis of monthly runoff using the maachine learning technique (:ref:`Ghiggi et. al., 2021 <ref-Ghiggi>`). The runoff sensitivities from CMIP5/6 models are also prepared to facilitate the comparison for new model development. The uncertainty ranges from internal variability, observational uncertainty, and inter-moel spread are provided for specific river basins to assess the significance of ESM biases.


Version & Contact info
----------------------

- Version/revision information: version 1 (10/31/2023)
- PI: Flavio Lehner, Cornell University, flavio.lehner@cornell.edu
- Developer/point of contact: Hanjun Kim, Cornell University, hk764@cornell.edu
- Other contributors: Andy wood, David Lawrence, Katie Dagon, Sean Swenson


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 


Functionality
-------------

The main driver code (runoff_sensitivities_diag.py) include all functions, codes for calculations and figures.

0) Functions are pre-defined for further analysis.
1) The codes will load data and do area average for 78 global river basins.
2) Water budget clousre (precipitaton - evaporation == runoff) in long term average is checked.
3) Every variables are averaged for water year with OBS-based start month which maximizes the inter-annual correlation between precipitaiton and runoff.
4) Using the pre-defined function "runoff_sens_reg", runoff sensitivities are calculated.
5) Calculated runoff sensitivities for target models are saved as .nc file.
6) The diagnostic figures will be plotted with the pre-calculated OBS and CMIP data.


Required programming language and libraries
-------------------------------------------

Python 3 is used to calculate and draw the figures.

- All libraries used in this diagnostic are available in MDTF conda environment "_MDTF_python3_base".
- Used libraries: "scipy", "numpy", "matplotlib", "netCDF4", "cartopy", "sklearn"    
- To deal with the shapefile, "cartopy.io.shapereader" and "matplotlib.path" is utilized.
- For multi-linear regression, "sklearn.linear_model" is utilized.    

**Caution**: In Oct. 2023, diagnostic does not work after update in "pydantic" library.
Below commands for downgrading "pydantic" solved the problem for us.

.. code-block:: restructuredtext
   
   conda activate _MDTF_base
   conda install -c conda-forge pydantic==1.10.12


Required model output variables
-------------------------------

The monthly historical simulations including period 1905-2005 are needed.
(Model outputs are assumed to be same with CMIP output.)

Target variables:
   - tas (surface air temperature, K), [time, lat, lon]
   - pr (precipitaiton, kg m-2 s-1), [time, lat, lon] 
   - hfls (latent heat flux, W m-2), [time, lat, lon]
   - mrro (runoff, kg m-2 s-1), [time, lat, lon]

lon-lat grids for 4 variables have to be same 
(In CMIP, there are some cases where grids are slightly different between land and atm variables. Checking/interpolation is recommended)


References
----------

.. _ref-Lehner: 

1.F. Lehner et al. (2019): The potential to reduce uncertainty in regional runoff projections from climate models. *Nature Climate Change*, **9** (12), 926-933, `doi:10.1038/s41558-019-0639-x <https://doi.org/10.1038/s41558-019-0639-x>`__.

.. _ref-Ghiggi: 

2.G. Ghiggi et al. (2021): G‐RUN ENSEMBLE: A multi‐forcing observation‐based global runoff reanalysis. *Water Resources Research*, **57** (5), e2020WR028787, `doi:10.1029/2020WR028787 <https://doi.org/10.1029/2020WR028787>`__.


More about this diagnostic
--------------------------

TBD


