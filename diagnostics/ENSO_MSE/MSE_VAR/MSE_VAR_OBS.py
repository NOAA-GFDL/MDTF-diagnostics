#
#      The code at this level uses pre-calculated data from levels 1 and 2
#     COMPOSITE and MSE.  It calculates the Moist Static Energy (MSE)
#    variances and select variable co-variances.  Area averaged seasonal
#     MSE variances and co-variances are displayed in bar charts in
#     ~/wkdir/MDTF_$CASE  directories.
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#     This package is distributed under the LGPLv3 license (see LICENSE.txt)

import numpy as np
import sys
import subprocess

import datetime

import os

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


from get_data_in_OBS import get_data_in_OBS
from get_flux_in_OBS import get_flux_in_OBS
from get_clima_in_OBS import get_clima_in_OBS
from get_clima_flux_in_OBS import get_clima_flux_in_OBS

from write_out import write_out
from write_out_general import write_out_general
from moist_routine_variance import moisture_variance
from get_parameters_in import get_parameters_in
from get_anomaly import get_anomaly

from get_lonlat_in_OBS import get_lonlat_in_OBS


shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)

      The top driver for the MSE component variances calculations
       all need to be anomalies !!!
      input data are as follows:
       2 dimensional atmospheric variables: all vertical integrals
   dimensions:  IMAX, JMAX
   variables : TS:  skin surface  temperature [K]
               PR :  precipitation rate [kg/m2/sec]
               LHF :  latent heat flux  [W/m2]
               SHF :  sensible heat flux  [W/m2]
               SW  :  net  shortwave flux [W/m2]
               LW  :  net  longwave flux [W/m2]
               MSE :  vertical integral of Moist Static Energy [J/m2]
               MADV :  moisture advection [W/m2]
               OMSE  : MSE vertical advection [W/m2]
   1 dimensional INPUT:
         LON(IMAX) - longitude dimensions
         LAT(JMAX) - latitude dimensions
         PLEV(ZMAX) - vertical dimensions and  pressure levels [mb]
         REARTH  - radius of earth in  [m]

     pamaters LON1, LON2, LAT1, LAT2   for spatial variances
    OUTPUT:   variances of input variables (over selected area)
               TS_VAR:  skin surface  temperature [K]
               PR_VAR :  precipitation rate [kg/m2/sec]
               LHF_VAR :  latent heat flux  [W/m2]
               SHF_VAR :  sensible heat flux  [W/m2]
               SW_VAR  :  net  shortwave flux [W/m2]
               LW_VAR  :  net  longwave flux [W/m2]
               MSE_VAR :  vertical integral of Moist Static Energy [J/m2]
               MADV_VAR :  moisture advection [W/m2]
               OMSE_VAR  : MSE vertical advection [W/m2]


  missing data are flaged by UNDEF which is a very large number

