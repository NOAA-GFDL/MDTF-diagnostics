Eulerian Storm Track
====================

.. rst-class:: center

Jeyavinoth Jeyaratnam\ |^1| and James F. Booth\ |^1|

.. rst-class:: center

|^1|\ The City College of New York, CUNY, New York

.. rst-class:: center

Last update: 10/9/2020

Description
-----------

Synoptic variability in the atmosphere can be isolated by filtering atmospheric data temporally,
in a manner that removes the diurnal and the greater than weekly variability (:ref:`Blackmon et al. 1976 <ref-1>`). 
Then, the standard deviation of the filtered data at each latitude and longitude can be
interpreted as the climatological baroclinic wave activity, which, for historical reasons, is termed
the storm tracks (:ref:`Wallace et al. 1988 <ref-4>`). Because these storm tracks are calculated for each latitude-
longitude point using time-series data, rather than tracking individual storms, they are sometimes
referred to as the Eulerian storms tracks – as opposed to the Lagrangian storm tracks. The storm
tracks are a large-scale metric for the skill in the model representation of baroclinic wave behavior
– which includes extratropical cyclones. Storm track location, seasonality and intensity correlate
very strongly with transient poleward energy transport (:ref:`Chang et al. 2002<ref-3>`).

Storm tracks can be evaluated with atmospheric data such as meridional wind or geopotential
height (see :ref:`Chang et al. 2002 <ref-3>` for a comparison of many different fields). :ref:`Booth et al. (2017) <ref-2>` show
that storm track strength – defined as the area-average of the storm track over an ocean basin, using
meridional winds at 850 hPa correlate very strongly with the storm track at 500 hPa. This is true
for interannual variability and for a comparison across multiple models. Therefore, the metric in
this diagnostic calculates the storm track using meridional winds at 850 hPa. The nomenclature
and calculation follow that of :ref:`Booth et al. (2017) <ref-2>`.

To isolate the synoptic timescale, this algorithm uses 24-hour differences of daily-averaged
data. Using daily averages removes the diurnal cycle and the 24-hour differencing removes
variability beyond 5 days (:ref:`Wallace et al. 1988 <ref-4>`). After filtering the data to create anomalies, the
variance of the anomalies is calculated across the four seasons for each year. Then the seasonal
variances are averaged across all years. For the first year in the sequence, the variance for JF is
calculated and treated as the first DJF instance. For the final December in the sequence is not used
in the calculation.

The maximum strength of the Eulerian storm track can be sensitive to the data’s spatial
resolution. To exemplify this fact, we have included the map view of the storm track using ERA-
Interim and ERA5 reanalysis data at two different resolutions (1.5\ |^o| horizontal resolution for ERA-
Interim data and 1\ |^o| resolution for ERA5 data). For this reason, we do not include a difference plot
of the lat/lon storm track maps. Instead, for a side-by-side comparison, we have generated a zonal
mean of the storm tracks.


Version & Contact Information
-----------------------------

- Version 1.0 :: 10/09/2020
- Current Developer: Jeyavinoth Jeyaratnam (jjeyaratnam@ccny.cuny.edu), CUNY
- PI: James F. Booth (jfbooth@ccny.cuny.edu), CUNY


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The POD contains the following files which perform various functionalities:

#. Eulerian_storm_track.py is the main driver code.
#. Eulerian_storm_track util.py is the code that computes the statistics.
#. plotter.py is the code used to create the plots.
#. Eulerian_storm_track_obs.py is an internal code used to preprocess the observations and convert them to NetCDF files.


Required programming language and libraries
-------------------------------------------

This package is run using Python 3, and requires the following Python packages:

- os
- numpy
- xarray
- netCDF4
- matplotlib
- cartopy
- basemap

Required model output variables
-------------------------------

The following 3D (time, lat, lon) model fields are required:

- V850 (units: m/s, daily)

References
----------

   .. _ref-1: 

1. Blackmon, M.L., 1976: A climatological spectral study of the 500mb geopotential height of the Northern Hemisphere. J. Atmos. Sci., 33, 1607-1623.
   
   .. _ref-2: 

2. Booth J. F., Y.-K. Kwon, S. Ko, J. Small, R. Madsek, 2017: Spatial Patterns and Intensity of the Surface Storm Tracks in CMIP5 Models. Journal of Climate, 30, 4965–4981.

   .. _ref-3: 

3. Chang, E., S. Lee and K. Swanson, 2002: Storm track dynamics. J. Climate, 15, 2163-2183.

   .. _ref-4: 

4. Wallace, J.M., G-H Lim, M. L Blackmon, 1988: Relationship between cyclone tracks, anticyclone tacks and baroclinic waveguides. J. Atmos. Sci., 45, 439-462.

.. |^o| replace:: \ :sup:`o`\ 
.. |^1| replace:: \ :sup:`1`\ 
.. |^2| replace:: \ :sup:`2`\ 
.. |^3| replace:: \ :sup:`3`\ 
.. |^-1| replace:: \ :sup:`-1`\ 
.. |^-2| replace:: \ :sup:`-2`\ 
.. |^-3| replace:: \ :sup:`-3`\ 
