.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

TC Seed Convective Organization Diagnostics
===============================

Last Update: 11/15/26

This POD calculates convective organization metrics for developing and non-developing tropical cyclone seed disturbances. 
These metrics include a simple fractional area of rainfall rates at and above the 95th Percentile and complex clustering metrics 
such as $L_{org}$, $I_{org}$, and $SCAI$. Snapshots are taken along the track of each developing and non-developing track, 
then each snapshot is composited by a function of its maximum wind speed (Vmax), and then metrics are calculated for each snapshot 
and then averaged within each wind intensity bin (6-9 m/s, 9-12 m/s, and 12-15 m/s). We compare results from  "observational data" ERA5 
and a climate model simulation.
.. Underline with '-'s to make a second-level heading.

Version & Contact info
----------------------

- Version Information: Version 1 (11/05/2026)
- PI: Allison Wing, Florida State University, awing@fsu.edu
- Developer: Jacob Hamil, Florida State University, jeh25d@fsu.edu
- Other Contributors: Grace Muesing, Suzana Camargo, Daehyun Kim, and Jihong Moon

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
.. Unless you've distributed your script elsewhere, you don't need to change this.

Functionality
-------------

Pre-calculated TC seed track data, in which the developing seeds are already matched to TC tracks, 
is required as an input to the POD as obs data (a NetCDF file). 

1. **Step 3a:** The code splits the tracks into Northern and Southern Hemisphere and into developing/non-developing.
2. **Step 3b:** For each snapshot along the track extracts convective and large-scale precipitation in 10x10 
degree boxes centered around the tracked seed center. The two precipitation types are summed them together 
to form total precipitation. Southern Hemisphere snapshots are flipped to orient poleward in the positive-y 
direction relative to the seed center to match the Northern Hemisphere snapshots (so poleward is in the 
positive-y direction in both hemispheres). We disregard any seed snapshot that has a central latitude greater than 30 degrees. 
3. **Step 3c:**Convective organization metrics are then computed for each snapshot. 

We composite the developing and non-developing seed snapshots and calculated organization metrics as a 
function of their maximum wind intensity using 3 separate bins at low intensities pre-TC genesis: 6-9 m/s, 9-12 m/s, 
and 12-15 m/s.  

Finally we plot spatial 10 x 10-degree maps of the average precipitation rate for each intensity bin 
and outline the 95th percentile rainfall rate for both the model and ERA5. We also plot the average convective organization 
metrics for each bin to make comparisons between developing and non-developing seeds in both the model and the observation.

Python Files called:

1. **Plotting_File.py** Creates the observation precipitation rate as function of Vmax spatial map for Observation and Model
2. **Convective_Org.py** Calculates $L_{org}$ and $I_{org}$ convective organization metrics

Required programming language and libraries
-------------------------------------------

* Python 3.11.7
* numpy, matplotlib, xarray, pandas, cftime, itertools, scipy, skimage, glob, intake, yaml

Required model output variables
-------------------------------

The following 3-D (time-lat-lon) variables are required:

3-D Variables:

Convective Precipitation Rate (PRECC), Units: m s-1, Frequency: 6-hourly instantaneous
Large-Scale Precipitaton Rate (PRECL), Units: m s-1, Frequency: 6-hourly instantaneous

In order to have sufficient samples, we recommend enough years of data to have at least 100 TCs, which is typically 2-5 years of simulation time depending on the resolution of the model.

In addition to model output, this POD requires pre-computed TC seed track data, provided as observational/ancillary data (OBS_DATA), plus the ERA5 reanalysis composite dataset used for comparison in the plots. 

References
----------

1. Moon, J., Kim, D., Wing, A. A., Camargo, S. J., Emlaw, G. N., Starr, J. C., & Cha, D.‐H. (2025). Tropical Cyclone Seed Disturbances in ERA5. Journal of Climate, 38(18), 4625–4639. https://doi.org/10.1175/JCLI‐D‐24‐0291.1
2. Tobin I, Bony S, Roca R. 2012. Observational Evidence for Relationships between the Degree of Aggregation of Deep Convection, Water Vapor, Surface Fluxes, and Radiation. Journal of Climate 25(20), doi:10.1175/jcli-d-11-00258.1, URL http://dx.doi.org/10.1175/JCLI-D-11-00258.1.
3. Biagioli G, Tompkins AM. 2023. Measuring Convective Organization. Journal of the Atmospheric Sciences 80(12), doi:10.1175/jas-d-23-0103.1, URL http://dx.doi.org/10.1175/JAS-D-23-0103.1.
4. Tompkins AM, Semie AG. 2017. Organization of tropical convection in low vertical wind shears: Role of updraft entrainment. Journal of Advances in Modeling Earth Systems 9(2), doi:10.1002/2016ms000802, URL http://dx.doi.org/10.1002/2016MS000802.
