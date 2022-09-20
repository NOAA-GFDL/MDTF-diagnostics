.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Eddy Heat Fluxes
================================

Last update: 2022-05-03

This POD assesses the action of vertically propagating planetary-scale
stationary waves on the polar winter/spring stratosphere. The vertical component
of the Eliassen-Palm Flux is approximately proportional to the eddy heat flux,
v'T', where v is the meridional wind, and T is the temperature
(see Andrews et al., 1987). Thus, this POD uses the eddy heat flux at 100 hPa
as a proxy for the vertical flux of waves entering the stratosphere.

In general, when the time-integrated eddy heat flux in the lowermost
stratosphere is above/below normal, the polar stratospheric circulation should
be weaker/stronger than normal, with warmer/colder temperatures, respectively
(see Newman, et al., 2001). The eddy heat fluxes entering the stratosphere are
primarily driven by vertically propagating planetary-scale Rossby waves which
have both stationary and transient components. This POD calculates eddy heat
fluxes using monthly mean fields, and thus it primarily measures these
relationships for stationary waves (since in the monthly mean the transient
waves will be averaged out).

This POD makes two kinds of figures from provided model data:

- Scatterplots of early-season eddy heat fluxes with late-season polar cap
  temperatures
- Lag-correlation plots of polar cap geopotential heights at different pressure
  levels and months with early-season eddy heat fluxes at 100 hPa

These plots are made for both hemispheres; for the Northern Hemisphere, they
focus on the early (DJF or Dec) and late winter (JFM). For the SH, they focus
on the early (ASO or Sep) and late spring (SON).


Version & Contact info
----------------------
- Version/revision information: v1.0 (Apr 2022)
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

The observational data this POD uses is based on ERA5 reanalysis, and includes
pre-computed zonal mean eddy heat fluxes, temperatures, and geopotential heights
(i.e., they have dimensions of ``(time,level,lat)``) calculated from
monthly mean fields.


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

.. _ref-Newman:

    Newman, P. A., E. R. Nash, and J. E. Rosenfield, 2001: What controls the
    temperature of the Arctic stratosphere during the spring? JGR: A,
    106, 19999–20010, https://doi.org/10.1029/2000JD000061.


More about this POD
--------------------------

TODO: add details about the bootstrapping on scatterplots
TODO: add details about interpretation of heat flux in NH vs SH
