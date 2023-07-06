.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: Stratospheric Polar Vortex Extremes
================================

Last update: 2023-07-06

This POD assesses stratospheric polar vortex extremes, the tropospheric circulation
patters that precede them, and the surface impacts that follow. Extremes in the 
stratospheric polar vortex are closely linked to the tropospheric
circulation and surface climate both before and after the event. The occurrence of 
polar stratospheric circulation extremes in the Northern Hemisphere (NH), such
as sudden stratospheric warmings (SSWs) and polar vortex intensifications (VIs), are important
aspects of stratospheric variability that rely on realistic representations of the 
stratosphere and the troposphere. Extremes in the strength of the Arctic polar 
stratospheric circulation are often preceded by known near-surface circulation 
patterns, and then subsequently followed by shifts in the storm tracks (sometimes
for weeks). SSWs in the Southern Hemisphere (SH) are rare (only one event in the 
satellite record), while VIs occur more often, but both events can have persistent 
impacts on SH mid-latitude weather.

The definition for SSW events used in this POD is arguably the most commonly used one
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
(Baldwin et al. 2022), but VIs less so (Limpasuvan et al. 2005). 

This POD makes three kinds of figures from provided model data:

- Barplots showing the frequency of events by month over the input period
- Pressure versus lag contour plots of polar cap geopotential height anomalies, composited around all detected SSWs and VI events. These types of plots are sometimes referred to "dripping paint" plots in the scientific literature.
- Polar stereographic maps of surface air temperature and 500 hPa geopotential height anomalies averaged over the 30 days before and after all detected SSW and VI events.

Additionally, the POD outputs text files of the detected SSW and VI event dates in each
hemisphere. These plots are made for both hemispheres, and require at least one event to 
be detected in order for the POD to create the figure. 

Version & Contact info
----------------------

- Version/revision information: v1.0 (Jul 2023)
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
hemisphes, so 6 plots in total) and outputs to text files the SSW and VI dates.

The observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes pre-computed daily-mean zonal mean 
zonal winds and geopotential heights (with dimensions of ``(time,lev,lat)``),
and gridded daily-mean 500 hPa geopotential heights and surface air 
temperatures (with dimensions of ``(time,lat,lon)``).


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

The following daily-mean fields are required:

- Zonal-mean zonal Winds, ``ua`` as ``(time,lev,lat)`` (units: m/s)
- Zonal-mean geopotential heights, ``zg`` as ``(time,lev,lat)`` (units: m)
- Geopotential Heights at 500 hPa, ``zg`` as ``(time,lat,lon)`` (units: m)
- Surface air temperature, ``tas`` as ``(time,lat,lon)`` (units: K)

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