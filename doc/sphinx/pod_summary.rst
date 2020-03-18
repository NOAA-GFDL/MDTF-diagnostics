Summary of MDTF process-oriented diagnostics
==========================================================

The MDTF diagnostic package is portable, extensible, usable, and open for contribution from the community. A goal is to allow diagnostics to be repeatable inside, or outside, of modeling center workflows. These are diagnostics focused on model improvement, and as such a slightly different focus from other efforts. The code runs on CESM model output, as well as on GFDL and CF-compliant model output.

The MDTF Diagnostic Framework consists of multiple modules, each of which is developed by an individual research group or user. Modules are independent of each other, each module:

- Produces its own html file (webpage) as the final product

- Consists of a set of process-oriented diagnostics

- Produces a figures or multiple figures that can be displayed by the html in a browser


1. Convective Transition Diagnostics
--------------------------------------------------------------
*J. David Neelin (UCLA)*
neelin@atmos.ucla.edu

This POD computes statistics that relate precipitation to measures of tropospheric temperature and moisture, as an evaluation of the interaction of parameterized convective processes with the large-scale environment. Here the basic statistics include the conditional average and probability of precipitation, PDF of column water vapor (CWV) for all events and precipitating events, evaluated over tropical oceans. The critical values at which the conditionally averaged precipitation sharply increases as CWV exceeds the critical threshold are also computed (provided the model exhibits such an increase).

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  6-hourly or higher
Column water vapor  6-hourly or higher
==================  ==================

References:

- Kuo, Y.-H., K. A. Schiro, and J. D. Neelin (2018): Convective transition statistics
  over tropical oceans for climate model diagnostics: Observational baseline. *J. Atmos. Sci.*, **75**, 1553-1570, https://doi.org/10.1175/JAS-D-17-0287.1.
 

2. Extratropical Variance (EOF 500hPa Height)
--------------------------------------------------------------
*CESM/AMWG (NCAR)*
bundy@ucar.edu

This POD computes the climatological anomalies of 500 hPa geopotential height and calculates the EOFs over the North Atlantic and the North Pacific.

===================  ==================
Variables            Frequency
===================  ==================
Surface pressure     Monthly 
Geopotential hegiht  Monthly
===================  ==================


3. MJO Propagation and Amplitude
--------------------------------------------------------------
*Xianan Jiang (UCLA)*
xianan@ucla.ecu

This POD calculates the model skill scores of MJO eastward propagation versus winter mean low-level moisture pattern over Indo-Pacific, and compares the simulated amplitude of MJO over the Indian Ocean versus moisture convective adjustment time-scale.

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  Daily or higher 
Specific humidity   Daily or higher 
==================  ==================

References:

- Jiang, X. (2017): Key processes for the eastward propagation of the Madden‐Julian 
  Oscillation based on multimodel simulations, *JGR‐Atmos*, **122**, 755–770, https://doi.org/10.1002/2016JD025955.

- Gonzalez, A. O., and X. Jiang (2017): Winter mean lower tropospheric moisture over 
  the Maritime Continent as a climate model diagnostic metric for the propagation of the Madden‐Julian oscillation, *Geophys. Res. Lett.*, **44**, 2588–2596, https://doi.org/10.1002/2016GL072430.

- Jiang, X., M. Zhao, E. D. Maloney, and D. E. Waliser, (2016): Convective moisture 
  adjustment time scale as a key factor in regulating model amplitude of the Madden‐Julian Oscillation. *Geophys. Res. Lett.*, **43**, 10412‐10419, https://doi.org/10.1002/2016GL070898. 


4. MJO Spectra and Phasing
--------------------------------------------------------------
*CESM/AMWG (NCAR)*
bundy@ucar.edu

This PDO computes many of the diagnostics described by the WGNE MJO Task Force and developed by Dennis Shea for observational data. Using daily precipitation, outgoing longwave radiation, zonal wind at 850 and 200 hPa and meridional wind at 200 hPa, the module computes anomalies, bandpass-filters for the 20-100 day period, calculates the MJO Index as defined as the running variance over the bandpass filtered data, performs an EOF analysis, and calculates lag cross-correlations, wave-number frequency spectra and composite life cycles of MJO events.

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  Daily 
OLR                 Daily 
U850                Daily 
U200                Daily 
V200                Daily 
==================  ==================

References:

