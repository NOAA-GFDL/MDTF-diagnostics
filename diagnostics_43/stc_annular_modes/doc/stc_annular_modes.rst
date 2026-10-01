.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Annular Modes
================================================

Last update: 2023-03-28

This POD assesses characteristics of the annular modes as a function of 
day of year. It makes four kinds of figures from provided model data:

1. EOF1 pattern plots on standard pressure levels, representing the 
   annular mode structures throughout the troposphere and stratosphere.
   (cf., Gerber et al. 2010, Fig. 4; Simpson et al., 2011, Fig. 1)
2. Annular mode interannual standard deviation (cf., Gerber et al., 2010,
   Fig. 7)
3. Annular mode e-folding timescales (or "persistence"; 
   cf., Gerber et al. 2010, Fig. 8; Kidston et al., 2015, Fig. 1)
4. Annular mode predictability (cf., Gerber et al., 2010, Fig. 9)
   
All figures are made for both hemispheres. This POD also outputs the
computed annular mode indices and EOF structures as netcdf files. 

The figure from (1) should always be viewed to verify the spatial structure 
of the annular modes; if the spatial patterns for model data do not match the 
observations (or the figures in the papers referenced above), then the 
1st EOF may not represent an "annular mode"-like pattern, which means caution 
is warranted for interpreting the other figures and the digested output data.

The figures from (2) highlight the seasonal cycle in annular mode variability.
The figures from (3) show estimates of the seasonally varying persistence of 
the annular modes. Lastly, the figures from (4) demonstrate what fraction
of the variance of the annular mode at a given pressure level (default 850 hPa)
can be "predicted" using a persistence forecast of the annular mode at other 
levels (see Gerber et al., 2010 for full details).


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
``stc_annular_modes.py``, the functions that perform the diagnostic
computations in ``stc_annular_modes_calc.py``, and the functions that 
compile the specific POD plots in ``stc_annular_modes_plot.py``. 
The driver script reads in the necessary data, calls the computation
functions to perform the anomaly calculations, the EOF analysis, and 
annular mode diagnostics.

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020) zonal mean geopotential heights.

By default, the annular modes are computed for input model data as 
described in Gerber et al., 2010; in short, for every timestep, the 
global mean geopotential height is removed, and then a 60 day low-pass 
filter is applied across the daily data before a 30 year low-pass filter 
is applied across the days of year. This process is intended to remove 
a slowly varying climatology that helps to remove trends, such 
that the anomalies represent "true" variations. The annular modes are 
then assumed to be the 1st EOF of these daily anomalies between 20-90 
degrees latitude (for the Northern and Southern hemispheres). 

Note: Users can opt to adjust this POD's settings.jsonc file to instead 
compute the annular modes using a "simple" method, which computes 
anomalies by removing the global mean heights, removing a standard 
climatology, and linearly detrending the anomalies across the days of year. 
However, the pre-digested observational data provided with this POD are 
computed using the "gerber" method. 

Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- scipy
- xarray
- pandas
- eofs
- matplotlib


Required model output variables
-------------------------------

Only one daily mean field on pressure levels is required:

- Zonal Mean Geopotential Height, ``zg`` as ``(time,lev,lat)`` (units: m)

Ideally, this data should span pressure levels between 1000 and 1 hPa. 
Results will be plotted for this range of levels. However, absent/missing 
data will properly have blanks in the output figures.


Scientific background 
---------------------
The Northern and Southern Annular Modes (NAM/SAM) are the dominant 
large-scale circulation variability patterns of the extratropics
(Thompson and Wallace, 2000). They represent fluctuations of mass into 
or out of the polar cap regions, manifesting as patterns of similarly 
signed height/pressure anomalies in the polar cap surrounded by an 
opposite signed ring of anomalies in the midlatitudes (hence their 
"annular" appearance). 

The annular modes also characterize a coupled pattern of variability 
between the troposphere and stratosphere (Gerber et al., 2010; Kushnir 2010; 
Simpson et al., 2011). In the troposphere, the NAM/SAM roughly correspond to 
the strength and latitudinal position of the mid-latitude jets; in the wintertime 
stratosphere, they represent the strength of the stratospheric polar vortex. 
During these winter periods, the state of the stratosphere can have a 
"downward influence" on the tropospheric annular mode state, whereby anomalies 
in the strength of the stratospheric vortex can drive persistent same-signed 
tropospheric annular mode phases (Baldwin and Dunkerton 2001). The resultant 
influence on the position of the jets can further impact regional shifts 
in large-scale weather patterns. Thus, while the tropospheric annular modes 
can evolve year-round, the stratosphere-troposphere coupling that occurs during 
winter/spring drives a distinct seasonal cycle in tropospheric annular 
mode variance and persistence (Gerber et al., 2010; Simpson et al. 2011; 
Schenzinger & Osprey 2015). 