'''
####  check the preprocessing
flag0  = 1
##############  get the parameters
prefix = os.environ["POD_HOME"] + "/MSE_VAR/"

##############  check for preprocessed data in OBS directory
composite_dir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"] + "/obs/"
mse_dir       = os.environ["ENSO_MSE_WKDIR_MSE"] + "/obs/"
mse_var_dir   = os.environ["ENSO_MSE_WKDIR_MSE_VAR"] + "/obs/"

prefix1 =  composite_dir +"/netCDF/DATA/"
convert_file = composite_dir +"/netCDF/DATA/preprocess.txt"

#######################################33
### print diagnostic message
print ("  The Observational MSE Variance  Composites to be processed ")


#################  set the default domain lat/lon boxes
###   Central Pacific
clon1 = 160.
clon2 = 200.
clat1 = -10.
clat2 = 5.
##  and  Eastern Pacific
elon1 = 220.
elon2 = 280.
elat1 = -5.
elat2 = 5.

### first get the system parameters   prefix = ~/obs_data/DATA/netCDF
##    nameout = ~/wkdir/MSE_VAR    prefix  top dir.

# Source code
prefix = os.environ["POD_HOME"] + "/MSE_VAR/"

composite_dir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"] + "/obs/"
mse_dir       = os.environ["ENSO_MSE_WKDIR_MSE"] + "/obs/"
mse_var_dir   = os.environ["ENSO_MSE_WKDIR_MSE_VAR"] + "/obs/"

###   input data  pre-calculated in obs
prefix1 = os.environ["OBS_DATA"] + "/DATA/netCDF/ELNINO/"
prefix2 = os.environ["OBS_DATA"] + "/DATA/netCDF/LANINA/"
prefix3 = os.environ["OBS_DATA"] + "/DATA/netCDF/"

###########3

prefixout  =  mse_var_dir+"/netCDF/"
prefixout1 =  mse_var_dir+"/netCDF/ELNINO/"
prefixout2 =  mse_var_dir+"/netCDF/LANINA/"

##


rearth = 6378000.0
dx = -9999.
dy = -9999.

undef = float(1.1e+20)

season = "NIL"
model = "NIL"
llon1 = undef
llon2 = undef
llat1 = undef
llat2 = undef
imindx1 = undef
imindx2 = undef
im1 = undef
im2 = undef
sigma = undef
composite = 0
composite24 = 0
regression = 0
correlation = 0
##

im1 = 12
im2 = 14

##iy1 = os.environ["FIRSTYR"]
##iy2 = os.environ["LASTYR"]
###  reading  in selected  parameters  from parameter.txt file
##   read in parameters    and the actual array dimensions imax, jmax, zmax,
##    longitudes, latitudes,  plevels
llon1, llon2, llat1, llat2, sigma, imindx1, imindx2,  composite, im1, im2, season,  composite24, regression, correlation,  undef  =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, imindx1, imindx2, composite, im1, im2, season, composite24, regression, correlation,  undef,  prefix)

###  reading in the domensions and the actual lon/lat/plev data
imax = 0
jmax = 0
zmax = 0

### print( imax,  " " , jmax , " " , zmax )

lon    = np.zeros(imax,dtype='float32')
lat    = np.zeros(jmax,dtype='float32')
plevs  = np.zeros(zmax,dtype='float32')

###  prefix1 = OBS directory ELNINO
imax, jmax, lon, lat = get_lonlat_in_OBS( imax, jmax, lon, lat, prefix1, undef)

###  array declarations
# 2D variables
ts   = np.zeros((imax,jmax),dtype='float32', order='F')
pr   = np.zeros((imax,jmax),dtype='float32', order='F')
shf  = np.zeros((imax,jmax),dtype='float32', order='F')
lhf  = np.zeros((imax,jmax),dtype='float32', order='F')
sw   = np.zeros((imax,jmax),dtype='float32', order='F')
lw   = np.zeros((imax,jmax),dtype='float32', order='F')
mse  = np.zeros((imax,jmax),dtype='float32', order='F')
madv = np.zeros((imax,jmax),dtype='float32', order='F')
omse = np.zeros((imax,jmax),dtype='float32', order='F')
tadv = np.zeros((imax,jmax),dtype='float32', order='F')

ts_clim   = np.zeros((imax,jmax),dtype='float32', order='F')
pr_clim   = np.zeros((imax,jmax),dtype='float32', order='F')
shf_clim  = np.zeros((imax,jmax),dtype='float32', order='F')
lhf_clim  = np.zeros((imax,jmax),dtype='float32', order='F')
sw_clim   = np.zeros((imax,jmax),dtype='float32', order='F')
lw_clim   = np.zeros((imax,jmax),dtype='float32', order='F')
mse_clim  = np.zeros((imax,jmax),dtype='float32', order='F')
madv_clim = np.zeros((imax,jmax),dtype='float32', order='F')
omse_clim = np.zeros((imax,jmax),dtype='float32', order='F')
tadv_clim = np.zeros((imax,jmax),dtype='float32', order='F')


#   and corresponding variances
shf_var = undef
lhf_var = undef
sw_var  = undef
lw_var  = undef
mse_var = undef
madv_var= undef
omse_var= undef
tadv_var = undef

##   reading in climatology of MSE components
##   prefix3 - climatology
mse_clim, omse_clim, madv_clim, tadv_clim =  get_clima_in_OBS(imax, jmax, mse_clim, omse_clim, madv_clim, tadv_clim, prefix3, undef)

##   reading in  climatological  fluxes
##print( prefix3)
pr_clim, ts_clim, lhf_clim, shf_clim, sw_clim, lw_clim = get_clima_flux_in_OBS(imax, jmax,  pr_clim, ts_clim, lhf_clim, shf_clim, sw_clim, lw_clim, prefix3, undef)

######################
###      El Nino/La Nina composites   for default domain NINO3.4 + general domain
###      general domain set by slon1, slon2, slat1, slat2  enviromental variables
###      under  MSE_VAR  section in ~/ENSO_MSE/ENSO_MSE.py

slon1 =  os.environ["slon1"]
slon2 =  os.environ["slon2"]
slat1 =  os.environ["slat1"]
slat2 =  os.environ["slat2"]

slon1 =  float(slon1)
slon2 =  float(slon2)
slat1 =  float(slat1)
slat2 =  float(slat2)

now = datetime.datetime.now()
print ("   Seasonal ENSO MSE Variance composites started  " + now.strftime("%Y-%m-%d %H:%M") )

##   read in the El Nino composite data of MSE budget components + fluxes
mse, omse, madv,  tadv  =  get_data_in_OBS(imax, jmax, mse, omse, madv, tadv,  prefix1, undef)
pr, ts, lhf, shf, sw, lw = get_flux_in_OBS(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix1, undef)

###  anomalies calculations  El Nino case
pr   = get_anomaly(imax, jmax, zmax,  pr, pr_clim, undef)
ts   = get_anomaly(imax, jmax, zmax,  ts, ts_clim, undef)
shf  = get_anomaly(imax, jmax, zmax,  shf, shf_clim, undef)
lhf  = get_anomaly(imax, jmax, zmax,  lhf, lhf_clim, undef)
sw   = get_anomaly(imax, jmax, zmax,  sw, sw_clim, undef)
lw   = get_anomaly(imax, jmax, zmax,  lw, lw_clim, undef)
mse  = get_anomaly(imax, jmax, zmax,  mse, mse_clim, undef)
madv = get_anomaly(imax, jmax, zmax,  madv, madv_clim, undef)
omse = get_anomaly(imax, jmax, zmax,  omse, omse_clim, undef)
tadv = get_anomaly(imax, jmax, zmax,  tadv, tadv_clim, undef)

## variance and co-variance calculations for default domains Central and Eastern Pacific:
###        Central Pacif:
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, clon1, clon2, clat1, clat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

####    output written out
nameout  = 'MSE_variance_C.out'
write_out(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout1,  nameout,  undef)

####  repeat for the Eastern
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, elon1, elon2, elat1, elat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

####    output written out
nameout  = 'MSE_variance_E.out'
write_out(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout1,  nameout,  undef)

######################################################################3
##  the same calculations for user selected  domain
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, slon1, slon2, slat1, slat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

###  selected domain data output
write_out_general(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout1, undef)

########   La Nina case   similar as for El Nino case
######
##          reading data in   from prefix2 La Nina
#############################################
mse, omse, madv,  tadv  =  get_data_in_OBS(imax, jmax, mse, omse, madv,  tadv, prefix2, undef)
pr, ts, lhf, shf, sw, lw = get_flux_in_OBS(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix2, undef)

###    anomaly calculations
pr    = get_anomaly(imax, jmax, zmax,  pr, pr_clim, undef)
ts    = get_anomaly(imax, jmax, zmax,  ts, ts_clim, undef)
shf   = get_anomaly(imax, jmax, zmax,  shf, shf_clim, undef)
lhf   = get_anomaly(imax, jmax, zmax,  lhf, lhf_clim, undef)
sw    = get_anomaly(imax, jmax, zmax,  sw, sw_clim, undef)
lw    = get_anomaly(imax, jmax, zmax,  lw, lw_clim, undef)
mse   = get_anomaly(imax, jmax, zmax,  mse, mse_clim, undef)
madv  = get_anomaly(imax, jmax, zmax,  madv, madv_clim, undef)
omse  = get_anomaly(imax, jmax, zmax,  omse, omse_clim, undef)
tadv  = get_anomaly(imax, jmax, zmax,  tadv, tadv_clim, undef)

## variance and co-variance calculations for default domains Central and Eastern Pacific:
###        Central Pacif:
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, clon1, clon2, clat1, clat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

####    output written out   in prefix2 directory
nameout  = 'MSE_variance_C.out'
write_out(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout2,  nameout,  undef)

####  repeat for the Eastern
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, elon1, elon2, elat1, elat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

####    output written out
nameout  = 'MSE_variance_E.out'
write_out(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout2,  nameout,  undef)

##  calculation of variances and co-variances - user selected domain
shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var  =  moisture_variance(imax, jmax, zmax, slon1, slon2, slat1, slat2, lon, lat, plevs, ts, pr, shf, lhf, sw, lw, mse, madv, omse, tadv,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  undef)

write_out_general(imax, jmax, zmax,  shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var,  prefixout2, undef)

###########  plot the default domain NINO3.4 bar plots
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE_VAR/NCL/plot_bars_composite_OBS.ncl")

##      plotting for the  user selected domain :
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE_VAR/NCL_general/plot_bars_composite_OBS.ncl")

############
##################################
now = datetime.datetime.now()
print ("   Seasonal OBS ENSO MSE Variance composites finished  " + now.strftime("%Y-%m-%d %H:%M") )

print ("   resulting plots are located in : " +mse_var_dir )

print (" ")
##########################

