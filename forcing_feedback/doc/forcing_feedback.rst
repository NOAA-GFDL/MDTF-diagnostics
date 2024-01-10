Forcing Feedback Diagnostic Package
============================================================
Last update: 12/21/2023

The Forcing Feedback Diagnostic package evaluates a model's radiative forcing and radiative feedbacks. This is a commong framework for understanding the radiative constraints on a model's climate sensitivity and is outlined in detail by :ref:`Sherwood et al. (2015) <1>`, among many others. To compute radiative feedbacks, anomalies of temperature, specific humidity and surface albedo are translated into radiative anomalies by multiplying them by radiative kernels developed from the CloudSat/CALIPSO Fluxes and Heating Rates product (:ref:`Kramer et al. 2019 <2>`).These radiative anomalies are regressed against the model's global-mean surface temperature anomalies to estimate the radiative feedbacks. Cloud radiative feedbacks are computed as the change in cloud radiative effects from the model's TOA radiative flux variables, corrected for cloud masking using the kernel-derived non-cloud radiative feedbacks (:ref:`Soden et al. 2008 <3>`).  The Instantaneous Radiative Forcing is computed first under clear-sky conditions by subtracting kernel-derivred clear-sky radiative feedbacks from the clear-sky TOA radiative imbalance diagnosed from the model's radiative flux variables. The all-sky Instantaneous Radiative Forcing is estimated by dividing the clear-sky Instantaneous Radiative Forcing by a cloud masking constant (:ref:`Kramer et al. 2021 <4>`). All radiative quantities in this package are defined at the TOA and positive represents an increase in net downwelling or a radiative heating of the planet.


Contact info
------------

- PI of the project: Brian Soden, University of Miami (bsoden@rsmas.miami.edu);
- Current developer: Ryan Kramer (ryan.kramer@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The currently package consists of:
- a Python script (forcing_feedback.py), which sets up the directories and calls\.\.\.
- \.\.\. an Python script (forcing_feedback_kernelcalcs.py) which reads the data, performs the calculations and saves the results to temporary netcdfs./././.
- \.\.\. Finally, a Python script (forcing_feedback_plots.py) reads in the temporary results, observational radiative forcing and feedbacks and creates plots.  Throughout the package, the scripts use Python functions defined in a third Python script (forcing_feedback_util.py)

As a module of the MDTF code package, all scripts of this package can be found
under ``mdtf/MDTF_$ver/var_code/forcing_feedback``
and pre-digested observational data and radiative kernels (in netcdf format) under ``mdtf/inputdata/obs_data/forcing_feedback``
Place your input data at: ``mdtf/inputdata/model/$model_name/mon/``

Required programming language and libraries
-------------------------------------------

Python is required to run the diagnostic.

The part of the package written in Python requires packages os, sys, numpy, xarray, scipy, matplotlib, cartopy and dask. These Python packages are already included in the standard Anaconda installation 

Required model output variables
-------------------------------

The following three 3-D (lat-lon-time), monthly model fields are required:
- surface skin temperature ("ts" in CMIP conventions)
- TOA incident shortwave radiation ("rsdt")
- TOA outgoing all-sky shortwave radiation ("rsut")
- TOA outgoing clear-sky shortwave radiation ("rsutcs")
- TOA outgoing all-sky longwave radiation ("rlut")
- TOA outgoing clear-sky longwave radiation ("rlutcs")
- Surface downwelling all-sky shortwave radiation ("rsds")
- Surface downwelling clear-sky shortwave radiation ("rsdscs")
- Surface upwelling all-sky shortwave radiation ("rsus")
- Surface upwelling clear-sky shortwave radiation ("rsuscs")

The following 4-D (lat-lon-level-time), monthly model fields are requied:
- Air temperature ("ta" in CMIP conventions)
- Specific humidity ("hus")

The observational estimates (see below) are for 2003-2014. The start date is based on data availability while the end date was selected to match the end date of relevant CMIP6 simulations. For an ideal comparison, the model data used in this POD should cover the same period and have realistic, historical forcing boundary conditions. However, this package will still have value as a "gut check" for any simulation, especially with respect to radiative feedbacks, which often exhibit similar characteristics regardless of the forcing scenario.




More about the diagnostic
-------------------------

a) Choice of reference dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While total TOA radiative changes are directly observed, the radiative feedback and radiative forcing components are not. Therefore, in this package the observational estimates of radiative feedbacks and radiative forcing are derived by multiplying data from ERA5 Reanalysis by the CloudSat/CALIPSO radiative kernels mentioned above. Global-mean surface temperature anomalies from ERA5 are used to compute the radiative feedbacks from the kernel-derived radiative anomalies as described above. To diagnose the instantaneous radiative forcing, the kernel-derived, clear-sky estimates of radiative feedbacks are subtracted by a measure of  the total radiative anomalies at the TOA. For the observational dataset used here, that total radiative anomaly estimates is from CERES. The methods for diagnosing these radiative changes in observations are outlined by :ref:`Kramer et al. 2021 <4>` and :ref:`He et al. 2021 <5>`

References
----------

   .. _1:

1. Sherwood, S. C., Bony, S., Boucher, O., Bretherton, C., Forster, P. M., Gregory, J. M., & Stevens, B. (2015). Adjustments in the Forcing-Feedback Framework for Understanding Climate Change. *Bulletin of the American Meteorological Society*, **96** (2), 217–228. https://doi.org/10.1175/BAMS-D-13-00167.1

   .. _2:

2. Kramer, R. J., Matus, A. V., Soden, B. J., & L’Ecuyer, T. S. (2019). Observation‐Based Radiative Kernels From CloudSat/CALIPSO. *Journal of Geophysical Research: Atmospheres*, 2018JD029021. https://doi.org/10.1029/2018JD029021

   .. _3:

3. Soden, B. J., Held, I. M., Colman, R., Shell, K. M., Kiehl, J. T., & Shields, C. A. (2008). Quantifying Climate Feedbacks Using Radiative Kernels. *Journal of Climate*, **21** (14), 3504–3520. https://doi.org/10.1175/2007JCLI2110.1

   .. _4:

4. Kramer, R.J, He, H., Soden, B.J., Oreopoulos, R.J., Myhre, G., Forster, P.F., & Smith, C.J. (2021) Observational Evidence of Increasing Global Radiative Forcing. *Geophys. Res. Lett.*, **48** (7), e2020GL091585. https://doi.org/10.1029/2020GL091585

   .. _5:

5. He, H., Kramer, R.J., & Soden, B.J. (2021) Evaluating Observational Constraints on Intermodel Spread in Cloud, Temperature and Humidity Feedbacks. *Geophys. Res. Lett.*, **48**, e2020GL092309. https://doi.org/10.1029/2020GL092309

