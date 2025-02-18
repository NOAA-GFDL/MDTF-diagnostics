.. This is a comment in RestructuredText format (two periods and a space).
Westerly Wind Event Diagnostic Documentation
================================

Last update: 2024-09-19

This POD identifies westerly wind events (WWEs) in the equatorial Pacific
(120E-280E) using daily equatrially-averaged (2.5S-2.5N) 120-day
highpass filtered zonal wind stress. WWEs in TropFlux observations are
compared to WWEs produced by earth system models. Two sets of figures
are created:

1. Hovmollers of 120-day highpass filtered zonal wind stress for each
   year of the data considered. Each year is a separate panel with the
   first 20 years occurring on one output figure and the next 20 years
   on the second output figure. Time-longitude zonal wind stress
   patches that qualify as WWEs are outlined in black. The Hovmollers
   are created for both the TropFlux observations and the ESM.

2. A 1D histogram of the likelihood of each 1 longitude
bin across the Pacific experiencing a WWE per day. The likelihood is
calculated as the total number of unique events at each 1 longitude
divided by the total number of days in each data set. The reciprocal
of the frequncy indicates the average return rate of a WWE per
longitude or the average number of days between WWEs at each
longitude.

The variables needed to created these figures are saved in the
follwing directories:
{work_dir}/WWEs/model/netCDF/ and /inputdata/obs_data/WWEs/ 

Version & Contact info
----------------------
- Version/revision information: v1.0 (September 2024)
- PI: Emily M. Riley Dellaripa (Emily.Riley@colostate.edu), Colorado State University
- Current Developer: Emily M. Riley Dellaripa (Emily.Riley@colostate.edu), Colorado State University
- Contributors: Charlotte A. DeMott (CSU); Eric D. Maloney (CSU);
  Jingxuan Cui (CSU)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

This POD is composed of two files. The main driver script is 
``WWEs.py``, which contains the code and functions which perform the
diagnostic computations and call the plotting code. The plotting code
and additional functions needed to identify the WWEs and determine
their characteristics are contained in ``WWE_diag_tools.py``. The main
driver script reads in the necessary data, prepares the zonal wind
stress for identifying WWEs, calls the function that identifies the
WWEs and their characteristics, saves the WWE labels and mask and
their characteristics (i.e., central time and longitude, zonal extent,
duration, and integrated wind work (i.e., total forcing of zonal wind
stress to the ocean)), calls the functions that make the plots.

The observational data used is TropFlux daily zonal surface fluxes
that are available from 1980-2014 (Praveen Kumar 2014).

The POD is based on Riley Dellaripa et al. (2024) and details of the
methods, motivation, and results of our work can be found there.

By default the WWEs in the model output are identified using a 0.04 N/m2
threshold, which reflects two standard deviations of the
equatorially-averaged 120-day highpass filtered TropFlux zonal wind
stress between 1980-2014.  Users can adjust the settings.jsonc file to
not use the 0.04 N/m2 threshold, but instead calculate the models two
standard deviations of its equatorially-averaged 120-day highpass
filtered zonal wind stress and use that as the threshold for
identifying the model's WWEs.

Required programming language and libraries
-------------------------------------------

* Python >= 3.12
* matplotlib
* xarray
* numpy
* os
* time
* xesmf
* scipy
* functools
* intake
* yaml
* sys

These dependencies are included in the python3_base environment
provided by the automated installation script
for the MDTF Framework.

Required model output variables
-------------------------------

This POD requires the following variables:

* Zonal wind stress (TAUU, 3D (time-lat-lon), Units: Pa, Frequency: Daily
* Percentage of the grid cell occupied by land (sftlf),  2D
  (lat-lon), Units: %, Frequency: Fixed


References
----------
1. Riley Dellaripa et al. (2024): Evaluation of Equatorial Westerly
   Wind Events in the Pacific Ocean in  CMIP6 Models. *J. Climate*,
   `doi: 10.1175/JCLI-D-23-0629.1 < https://doi.org/10.1175/JCLI-D-23-0629.1>`__.

2. Praveen Kumar,B., J. Vialard, M. Lengaigne, V. S. N. Murty, M. J. McPhaden M. F. Cronin, F. Pinsard,
   and K. Gopala Reddy, 2013: TropFlux wind stresses over the tropical
   oceans: evaluation and comparison with other products. Clim. Dyn.,
   40, 2049–2071,  `doi: 10.1007/s00382-012-1455-4 < https://doi.org/10.1007/s00382-012-1455-4>`__.

More about this diagnostic
--------------------------
Westerly wind events (WWEs) are anomalously strong, long lasting
westerlies that occur primarily over the Pacific Ocean. The momentum
imparted on the ocean from WWEs have the potential to excite eastward
propagating oceanic Kelvin wave. The oceanic Kelvin waves, in turn,
warm the ocean surface and depress the thermocline as they propagate
eastward, which can have impacts on ENSO development. Because of WWEs
relationship to oceanic Kelvin waves and ENSO development, it is
important to determine how well earth system models (ESMs) replicate
them. The inability for a model to accurately replicate WWE frequency,
location, and strength has potential consequences for ENSO
development. WWEs are frequently associated with Madden Julian
Oscillaiton (MJO) events or equatorial convectively coupled Rosby
waves (CRWs), though MJO and CRWs are not the only source of WWEs. The
inability of a model to appropriately represent WWE forcing can be
linked to deficiencies in a models representation of MJO and CRW
variability, though there are some models that accurately capture MJO
and CRW variability while still misprepresenting WWE forcing in the
west Pacific. For more details on this work please see Riley Dellaripa
et al. (2014).
