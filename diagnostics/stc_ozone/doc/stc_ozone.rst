.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Stratospheric Ozone and Circulation
================================

Last update: 2023-01-13

This POD assesses coupling between stratospheric ozone and the large-scale 
circulation. Ozone-circulation coupling occurs during spring when sunlight 
returns to the polar region and the radiative influence of ozone anomalies 
drives changes to meridional temperature gradients and thus zonal winds, which
can then dynamically drive temperatures changes, which feedback onto ozone 
chemistry. For example, in years when the Antarctic ozone hole is larger (more
ozone loss) in early spring, the polar vortex stays stronger and persists 
later, leading to a later transition of the vortex at 50mb to its summertime
state, here defined as less than 5 (15) m/s in the NH (SH). This seasonal 
transition of the polar vortex is called the "final stratospheric warming". 
Because the Arctic rarely gets cold enough for severe chemical ozone loss, 
ozone-circulation coupling is primarily observed in the Southern Hemisphere, 
but this POD allows application to both hemispheres, as similar relationships 
may still occur in the Northern Hemisphere during extreme polar conditions. 

This POD makes four kinds of figures from provided model data:

- Scatterplots of early-spring polar cap stratospheric ozone with 
  late-spring zonal winds
- Scatterplots of early-spring polar cap stratospheric ozone with 
  final stratospheric warming day of year
- Lag-correlation plots of polar cap stratospheric ozone with 
  extratropical zonal winds for different pressure levels
- Linear trends of polar cap ozone, temperature, and extratropical
  zonal winds as a function of month and pressure level

These plots are made for both hemispheres, with a focus on spring. This season
is when sunlight returns to the polar region and when the strongest coupling 
between stratospheric ozone and the circulation appears. 


Version & Contact info
----------------------

- Version/revision information: v1.0 (Jan 2023)
- Project PIs: Amy H. Butler (NOAA CSL) and Zachary D. Lawrence (CIRES/NOAA PSL)
- Developer/point of contact: Amy Butler (amy.butler@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

This POD is driven by the file ``stc_ozone.py``, with a helper script of
``stc_ozone_defs.py``.
The driver script reads in the model fields, calculates zonal mean zonal winds
for user-defined latitude bands, and polar cap ozone and temperature, and
generates the plots. It also estimates the final warming DOY using 
monthly-mean zonal wind data at 60 degLat, as in Hardimann et al. 2011.

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes pre-computed zonal mean zonal winds,
temperatures, and ozone (i.e., they have dimensions of ``(time,lev,lat)``)
calculated from monthly mean fields.


Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- datetime
- scipy
- xarray
- matplotlib


Required model output variables
-------------------------------

The following monthly mean fields are required:

- Temperature, ``ta`` as ``(time,lev,lat,lon)`` (units: K)
- Zonal Winds, ``ua`` as ``(time,lev,lat,lon)`` (units: m/s)
- Ozone, ``o3`` as ``(time,lev,lat,lon)`` (units: mol mol-1)

References
----------

.. _ref-Andrews:

    Andrews, D. G., J. R. Holton, and C. B. Leovy, 1987:
    Middle Atmosphere Dynamics, Academic press, No. 40.

.. _ref-Hersbach:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803


More about this POD
--------------------------

**Sign of eddy heat fluxes in NH vs SH**

In the Northern Hemisphere (NH), positive eddy heat fluxes represent 
poleward and upward wave fluxes. However, in the Southern Hemisphere 
(SH), the sign is flipped such that negative eddy heat fluxes represent 
the poleward and upward wave fluxes. This means that the statistical 
relationships evaluated in this POD will generally be opposite-signed 
for the SH figures.

**Use of bootstrapping**

The scatterplots provided by this POD show the correlations between the 
100 hPa eddy heat flux and 50 hPa polar carp temperatures. In these figures, 
the parentheses next to the correlations contain the 95% bootstrap confidence 
interval on the correlations from resampling the available years 1000 times. 
These confidence intervals help to determine whether the correlations are 
significant; if 0 does not fall within the range of the confidence 
interval, the correlation can be said to be statistically significant. 
Furthermore, the bootstrap confidence interval in the observation plots
give a sense of the sampling variability in the historical record; if 
the model correlation falls outside the observed bootstrap confidence interval, 
it is fair to say the model has a too strong or too weak relationship.
