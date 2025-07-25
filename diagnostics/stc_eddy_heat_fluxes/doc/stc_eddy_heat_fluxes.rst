.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Eddy Heat Fluxes
===================================================

Last update: 2022-09-26

This POD assesses the interaction of vertically propagating planetary-scale
stationary waves on the polar winter/spring stratosphere. The vertical component
of the Eliassen-Palm Flux is approximately proportional to the zonal mean eddy
heat flux, v'T', where v is the meridional wind, and T is the temperature
(see Andrews et al., 1987). Thus, this POD uses the eddy heat flux at 100 hPa
as a proxy for the vertical flux of waves entering the stratosphere.

In general, when the time-integrated eddy heat flux in the lowermost
stratosphere is above normal, the polar stratospheric circulation should
be weaker than normal with warmer temperatures; similarly, when the eddy heat
flux is below normal, the circulation should be stronger than normal with
colder temperatures (see Newman, et al., 2001). The eddy heat fluxes entering
the stratosphere are primarily driven by vertically propagating planetary-scale
Rossby waves which have both stationary and transient components. This POD
calculates eddy heat fluxes using monthly mean fields, and thus it primarily
measures these relationships for stationary waves (since in the monthly mean
the transient waves will be averaged out).

This POD makes two kinds of figures from provided model data:

- Scatterplots of early-season eddy heat fluxes with late-season polar cap
  temperatures
- Lag-correlation plots of polar cap geopotential heights at different pressure
  levels and months with early-season eddy heat fluxes at 100 hPa

These plots are made for both hemispheres; for the Northern Hemisphere (NH),
they focus on the early (DJF or Dec) and late winter (JFM). For the Southern
Hemisphere (SH), they focus on the early (ASO or Sep) and late spring (SON).
These months are when coupling between the stratosphere and troposphere are
most active in the respective hemispheres.

Polar stratospheric circulation variability is known to influence tropospheric
weather and climate (see Kidston et al., 2015). Different teleconnections, like those
related to ENSO, are sometimes considered to have stratospheric pathways through
which they act. These stratospheric teleconnection pathways are generally related
to how a given phenomenon influences stratospheric circulation variability, and
the subsequent coupling of the stratospheric state with the troposphere.

In a simple sense, this POD evaluates the "first step" of stratosphere-troposphere
coupling -- that is, the tropospheric influence on driving stratospheric circulation
anomalies. If a model underestimates or misrepresents this "upward coupling", they
can further miss or underestimate the impact of "downward coupling" related to the
stratosphere. Issues in modeling these processes can be related to model
characteristics such as vertical resolution, the height of the model lid, and
the representation of parameterized processes. 


Version & Contact info
----------------------

- Version/revision information: v1.0 (Jun 2022)
- Project PIs: Amy H. Butler (NOAA CSL) and Zachary D. Lawrence (CIRES / NOAA PSL)
- Developer/point of contact: Zachary Lawrence (zachary.lawrence@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

The entirety of this POD is contained in the file ``stc_eddy_heat_fluxes.py``.
This script reads in the model fields, calculates zonal mean eddy heat fluxes
and polar cap temperatures and geopotential heights, and generates the plots.

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes pre-computed zonal mean eddy
heat fluxes, temperatures, and geopotential heights (i.e., they have
dimensions of ``(time,level,lat)``) calculated from monthly mean fields.


Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- scipy
- xarray
- xesmf
- matplotlib


Required model output variables
-------------------------------

The following monthly mean fields are required:

- Temperature at 50 hPa, ``t50`` as ``(time,lat,lon)`` (units: K)
- Temperature at 100 hPa, ``t100`` as ``(time,lat,lon)`` (units: K)
- Meridional Winds at 100 hPa, ``v100`` as ``(time,lat,lon)`` (units: m/s)
- Geopotential Height, ``zg`` as ``(time,level,lat,lon)`` (units: m)

References
----------

.. _ref-Andrews:

    Andrews, D. G., J. R. Holton, and C. B. Leovy, 1987:
    Middle Atmosphere Dynamics, Academic press, No. 40.

.. _ref-Furtado:

    Furtado, J. C., J. L. Cohen, A. H. Butler, E. E. Riddle, and A. Kumar, 2015:
    Eurasian snow cover variability and links to winter climate in the CMIP5
    models. Clim Dyn, 45, 2591–2605, https://doi.org/10.1007/s00382-015-2494-4.

.. _ref-Hersbach:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803
    

.. _ref-Kidston:

    Kidston, J., A. Scaife, S. C. Hardiman, D. M. Mitchell, N. Butchart, M. P. Baldwin, and L. J. Gray, 2015:
    Stratospheric influence on tropospheric jet streams, storm tracks and surface weather.
    Nature Geosci 8, 433–440. https://doi.org/10.1038/ngeo2424
    
.. _ref-Newman:

    Newman, P. A., E. R. Nash, and J. E. Rosenfield, 2001: What controls the
    temperature of the Arctic stratosphere during the spring? JGR: A,
    106, 19999–20010, https://doi.org/10.1029/2000JD000061.


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
