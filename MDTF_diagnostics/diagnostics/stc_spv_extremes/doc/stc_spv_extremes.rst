.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Stratospheric Polar Vortex Extremes
======================================================================

Last update: 2023-08-22

This POD assesses stratospheric polar vortex extremes, and the tropospheric circulation
and surface patterns that precede and follow them. Extremes in the 
stratospheric polar vortex are closely linked to the tropospheric
circulation and surface climate both before and after the event. The occurrence of 
polar stratospheric circulation extremes in the Northern Hemisphere (NH), such
as sudden stratospheric warmings (SSWs) and polar vortex intensifications (VIs), are important
aspects of stratospheric variability that rely on realistic representations of the 
stratosphere and the troposphere. Extremes in the strength of the Arctic polar 
stratospheric circulation are often preceded by known near-surface circulation 
patterns, and then subsequently followed by shifts in weather patterns (sometimes
for weeks). SSWs in the Southern Hemisphere (SH) are rare (only one event in the 
satellite record), while VIs occur more often, but both events can have persistent 
impacts on SH mid-latitude weather.

The definition for SSW events used in this POD is the most commonly used one
(Charlon and Polvani 2007): a reversal of the 10 hPa 60 deg latitude daily-mean climatological
westerly zonal winds between November and March, which returns to westerly for at least 10
consecutive days prior to 30 April (so that final warmings are not included). SSWs are
independent events if they are separated by at least 20 days of consecutive westerlies.
The definition for VI events used in this POD is adapted from previous studies 
(Limpasuvan et al. 2005, Domeisen et al. 2020): an increase of the 10 hPa 60 deg latitude
daily-mean zonal-mean zonal winds above the daily 80th percentile value calculated across
the full input data time period, which persists for at least 10 consecutive days. VIs are
independent events if they are separated by at least 20 consecutive days below the 80th 
percentile.

Models often show a different SSW seasonality compared to reanalysis (Ayarzaguena et al. 2020),
and may vary in their simulation of tropospheric circulation/surface patterns 
both preceding and following extreme stratospheric events (Ayarzaguena et al. 2020). 
Models with low model lids (>1 hPa in pressure) may show less persistent 
downward coupling than models with higher model lids (Charlton-Perez et al. 2013).
SSWs and their precursor patterns and impacts have been heavily studied 
(Baldwin et al. 2021), but VIs less so (Limpasuvan et al. 2005). 

This POD makes three kinds of figures from provided model data:

- Barplots showing the frequency of events by month over the input period
- Pressure versus lag contour plots of polar cap geopotential height anomalies, composited around all detected SSWs and VI events. These types of plots are sometimes referred to "dripping paint" plots in the scientific literature.
- Polar stereographic maps of surface air temperature and 500 hPa geopotential height anomalies averaged over the 30 days before and after all detected SSW and VI events.

Additionally, the POD outputs text files of the detected SSW and VI event dates in each
hemisphere. These plots are made for both hemispheres, and require at least one event to 
be detected in order for the POD to create the figure. 

Version & Contact info
----------------------

- Version/revision information: v1.0 (Aug 2023)
- Project PIs: Amy H. Butler (NOAA CSL) and Zachary D. Lawrence (CIRES/NOAA PSL)
- Developer/point of contact: Amy Butler (amy.butler@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

This POD is driven by the file ``stc_spv_extremes.py``, with a helper script of
``stc_spv_extremes_defs.py``.
The driver script reads in the model fields, performs a few preparatory actions
such as averaging the geopotential heights over the polar cap and removing
the daily climatology to obtain anomalies, and selecting
the 10 hPa zonal-mean zonal winds. The script then creates three plots (in both
hemispheres, so 6 plots in total) and outputs to text files the SSW and VI dates.

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes pre-computed daily-mean zonal mean 
zonal winds and geopotential heights (with dimensions of ``(time,lev,lat)``),
and gridded daily-mean 500 hPa geopotential heights and surface air 
temperatures (with dimensions of ``(time,lat,lon)``).


Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- pandas
- datetime
- xarray
- matplotlib
- statsmodels
- cartopy
- scipy


Required model output variables
-------------------------------

The following daily-mean fields are required:

- Zonal-mean zonal wind, ``ua`` as ``(time,lev,lat)`` (units: m/s)
- Zonal-mean geopotential heights, ``zg`` as ``(time,lev,lat)`` (units: m)
- Geopotential Heights at 500 hPa, ``zg`` as ``(time,lat,lon)`` (units: m)
- Surface air temperature, ``tas`` as ``(time,lat,lon)`` (units: K)

References
----------

.. _ref-Charlton_a:

    Charlton, A. J., and L. M. Polvani, 2007: A new look at stratospheric sudden warmings. 
    Part I: Climatology and modeling benchmarks. Journal of Climate, 20, 449–469.

.. _ref-Limpasuvan:

    Limpasuvan, V., D. L. Hartmann, D. W. J. Thompson, K. Jeev, and Y. L. Yung, 2005: 
    Stratosphere-troposphere evolution during polar vortex intensification. Journal of 
    Geophysical Research, 110, D24101, https://doi.org/10.1029/2005JD006302.

.. _ref-Domeisen:

    Domeisen, D. I. V., and Coauthors, 2020: The role of the stratosphere in subseasonal 
    to seasonal prediction Part I: Predictability of the stratosphere. Journal of Geophysical
    Research: Atmospheres, 125, e2019JD030920, https://doi.org/10.1029/2019JD030920.
    
.. _ref-Ayarzaguena:

    Ayarzagüena, B., and Coauthors, 2020: Uncertainty in the Response of Sudden Stratospheric
    Warmings and Stratosphere-Troposphere Coupling to Quadrupled CO2 Concentrations in CMIP6 Models.
    Journal of Geophysical Research: Atmospheres, 125, e2019JD032345, https://doi.org/10.1029/2019JD032345.
    
.. _ref-Baldwin:   

    Baldwin, M. P., and Coauthors, 2021: Sudden Stratospheric Warmings. Reviews of Geophysics,
    59, e2020RG000708, https://doi.org/10.1029/2020RG000708.
    
.. _ref-Hersbach:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803


More about this POD
--------------------------

**Confidence intervals for frequency of events**

This POD calculates the total frequency of SSW and VI events over the input
period, and then determines what fraction of those events occur in each month
of the winter season. Because the event either occurs or doesn't in any given
month, we calculate the binomial proportion confidence interval using the 
Wilson score interval, for the 95% level. 

**Significance for vertical composites**

The lag-pressure composites ("dripping paint") plots provided by this POD show
the composite-mean values of standardized polar cap geopotential height anomalies.
In these figures, significance is evaluated at the 95% level using a one-sample
t-test, and assumes that the population mean has an anomaly value of 0 and that
the sample mean comes from a normally distributed population. This may not be a 
robust assumption, but here this test is chosen for a computationally inexpensive
estimate of significance. In these plots, values that are *insignificant* by this
test are stippled. 
