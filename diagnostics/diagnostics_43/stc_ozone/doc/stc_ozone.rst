.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Stratospheric Ozone and Circulation
======================================================================

Last update: 2023-01-31

This POD assesses coupling between stratospheric ozone and the large-scale 
circulation. Ozone-circulation coupling occurs during spring when sunlight 
returns to the polar region and the radiative influence of ozone anomalies 
drives changes to meridional temperature gradients and thus zonal winds, which
can then dynamically drive temperatures changes, which feedback onto ozone 
chemistry. For example, in years when the Antarctic ozone hole is larger (more
ozone loss) in early spring, the polar vortex stays stronger and persists 
later, leading to a later transition of the vortex at 50 mb to its summertime
state, here defined zonal-mean zonal winds at 60 degLat as less than 5 (15) 
m/s in the NH (SH). This seasonal transition of the polar vortex is called 
the "final stratospheric warming". Because the Arctic rarely gets cold enough
for severe chemical ozone loss, ozone-circulation coupling is primarily observed
in the Southern Hemisphere, but this POD allows application to both hemispheres, 
as similar relationships may still occur in the Northern Hemisphere during extreme 
polar conditions. 

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
between stratospheric ozone and the circulation appears. The metrics used are 
designed to focus on processes with known biases, particularly in the 
Southern Hemisphere. For example, the scatterplots showing late-spring zonal
winds or final stratospheric warming day of year can be used to compare the 
mean values of these quantities in the model with reanalysis. In the SH, CMIP models
tend to have too late of final warming, or equivalently, too strong of late spring 
polar vortex winds (Wilcox et al., 2013). The POD outputs some of these metrics 
so that multi-model comparison can be performed.

Note that many CMIP6 models do not have interactive stratosheric chemistry, and 
instead use prescribed ozone provided by Checa-Garcia et al. (2018a,b), except for
three models that instead use prescribed ozone from simulations performed by the 
CESM-WACCM model (CESM2, CESM2-FV2, NorESM2). Details of ozone in CMIP6 models 
can be found in Keeble et al. (2021). In models with prescribed ozone, the ozone
forcing will still influence the circulation, but the circulation changes cannot 
feedback onto ozone, which may influence the degree to which they capture the full 
response in both hemispheres (Haase et al., 2020, Friedel et al. 2022).


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
monthly-mean zonal wind data at 60 degLat, as in Hardimann et al. (2011).

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

.. _ref-Hardimann:

    Hardiman, S. C., et al., 2011: Improved predictability of the troposphere 
    using stratospheric final warmings, J. Geophys. Res., 116, D18113, 
    doi:10.1029/2011JD015914

.. _ref-Hersbach:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803

.. _ref-Checa-Garcia_a:

    Checa-Garcia, R: CMIP6 Ozone forcing dataset, 2018: supporting information, Zenodo,
    https://doi.org/10.5281/zenodo.1135127
    
.. _ref-Checa-Garcia_b:

    Checa-Garcia, R., Hegglin, M. I., Kinnison, D., Plummer, D. A., and Shine, K. P., 2018: 
    Historical Tropospheric and Stratospheric Ozone Radiative Forcing Using the CMIP6 
    Database, Geophys. Res. Lett., 45, 3264–3273, https://doi.org/10.1002/2017GL076770

.. _ref-Keeble:

    Keeble, J., Hassler, B., Banerjee, A., Checa-Garcia, R., Chiodo, G., Davis, S., Eyring, V., Griffiths, P. T., Morgenstern, O.,   
    Nowack, P., Zeng, G., Zhang, J., Bodeker, G., Burrows, S., Cameron-Smith, P., Cugnet, D., Danek, C., Deushi, M., Horowitz, L. 
    W., Kubin, A., Li, L., Lohmann, G., Michou, M., Mills, M. J., Nabat, P., Olivié, D., Park, S., Seland, Ø., Stoll, J., Wieners, 
    K.-H., and Wu, T.. 2021: Evaluating stratospheric ozone and water vapour changes in CMIP6 models from 1850 to 2100, Atmos. Chem. 
    Phys., 21, 5015–5061, https://doi.org/10.5194/acp-21-5015-2021

.. _ref-Haase:

    Haase, S., Fricke, J., Kruschke, T., Wahl, S., and Matthes, K., 2020: Sensitivity of the Southern Hemisphere circumpolar jet 
    response to Antarctic ozone depletion: prescribed versus interactive chemistry, Atmos. Chem. Phys., 20, 14043–14061, 
    https://doi.org/10.5194/acp-20-14043-2020

.. _ref-Friedel:

    Friedel, M., Chiodo, G., Stenke, A. et al., 2022: Springtime arctic ozone depletion forces northern hemisphere climate 
    anomalies. Nat. Geosci. 15, 541–547, https://doi.org/10.1038/s41561-022-00974-7
    
.. _ref-Wilcox:

    Wilcox, L. J., and Charlton-Perez, A. J., 2013: Final warming of the Southern Hemisphere polar vortex in high- and low-top CMIP5     models, J. Geophys. Res. Atmos., 118, 2535– 2546, doi:10.1002/jgrd.50254


More about this POD
--------------------------

**Statistical testing for correlations**

One of the outputs of this POD is lag correlations between spring ozone at 
50 mb and zonal-mean zonal winds at all other pressure levels for two months
before and after. A student's 2-tailed t-test of the Pearson's correlation
coefficient is used to determine where the correlation is significant at 
p<0.05. Stippling is shown where the correlations are *not* significant. 

**Use of bootstrapping**

The scatterplots provided by this POD show the correlations between 
springtime ozone at 50 mb and either the final stratospheric warming day of year, 
or the late summer zonal winds at 50 mb. In these figures, 
the parentheses next to the correlations contain the 95% bootstrap confidence 
interval on the correlations from resampling the available years 1000 times. 
These confidence intervals help to determine whether the correlations are 
significant; if 0 does not fall within the range of the confidence 
interval, the correlation can be said to be statistically significant. 
Furthermore, the bootstrap confidence interval in the observation plots
give a sense of the sampling variability in the historical record; if 
the model correlation falls outside the observed bootstrap confidence interval, 
it is fair to say the model has a too strong or too weak relationship.

**Statistical testing for linear trends**
This POD outputs linear least squares best-fit trends in temperatures, winds, and 
ozone averaged for different regions in the extratropics, for two different 
historical periods during which ozone depletion or recovery occurred. These are 
calculated using the scipy function "linregress", which allows output of the 
p-value which is defined as: "The p-value for a hypothesis test whose null hypothesis
is that the slope is zero, using Wald Test with t-distribution of the test statistic."
Stippling is shown where the trends are *not* significant.