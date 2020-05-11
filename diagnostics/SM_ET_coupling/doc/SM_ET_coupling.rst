Soil moisture-Evapotranspiration Coupling Diagnostic Package
============================================================
Last update: 6/28/2019

The Soil moisture-Evapotranspiration (SM-ET) Coupling Diagnostic Package evaluates the relationship between SM and ET in the summertime. It computes the correlation between surface (top-10cm) SM and ET, at the interannual timescale, using summertime-mean values. Positive correlation values indicate that, at the interannual time scale (from one summer to the next), soil moisture variability controls ET variability. This can generally be expected to occur when soil moisture availability is the limiting factor for ET. Conversely, negative values indicate that ET variations drive variations in soil moisture levels, which can be expected to occur in regions where soil moisture is plentiful and the limiting factor for ET becomes atmospheric evaporative demand (radiation, temperature); it also reflects the anticorrelation between precipitation, which drives soil moisture, and radiation, which drives ET. In addition to its sign, the correlation value quantifies how much of ET interannual variability is explained by soil moisture variations (if the correlation is positive; vice versa if it is negative)—in other words, the tightness of the SM–ET relationship. Considering seasonal means removes issues associated with the coseasonality of soil moisture and ET, while still reflecting the overall (i.e., seasonally integrated) dependence of ET on soil moisture throughout the whole season. See Berg and Sheffield (2018) for further details.

Contact info
------------

- PIs of the project: Eric Wood, Princeton University (efwood@princeton.edu);
- previous PI Justin Sheffield, formerly at Princeton University, now at University of Southampton, UK (justin.sheffield@soton.ac.uk).
- Current developer: Alexis Berg (ab5@princeton.edu)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The currently package consists of:
- a Python script (SM_ET_coupling.py), which sets up the directories and calls\.\.\.
- \.\.\. an R script (SM_ET_coupling.R) which reads the data, performs the calculations and generates the plots.

As a module of the MDTF code package, all scripts of this package can be found
under ``mdtf/MDTF_$ver/var_code/SM_ET_coupling``
and pre-digested observational data (in RData format) under ``mdtf/inputdata/obs_data/SM_ET_coupling``
Place your input data at: ``mdtf/inputdata/model/$model_name/mon/``

Required programming language and libraries
-------------------------------------------

Python and R are required to run the diagnostic.

The part of the package written in Python requires packages os and subprocess. These Python packages are already included in the standard Anaconda installation The R script requires packages ColorRamps, maps, fields, akima and ncdf4. R version 3.4 was used to develop this package, but it should work on older and more recent R versions.

Required model output variables
-------------------------------

The following three 3-D (lat-lon-time), monthly model fields are required:

- surface soil moisture (“mrsos” in CMIP5 conventions)
- land evaporation (“evspsbl”) or latent heat flux (“hfls”)
- precipitation (“pr”)

The observational estimate from GLEAM (see below) is for 1980-2014; therefore, the model data should cover the same time period, as the background climate, and thus the SM-ET coupling, could be different if the model data covers another period (although we attempt to control for precipitation differences between model and observations – see below). Note that 2014 is the end year of the historical period of CMIP6 historical simulations. 1980 is the beginning of the GLEAM data. Note that, by default, the R script will read the whole monthly model file provided as input. We thus recommend that users truncate their model files to cover precisely the period 1980-2014.

More about the diagnostic
-------------------------

a) Choice of reference dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With respect to SM-ET coupling, an observational value of the metric is difficult to obtain, because of the challenges associated with measuring soil moisture and evapotranspiration extensively over continents, at the required spatial and temporal scales. Global observational products of ET and soil moisture do exist (in particular from remote sensing), but are plagued by numerous uncertainties or shortcomings limiting their use, here, to compute SM-ET coupling in a straightforward manner. Calculating SM-ET coupling from various datasets combining modeling and observations, such as reanalyses (e.g., MERRA2, JRA55, ERA-I) or land surface models driven by observations (e.g., GLADS, GLDAS2), yields estimates of SM-ET coupling that exhibit significant spread (comparable in some regions to the spread across CMIP5 models), even though their representation of the driving surface climate (e.g., precipitation) is very comparable. This diversity is not necessarily surprising, given that SM-ET coupling largely remains, in these types of products, a product of the underlying land model used to create the dataset. In this context, we eventually decided to use the GLEAM (Global Land Evaporation Amsterdam Model) dataset (:ref:`Martens et al. 2017 <2>`; see https://www.gleam.eu/), as a reference, provided along the SM-ET coupling metric here in the diagnostic package. GLEAM is a global, gridded land surface dataset based on remote sensing covering 1980-2017 (here we only use 1980-2014, so that, in particular, the latest CMIP6 simulations, which extend to 2014, can be compared to this data). While the control of SM on ET in the GLEAM dataset ultimately remains a property of the modeling assumptions underlying this product, GLEAM is the only product, to our knowledge, assimilating available remote sensing observations of both soil moisture and vegetation, thus providing a dataset including both observationally-constrained and mutually-consistent SM and ET. That being said, caution should be exerted when comparing the model results to this estimate, which is only provided as a tentative reference, not an observational truth.

b) Correction for precipitation differences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In :ref:`Berg and Sheffield (2018) <1>`, we found that across CMIP5 models, differences in summertime precipitation explained a significant part of model differences in SMET coupling. In other words, in a given location – for instance, a semi-arid location models with more precipitation have less positive SM-ET coupling – i.e., ET is less limited by soil moisture (see Figure 3 in :ref:`Berg and Sheffield 2018 <1>`). However, mean precipitation did not explain all of the differences across models, which we interpreted as reflecting model differences, for a given amount of precipitation, in the treatment of land surface processes related to vegetation and hydrology. In the diagnostic package here, summertime precipitation differences between the model and the observations (GLEAM over 1980-2014) are provided as a plot. Assuming that, to first approximation, precipitation differences are independent from the surface, we attempt to control for precipitation differences between model and observations in the package by using the regression across CMIP5 models between mean summertime precipitation and SM-ET coupling established in Berg and Sheffield (:ref:`2018 <1>`; Figure 3). In other words, the coupling calculated for the model, when correcting for precipitation differences, is the coupling that would have existed in the model if precipitation were correct (i.e., equal to the observations in GLEAM). For instance, in regions where the model produces too much rainfall, the correction will tend to increase the estimate of SM-ET coupling (since, if precipitation was more realistic, it would be lower and soil moisture control on ET would thus be greater). This correction is tentative, as it assumes that the relationship across CMIP5 models between precipitation and SM-ET coupling is realistic, in the sense that it says something about the physics of the real world.

References
----------

   .. _1:

1. Berg A. and J. Sheffield (2018), Soil moisture-evapotranspiration coupling in CMIP5 models: relationship with simulated climate and projections, *Journal of Climate*, **31** (12), 4865-4878.

   .. _2:

2.  Martens, B., Miralles, D.G., Lievens, H., van der Schalie, R., de Jeu, R.A.M., FernándezPrieto, D., Beck, H.E., Dorigo, W.A., and Verhoest, N.E.C.: GLEAM v3: satellite-based land evaporation and root-zone soil moisture, *Geoscientific Model Development*, **10**, 1903–1925, https://doi.org/10.5194/gmd-10-1903-2017, 2017.
