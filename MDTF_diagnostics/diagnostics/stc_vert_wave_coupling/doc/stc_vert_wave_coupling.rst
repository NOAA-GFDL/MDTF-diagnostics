.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Vertical Wave Coupling
=========================================================

Last update: 2023-03-10

This POD assesses the seasonality and extremes of vertical planetary wave 
coupling between the extratropical troposphere and stratosphere. It makes four 
kinds of figures from provided model data:

1. Climatological time series of planetary wave amplitudes in the 
   troposphere (500 hPa) and stratosphere (10 hPa)
2. NH winter and SH spring distributions of 50 hPa polar cap eddy heat fluxes
   (Shaw et al., 2014; Dunn-Sigouin and Shaw, 2015; England et al., 2016)
3. Composite maps of eddy geopotential heights and anomalies during 
   extreme heat flux days (Shaw et al., 2014; England et al., 2016)
4. Correlation coherence of planetary waves between 10 and 500 hPa
   (Randel 1987; Shaw et al., 2014)
   
All figures are made for both hemispheres. The plots from (2) and (3) focus 
primarily on the JFM and SON periods for the NH and SH, respectively, as 
these are generally the seasons with the greatest variability/extremes in 
heat fluxes. The plots from (1) and (4) show full-season perspectives. 

The figures from (1) and (2) together evaluate statistical characteristics 
of the planetary waves as a function of day of year and season. The figures 
from (3) show composite maps during extreme heat flux events 
relative to climatological stationary wave patterns, which help to assess 
the vertically-deep wave patterns associated with upward/downward propagation.
The figures from (4) demonstrate the lag times at which planetary waves in 
the stratosphere and troposphere are most coherent, with positive lag 
times indicative of upward propagation and negative lag times indicative 
of downward propagation.


Version & Contact info
----------------------

