Information about Level 1 – Basic ENSO diagnostics
=============================================================================

At this level, POD calculates simple seasonal climatology, anomalies and composites
Identify ENSO winters and construct seasonal composite anomalies for relevant variables (e.g.,
anomalous precipitation, circulation, geopotential height to estimate standardized PNA index). Also, seasonal climatology required for other Levels are also computed here.
Reference index (e.g., Nino3.4 SST)

-  Seasonal averages

..

   *Note: Level 1 diagnostics (ENSO-related anomalies and seasonal
   climatology) are required to perform Levels 2-4 diagnostics*

Based on a reference ENSO index (e.g., area-averaged SST anomalies over Nino3.4 region), 
ENSO winters are identified, and seasonal composites of variables relevant to Rossby wave
sources and global circulation anomalies are constructed.

The code files related to this Level 1 are stored in the ~/diagnostics/ENSO_RWS/LEVEL_01 directory.  
All input data should be under ~/diagnostics/inputdata/model/$model/mon, (e.g. $model = CESM1),
the intermediate output data are 
in: ~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model/netCDF, (e.g. $model = CESM1, $first_year = 1950, $last_year = 2005), while graphics is under
~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model/PS

Required model output variables and their corresponding units
========================================================================================

The following model fields are required as monthly data:
4-D variables (longitude, latitude, pressure level, time):

1. *zg* : HGT geopotential height (m)

2. *ua* : U wind component [m/s]

3. *va* : V wind component [m/s]

4. *ta* : Temperature [K]

3-D variables (longitude, latitude, time):

5. *pr* : Precipitation [kg/m2/s]

6. *ts* : Surface Temperature [K]


All input file should be in netCDF format following CF convention, one variable per file, with monthly
output frequency, $model.$variable.mon.nc. For instance, CESM2 temperature data will be in
CESM2.ta.mon.nc file. *CF convention refers to standard CMIP-era model outputs.*


Final output directories:
=========================
The output files are under
~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model/netCDF 
(e.g. $model = CESM1, $fist_year= 1950, $last_year = 2005)
The composites for El Niño/La Nina are under
~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model/netCDF/ELNINO (or LANINA)
Graphical output is now set to be all global and for all variables. The actual files are in
~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model.