In the Northern Hemisphere, the aforementioned sort of "downward influence" 
is generally organized around midwinter extreme vortex events such as
sudden stratospheric warmings and vortex intensifications. However, in the 
Southern Hemisphere, stratosphere-troposphere annular mode coupling is 
typically organized around the seasonal breakdown of the polar vortex 
in late spring. As a result, the seasonal cycle in annular mode variability
and persistence tends to occur close in time in both hemispheres, maximizing 
around December-February in the Northern Hemisphere, and October-December 
in the Southern Hemisphere (Kidston et al., 2015).

A misrepresentation of stratospheric variability in models can lead to 
biases in annular mode coupling (Gerber et al., 2010; Simpson et al., 2011). 
For instance, a lack of SSWs or too late final warmings can shift the seasonal 
cycle in annular mode variance/persistence too late in models relative to 
observations. Processes that affect stratospheric polar vortex variability in 
models (e.g., model lid height, gravity wave parameterizations, interactive 
chemistry, etc.), can thus potentially affect the representation of the tropospheric 
jets, regional weather, and the statistics of temperatures and precipitation 
through the annular mode "pathway". However, it is also possible for model biases 
in the annular modes to arise separately from the stratosphere due to poorly 
represented processes such as low-level orographic drag (Pithan et al., 2016). 


References
----------

.. _ref-ThompsonWallace2000:

   Thompson, D. W. J., and J. M. Wallace, 2000: Annular Modes in the Extratropical 
   Circulation. Part I: Month-to-Month Variability. J. Climate, 13, 
   1000–1016, https://doi.org/10.1175/1520-0442(2000)013<1000:AMITEC>2.0.CO;2.
   
.. _ref-BaldwinDunkerton2001:

    Baldwin, M. P., and T. J. Dunkerton, 2001: Stratospheric harbingers of anomalous 
    weather regimes. Science, 294(5542), 581-584, https://doi.org/10.1126/science.1063315

.. _ref-BaldwinThompson2009:

    Baldwin, M.P. and D.W.J. Thompson, 2009: A critical comparison of 
    stratosphere–troposphere coupling indices. Q.J.R. Meteorol. Soc., 
    135: 1661-1672, https://doi.org/10.1002/qj.479

.. _ref-Gerber2010:

    Gerber, E. P., et al. 2010: Stratosphere-troposphere coupling and annular mode 
    variability in chemistry-climate models, J. Geophys. Res., 115, D00M06, 
    https://doi.org/10.1029/2009JD013770.

.. _ref-Kushnir2010:

    Kushner, P. J., 2010: Annular modes of the troposphere and stratosphere. 
    The Stratosphere: Dynamics, Transport, and Chemistry, 190, 59-91., 
    https://doi.org/10.1029/GM190

.. _ref-Simpson2011:

    Simpson, I. R., P. Hitchcock, T. G. Shepherd, and J. F. Scinocca, 2011: 
    Stratospheric variability and tropospheric annular-mode timescales, 
    Geophys. Res. Lett., 38, L20806, https://doi.org/10.1029/2011GL049304.

.. _ref-Kidston2015:

    Kidston, J., et al. 2015: Stratospheric influence on tropospheric 
    jet streams, storm tracks and surface weather. Nature Geosci 8, 433–440, 
    https://doi.org/10.1038/ngeo2424

.. _SchenzingerOsprey2015:

    Schenzinger, V., and S. M. Osprey, 2015: Interpreting the nature of Northern 
    and Southern Annular Mode variability in CMIP5 Models, J. Geophys. Res. Atmos., 
    120, 11,203– 11,214, https://doi.org/10.1002/2014JD022989.

.. _Pithan2016:
    
    Pithan, F., T. G. Shepherd, G. Zappa, and I. Sandu 2016: Climate model biases in 
    jet streams, blocking and storm tracks resulting from missing orographic drag, 
    Geophys. Res. Lett., 43, 7231–7240, https://doi.org/10.1002/2016GL069551.

.. _ref-Hersbach2020:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803