- Version/revision information: v1.0 (Mar 2023)
- Project PIs: Amy H. Butler (NOAA CSL) and Zachary D. Lawrence (CIRES / NOAA PSL)
- Developer/point of contact: Zachary Lawrence (zachary.lawrence@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

This POD is composed of three files, including the main driver script
``stc_vert_wave_coupling.py``, the functions that perform the diagnostic
computations in ``stc_vert_wave_coupling_calc.py``, and the functions that 
compile the specific POD plots in ``stc_vert_wave_coupling_plot.py``. 
The driver script reads in the necessary data, calls the computation
functions to perform Fourier decomposition, and sends the digested data 
to the plotting functions. The POD computes Fourier coefficients of 
10 and 500 hPa geopotential heights for the 60 degrees N/S latitudes 
and 45-80 degree latitude bands for zonal waves 1-3. It also computes
zonal wave decomposed polar cap (60-90 degrees lat) eddy heat fluxes at 
50 hPa. 

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes the same diagnostics described above. 
The observational data also includes eddy geoopotential height fields for 
the NH JFM seasons, and SH SON seasons, which are used to plot composite
maps during extreme heat flux events. 


Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- scipy
- xarray
- pandas
- matplotlib


Required model output variables
-------------------------------

The following daily mean fields are required:

- Temperature at 50 hPa, ``ta50`` as ``(time,lat,lon)`` (units: K)
- Meridional wind at 50 hPa, ``va50`` as ``(time,lat,lon)`` (units: m/s)
- Geopotential Height at 10 hPa, ``zg10`` as ``(time,lat,lon)`` (units: m)
- Geopotential Height at 500 hPa, ``zg500`` as ``(time,lat,lon)`` (units: m)


Scientific background 
---------------------
Wave motions in the polar stratosphere are primarily dominated by 
vertically propagating Rossby waves from the troposphere. Because of 
so-called "Charney-Drazin filtering", only the largest planetary scale 
waves are able to propagate into the stratosphere when there are westerly 
mean winds (Charney & Drazin, 1961; Andrews et al., 1987). As a result, 
vertical wave coupling between the troposphere and stratosphere follows a 
distinct seasonal cycle organized around the formation of the westerly 
stratospheric polar vortex in autumn (when waves can enter the stratosphere), 
and its breakdown in spring/early summer (when easterly winds prevent propagation).

The propagation characteristics of planetary waves are strongly dependent on 
the background mean flow, which can influence where/how these waves propagate. 
In some cases these can lead to events in which waves are reflected from the 
stratosphere back into the troposphere, which tend to occur most often in late 
winter in the NH and spring in the SH (Shaw et al., 2010). These reflected 
waves can directly influence the tropospheric circulation. 

Wave events in the stratosphere are associated with meridional fluxes of heat
that can be characterized by "eddy heat fluxes" (v'T', where v is the 
meridional wind, and T is the temperature, and primes denote deviations from
the zonal mean), which are proportional to the wave vertical group velocity
under linear wave theory (Andrews et al., 1987). Statistically extreme heat 
flux events thus represent extremes in wave propagation with vertically deep
planetary wave structures (Dunn-Sigouin and Shaw, 2015); extraordinarily high 
heat fluxes weaken and warm the polar vortex, whereas negative heat fluxes are 
generally associated with wave reflection that can dynamically cool and 
strengthen the vortex. 

Improper representation of the wave coupling between the troposphere and 
stratosphere can significantly influence the tropospheric stationary wave 
pattern, and be tied to climatological biases in the positions of
the tropospheric jets (Shaw et al., 2014b, England et al., 2016). Biases 
in the stratospheric circulation that can arise from, e.g., too little 
parameterized gravity wave drag can also affect how planetary waves 
propagate in the stratosphere and affect the occurrence of extreme heat 
flux events. Model characteristics such as the height of the model top, 
and the implementation (or lack of) sponge layers near the model top 
can additionally lead to unphysical excessive damping or reflection of waves,
which can subsequently influence biases in the tropospheric stationary wave
patterns, blocking frequencies, and annular mode timescales (Shaw & Perlwitz, 2010).


More about this POD
--------------------------

**Sign of eddy heat fluxes in NH vs SH**

In the Northern Hemisphere (NH), positive eddy heat fluxes represent 
poleward and upward wave fluxes. However, in the Southern Hemisphere 
(SH), the sign is flipped such that negative eddy heat fluxes represent 
the poleward and upward wave fluxes. This means that the SH polar cap 
eddy heat flux distributions will appear "flipped" compared to those 
for the NH. This also means that the extreme positive/negative heat 
flux events are in the opposite sense of those in the NH (i.e., 
extreme negative SH heat flux events are akin to extreme positive 
NH heat flux events).

**Tip about horizontal resolution of data**

Since this POD is primarily concerned with planetary scale waves, 
data with high horizontal resolution can be usefully downsampled 
without affecting results too much. This can speed up the MDTF data 
preprocessing and POD operation, while also decreasing the memory 
footprint.


References
----------

.. _ref-Andrews1987:

    Andrews, D. G., J. R. Holton, and C. B. Leovy, 1987:
    Middle Atmosphere Dynamics, Academic press, No. 40.

.. _ref-CharneyDrazin1961:

    Charney, J. G., and P. G. Drazin, 1961: Propagation of planetary‐scale 
    disturbances from the lower into the upper atmosphere. 
    Journal of Geophysical Research, 66(1), 83-109.

.. _ref-DunnSigouin2015:

    Dunn-Sigouin, E., and T. A. Shaw, 2015: Comparing and contrasting extreme 
    stratospheric events, including their coupling to the tropospheric circulation. 
    J. Geophys. Res. Atmos., 120: 1374– 1390. https://doi.org/10.1002/2014JD022116

.. _ref-England2016:

    England, M. R., T. A. Shaw, and L. M. Polvani, 2016: Troposphere-stratosphere 
    dynamical coupling in the southern high latitudes and its linkage to the 
    Amundsen Sea. Journal of Geophysical Research: Atmospheres, 121, 3776–3789,
    https://doi.org/10.1002/2015JD024254.

.. _ref-Hersbach2020:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803
    
.. _ref-Randel1987:
    
    Randel, W. J., 1987: A Study of Planetary Waves in the Southern Winter 
    Troposphere and Stratosphere. Part I: Wave Structure and Vertical 
    Propagation. J. Atmos. Sci., 44, 917–935, 
    https://doi.org/10.1175/1520-0469(1987)044<0917:ASOPWI>2.0.CO;2.
    
.. _ref-Shaw2010:
    
    Shaw, T. A., J. Perlwitz, and N. Harnik, 2010: Downward Wave Coupling between 
    the Stratosphere and Troposphere: The Importance of Meridional Wave Guiding 
    and Comparison with Zonal-Mean Coupling. J. Climate, 23, 6365–6381,
    https://doi.org/10.1175/2010JCLI3804.1.

.. _ref-ShawPerlwitz2010:
    
    Shaw, T. A., and J. Perlwitz 2010: The Impact of Stratospheric Model 
    Configuration on Planetary-Scale Waves in Northern Hemisphere Winter, 
    J. Clim., 23(12), 3369-3389. https://doi.org/10.1175/2010JCLI3438.1

.. _ref-Shaw2014:
   
    Shaw, T. A., J. Perlwitz, and O. Weiner, 2014: Troposphere-stratosphere
    coupling: Links to North Atlantic weather and climate, including their 
    representation in CMIP5 models. J. Geophys. Res.: Atmospheres, 
    119, 5864–5880, https://doi.org/10.1002/2013JD021191.