- Waliser et al. (2009): MJO simulation diagnostics. *J. Climate*, **22**, 3006–3030,
  https://doi.org/10.1175/2008JCLI2731.1.


5. MJO Teleconnections 
--------------------------------------------------------------
*Eric Maloney (CSU)*
eric.maloney@colosate.edu

The POD first compares MJO phase (1-8) composites of anomalous 250 hPa geopotential height and precipitation with observations (ERA-Interim/GPCP) and several CMIP5 models (BCC-CSM1.1, CNRM-CM5, GFDL-CM3, MIROC5, MRI-CGCM3, and NorESM1-M). Then, average teleconnection performance across all MJO phases defined using a pattern correlation of geopotential height anomalies is assessed relative to MJO simulation skill and biases in the North Pacific jet zonal winds to determine reasons for possible poor teleconnections. Performance of the candidate model is assessed relative to a cloud of observations and CMIP5 simulations.

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  Daily 
OLR                 Daily 
U850                Daily 
U250                Daily 
Z250                Daily 
==================  ==================

References:

- Henderson, S. A., Maloney, E. D., & Son, S. W. (2017): Madden–Julian oscillation 
  Pacific teleconnections: The impact of the basic state and MJO representation in general circulation models. *Journal of Climate*, **30** (12), 4567-4587 https://doi.org/10.1175/JCLI-D-16-0789.1.


6. Diurnal Cycle of Precipitation
--------------------------------------------------------------
*Rich Neale (NCAR)*
bundy@ucar.edu

The POD generates a simple representation of the phase (in local time) and amplitude (in mm/day) of total precipitation, comparing a lat-lon model output of total precipitation with observed precipitation derived from the Tropical Rainfall Measuring Mission.

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  3-hourly or higher 
==================  ==================

References:

- Gervais, M., J. R. Gyakum, E. Atallah, L. B. Tremblay, and R. B. Neale (2014): How 
  Well Are the Distribution and Extreme Values of Daily Precipitation over North America Represented in the Community Climate System Model? A Comparison to Reanalysis, Satellite, and Gridded Station Data. *Journal of Climate*, **27**, 5219–5239, https://doi.org/10.1175/JCLI-D-13-00320.1.

- Gettelman, A., P. Callaghan, V. E. Larson, C. M. Zarzycki, J. T. Bacmeister, P. H. 
  Lauritzen, P. A. Bogenschutz, and R. B. Neale, (2018): Regional Climate Simulations With the Community Earth System Model. *Journal of Advances in Modeling Earth Systems*, **10**, 1245–1265, https://doi.org/10.1002/2017MS001227.


7. Coupling between Soil Moisture and Evapotranspiration
--------------------------------------------------------------
*Alexis M. Berg (Princeton)*
ab5@princeton.edu

This POD evaluates the relationship between soil moisture and evapotranspiration. It computes the correlation between surface (0~10 cm) soil moisture and evapotranspiration during summertime. It then associates the coupling strength with the simulated precipitation.   

==================  ==================
Variables           Frequency
==================  ==================
Soil moisture       Monthly 
Evapotranspiration  Monthly
Precipitation rate  Monthly
==================  ==================

References: 

- Berg, A and J. Sheffield. (2018): Soil Moisture–Evapotranspiration Coupling in 
  CMIP5 Models: Relationship with Simulated Climate and Projections, *J. Climate*, **31** (12), 4865-4878, https://doi.org/10.1175/JCLI-D-17-0757.1. 


8. Wavenumber-Frequency Spectra
--------------------------------------------------------------
*CESM/AMWG (NCAR)*
bundy@ucar.edu

This POD performs wavenumber frequency spectra analysis (Wheeler and Kiladis) on OLR, Precipitation, 500hPa Omega, 200hPa wind and 850hPa wind.

==================  ==================
Variables           Frequency
==================  ==================
Precipitation rate  Daily 
OLR                 Daily 
U850                Daily 
U200                Daily 
W250                Daily 
==================  ==================

References:

- Wheeler, M. and G. N. Kiladis (1999): Convectively Coupled Equatorial Waves: Analysis
  of Clouds and Temperature in the Wavenumber–Frequency Domain. *J. Atmos. Sci.*, **56**, 3, 374–99. `https://doi.org/10.1175/1520-0469(1999)056<0374:CCEWAO>2.0.CO;2 <https://doi.org/10.1175/1520-0469(1999)056\<0374:CCEWAO\>2.0.CO;2>`_. 

