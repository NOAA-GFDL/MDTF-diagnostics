**Information about Level 1 – Basic ENSO diagnostics**

At this level, POD calculates simple seasonal averages, composites,
regression and correlations.

Based on a reference ENSO index (e.g., area-averaged SST anomalies over
Nino3.4 region), seasonal composites of variables relevant to MSE budget
are constructed for the entire 2-year life-cycle of ENSO. Here, Y (0)
refers to the developing, and Y (1) the decaying phase of ENSO.

To perform composites set ENSO_COMPOSITE = 1 in the
~/diagnostics/ENSO_MSE/settings.jsonc.

The code files related to this Level 1 are stored in the
~/diagnostics/ENSO_MSE/COMPOSITE directory. All input data should be
under ~/diagnostics/inputdata/model/$model/mon, (e.g. $model = CESM1),
the intermediate output data are in:
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/

COMPOSITE/model/netCDF, (e.g. $model = CESM1, $first_year = 1950,
$last_year = 2005),

while graphics is under
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/model

The required input variables are:

    *Z(x,y,z,t)* geopotential height,

    *U(x,y,z,t), V(x,y,z,t)* u and v wind components

    *T(x,y,z,t)* temperature

    *Q(x,y,z,t)* specific humidity

    *OMG(x,y,z,t)* vertical velocity

    *PR(x,y,t)* precipitation

    *SST(x,y,t)* surface temperature

    *SHF(x,y,t)* sensible heat flux

    *LHF(x,y,t)* latent heat flux

    *RSDT(x,y,t)* top of the atmosphere shortwave down

    *RSUT(x,y,t)* top of the atmosphere shortwave up

    *RLUT(x,y,t)* top of the atmosphere longwave up

    *RSDS (x,y,t)* surface shortwave down

    *RSUS(x,y,t)* surface shortwave up

    *RLUS(x,y,t)* surface longwave up

    *RLDS(x,y,t)* surface longwave down

All input file should be in netCDF format following CF convention, one
variable per file, with monthly output frequency,
$model.$variable.mon.nc. For instance, CESM2 temperature data will be in
CESM2.ta.mon.nc file. *CF convention refers to standard CMIP-era model
outputs.*

*Final output directories:*

The output files are under
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/$diag_name/model/netCDF
(e.g. $model = CESM1, $fist_year= 1950, $last_year = 2005, $diag_name =
COMPOSITE )

The composites for El Niño/La Nina are under

~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/$diag_name/model/netCDF/ELNINO
(or LANINA)

Similarly 2-year life cycle ENSO composite results are under:

~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/$diag_name/model/netCDF/24MONTH_ELNINO (or 24MONTH_LANINA)

Graphical output is now set to be all global and for all surface
variables. The actual files are in
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/model.
