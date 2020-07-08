#
#      The code preprocesses the model input data to create
#      climatologies and corresponding anomalies.
#      Based on calculated anomalies, the code selects the El Nino/La Nina
#      years and construct corresponding seasonal composites.
#      Additionally,  seasonal correlations and regressions are calculated.
#      The final graphical outputs are placed in ~/wkdir/MDTF_$CASE directories.
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#       Reference:
#       Annamalai, H., J. Hafner, A. Kumar, and H. Wang, 2014:
#       A Framework for Dynamical Seasonal Prediction of Precipitation
#       over the Pacific Islands. J. Climate, 27 (9), 3272-3297,
#       doi:10.1175/JCLI-D-13-00379.1. IPRC-1041.
#
##      This package is distributed under the LGPLv3 license (see LICENSE.txt) 

import numpy as np
import sys
import math
import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from get_parameters_in import get_parameters_in
from get_nino_index import get_nino_index
from get_data_in import get_data_in
from get_flux_in import get_flux_in
from get_clima_in import get_clima_in
from get_flux_clima import get_flux_clima
from get_flux_in_24 import get_flux_in_24
from get_data_in_24 import get_data_in_24
from write_out import write_out

from get_correlation import get_correlation
from get_regression import get_regression

import datetime
from util import check_required_dirs
from get_season import get_season
from get_lon_lat_plevels_in import  get_lon_lat_plevels_in
from get_dimensions import get_dimensions
from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)
      The top driver code for the COMPOSITE module.

      The code preprocessed the model input data to create
      climatologies and corresponding anomalies for Observational dataset.

   ========================================================================
      input data are as follows:
      3-dimensional atmospheric variables dimensioned IMAX, JMAX, ZMAX
     HGT - geopotential height [m]
     UU  - U  wind  [m/s]
     VV  - V wind [m/s]
     TEMP  - temperature [K]
     SHUM - specific humidity [kg/kg]
     VVEL - vertical velocity [Pa/s]
 
    2-dimensional variables  (fluxes)
    outputs are 3-dimensional MSE components and its 2-dimensional 
      vertical integrals

      PRECIP precip. kg/m2/sec
      SST    Skin Surface Temperature   [K]
      SHF    sensible heat flux  [W/m2]
      LHF    latent heat flux [W/m2]
      SW     net SW flux [W/m2]  ( or individual SW flux components)
      LW     net LW flux [W/m2]  ( or individual LW flux components)
      
    all for full values.

     Additionally needed on input :
      imax  - x horizontal model dimension
      jmax -  y horizontal model dimension
         zmax -  z vertical model  dimension  and 
      PLEV - pressure levels [mb]

     missing values are flagged by UNDEF which is a large number

'''

now = datetime.datetime.now()
print("===============================================================")
print("   Start of Observational Composite Module  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

###     The domain dimensions imax, jmax, zmax and plevs  are  user selectable  
####    users can set the exact values in ~/var_code/ENSO_MSE/COMPOSITE.parameter.txt file 
###     along with  settings for ENSO selection,  season selection.
###     Currently imax, jmax, zmax dimensions  are set to default 180x90x17, 
###     but that can be user selected in parameter.txt file under ~/var_code/ENSO_MSE/COMPOSITE
### 
###     The code construct the 24 month ENSO evolution cycle Year(0)+Year(1) and 
###     the resulting plots are set fordefault  DJF season (Year(0) of the 24 month ENSO cycle
####    
####     

undef = float(-9999.)
undef2 = float(1.1e+20)
iundef = -9999.

##   the pointer to code directory 
prefix = os.environ["POD_HOME"] + "/COMPOSITE/"

## base path of all the files written/ready here
wkdir_obs = os.environ["ENSO_MSE_WKDIR_COMPOSITE"] + "/obs"

##  prefix1 =   input data (created by preprocess_OBS.py)
prefix1 = wkdir_obs  + "/netCDF/DATA/"
##   prefix2 =   input CLIMA (created by preprocess_OBS.py)
prefix2 = wkdir_obs + "/netCDF/CLIMA/"

###  output  
#old prefixout = os.environ["OBS_DATA"] + "/COMPOSITE/netCDF/"
#primary 
prefixout    =  wkdir_obs + "/netCDF/"
#if needed to share
#os.environ["ENSO_MSE_COMPOSITE_OBS_prefixout"] = prefixout

#   El Nino
prefixout1 = prefixout+"/ELNINO/"
#  La Nina out
prefixout2 = prefixout+"/LANINA/"
##  24 month evoution prefixes EL NINO
prefixout11 =  prefixout+"/24MONTH_ELNINO/BIN/"
#  La Nina out
prefixout22 = prefixout+"/24MONTH_LANINA/BIN/"

## SEASONAL  climatology output
prefixclim = prefixout

season_file = prefixout + "../season.txt"

flag0 = -1

season = "XXX"
season = get_season( season, prefix) 

if( os.path.isfile( season_file) ):
    print(" \t opening "+season_file)
    f = open(season_file , 'r')
    line = f.readline()
    line = line.strip()
    column = line.split()
    season_obs = column[0]
    f.close()
    ## print( season_obs ,  season) 
    if( season_obs == season ):
        flag0 = 1

if( flag0 == 1):
### print diagnostic message
    print "  The Observational Composites have been already completed  "
    print "  for  ", season, " season"
    print "   "
    exit()
    #### exit the routine 
else:
### print diagnostic message
    print "  The Observational Composites to be processed "
    print "    for  ", season, " season" 
    print " "
###   prepare the directories

### already checked in get_directories_OBS.py
##dirs_to_create = [prefix1, prefix2, prefixout1, prefixout2,prefixout11, prefixout22]
##check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)

rearth = 6378000.0

dummy1 = undef
dummy2 = undef
dummy3 = undef
dummy4 = undef
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
## optionally read in the parameters

###  years  read from pre-processed OBS  data   prefix1
##iy1 = os.environ["FIRSTYR"] 
##iy2 = os.environ["LASTYR"] 
if (os.path.exists(prefix1 + 'years.txt')):
	file = open(prefix1 + 'years.txt', 'r')
	line = file.readline()
	line = line.strip()
	column = line.split()
	iy1 =  float(column[0])
	line = file.readline()
	line = line.strip()
	column = line.split()
	iy2 = float(column[0]) 

print(" iy1 , iy2 " + iy1  + " " + iy2) 

model = "OBS" 
im1 = int( undef)
im2 = int( undef)  
#####
##   read in parameters    and the actual array dimensions imax, jmax, zmax, 
##    longitudes, latitudes,  plevels 
llon1, llon2, llat1, llat2, sigma, imindx1, imindx2,  composite, im1, im2, season,  composite24, regression, correlation,  undef, undef2 =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, imindx1, imindx2, composite, im1, im2, season, composite24, regression, correlation,  undef, undef2, prefix)

###  reading in the domensions and the actual lon/lat/plev data 
imax = 0
jmax = 0
zmax = 0
tmax24 = 24 
print("Calling get_dimensions for model: "+model)
imax, jmax, zmax = get_dimensions( imax,jmax, zmax, prefix1)

### print( imax,  " " , jmax , " " , zmax )

lon    = np.zeros(imax,dtype='float32')
lat    = np.zeros(jmax,dtype='float32')
plevs  = np.zeros(zmax,dtype='float32')

lon, lat, plevs = get_lon_lat_plevels_in( imax, jmax, zmax, lon, lat, plevs, prefix1)

ii1 = iundef
ii2 = iundef
jj1 = iundef
jj2 = iundef

### print diagnostic message 
print "  The following parameters are set in the Observational Composite Module Calculations  "
print "     the reference area for SST indices calculations is selected to:        "
print "     lon = ", llon1, " - ", llon2 , " E", "lat = ", llat1, " - ", llat2, "N" 
print "     ENSO indices  based on SST reference anomalies +/- ", sigma, " of SST sigma"
print "     Selected season  is : ", season  
print "     Selected year span for composites is : ", iy1,"/",  iy2 
print "     Selected model  : " , model
print "   "
print "    The following elements will be calculated  "
if( composite == 1):
    print "       Seasonal Composites for El Nino/La Nina years "
if( composite24 == 1):
    print "       2 Year life cycle of ENSO:  Year(0) and Year(1) " 
    print"                Year (0) = developing phase and Year(1) = decaying phase "
if( correlation == 1):
    print "       Reference area SST correlations will be calculated " 
if( regression == 1):
    print "      Regressions to reference area SST will be calculated "

print " " 

## composite years:
itmax = iy2 - iy1 + 1
ttmax1 = itmax
ttmax2 = itmax
years1 =  np.zeros((itmax), dtype='int32')
years2 =  np.zeros((itmax), dtype='int32')

####  declare the variable arrays
# 3d variables
uu = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vv = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
temp = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
hgt = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
shum = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvel = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')

# 2d varaibles - fluxes
ts  = np.zeros((imax,jmax),dtype='float32',  order='F')
pr  = np.zeros((imax,jmax),dtype='float32',  order='F')
shf = np.zeros((imax,jmax),dtype='float32',  order='F')
lhf = np.zeros((imax,jmax),dtype='float32',  order='F')
lw  = np.zeros((imax,jmax),dtype='float32',  order='F')
sw  = np.zeros((imax,jmax),dtype='float32',  order='F')
frad = np.zeros((imax,jmax),dtype='float32',  order='F')

## the same for the climatology
uuclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
tempclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
hgtclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
shumclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvelclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')

tsclim  = np.zeros((imax,jmax),dtype='float32',  order='F')
prclim  = np.zeros((imax,jmax),dtype='float32',  order='F')
shfclim = np.zeros((imax,jmax),dtype='float32',  order='F')
lhfclim = np.zeros((imax,jmax),dtype='float32',  order='F')
lwclim  = np.zeros((imax,jmax),dtype='float32',  order='F')
swclim  = np.zeros((imax,jmax),dtype='float32',  order='F')
fradclim = np.zeros((imax,jmax),dtype='float32',  order='F')

###  24 month variable arrays  for 2yr ENSO evolution
uu24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')
vv24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')
temp24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')
hgt24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')
shum24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')
vvel24 = np.zeros((imax,jmax,zmax, tmax24),dtype='float32',  order='F')

ts24  = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')
pr24  = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')
shf24 = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')
lhf24 = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')
lw24  = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')
sw24  = np.zeros((imax,jmax, tmax24),dtype='float32',  order='F')

###  correlations + regression
correl  = np.zeros((imax,jmax), dtype='float32',  order='F')
aregress = np.zeros((imax,jmax), dtype='float32',  order='F')

##  select season (imindx1, imindx2) and get the years for composites  (iyear)    
##   the NINO3.4 indices  based on area averaging ...  
##################################################3
#############   El Nino/La Nina indices selection

ii1, ii2, jj1, jj2, ttmax1, years1, ttmax2, years2 = get_nino_index(imax, jmax, lon, lat,  itmax,  iy1, iy2, imindx1, imindx2, llon1, llon2, llat1, llat2, ii1, ii2, jj1, jj2, sigma, ttmax1, ttmax2, years1,  years2,  prefix1, undef2)


######   CLIMATOLOGY:   reading pre-calculated total CLIMATOLOGY - output seasonal one
now = datetime.datetime.now()
print " Reading  Observational Climatologies  "  + now.strftime("%Y-%m-%d %H:%M")

hgtclim  = get_clima_in(imax, jmax, zmax,  im1, im2, "Z_clim",  hgtclim, prefix2,  undef2)
uuclim   = get_clima_in(imax, jmax, zmax, im1, im2, "U_clim",   uuclim , prefix2,  undef2)
vvclim   = get_clima_in(imax, jmax, zmax, im1, im2, "V_clim",   vvclim,  prefix2,  undef2)
tempclim = get_clima_in(imax, jmax, zmax, im1, im2, "T_clim",   tempclim, prefix2, undef2)
shumclim = get_clima_in(imax, jmax, zmax, im1, im2, "Q_clim",   shumclim, prefix2, undef2)
vvelclim = get_clima_in(imax, jmax, zmax, im1, im2, "OMG_clim", vvelclim, prefix2, undef2)
## and the clima fluxes  average over im1, im2
prclim  = get_flux_clima(imax, jmax, im1, im2, "PR_clim",   prclim,  prefix2, undef2)
tsclim  = get_flux_clima(imax, jmax, im1, im2, "TS_clim",   tsclim,  prefix2, undef2)
shfclim = get_flux_clima(imax, jmax, im1, im2, "SHF_clim",  shfclim, prefix2, undef2)
lhfclim = get_flux_clima(imax, jmax, im1, im2, "LHF_clim",  lhfclim, prefix2, undef2)
swclim  = get_flux_clima(imax, jmax, im1, im2, "SW_clim",   swclim,  prefix2, undef2)
lwclim  = get_flux_clima(imax, jmax, im1, im2, "LW_clim",   lwclim,  prefix2, undef2)

###  write seasonal climatology for further processing 
write_out( "Z_clim",    hgtclim,  prefixclim)
write_out( "U_clim",     uuclim,  prefixclim)
write_out( "V_clim",     vvclim,  prefixclim)
write_out( "T_clim",   tempclim,  prefixclim)
write_out( "Q_clim",   shumclim,  prefixclim)
write_out( "OMG_clim", vvelclim,  prefixclim)
## similarly the fluxes
write_out(  "PR_clim",   prclim,  prefixclim)
write_out(  "TS_clim",   tsclim,  prefixclim)
write_out(  "SHF_clim", shfclim,  prefixclim)
write_out(  "LHF_clim", lhfclim,  prefixclim)
write_out(  "LW_clim",   lwclim,  prefixclim)
write_out(  "SW_clim",   swclim,  prefixclim)
##   add Frad
lwclim = np.ma.masked_greater_equal(lwclim, undef, copy=False)
swclim = np.ma.masked_greater_equal(swclim, undef, copy=False)
fradclim = lwclim  +  swclim
write_out(  "FRAD_clim", fradclim,   prefixclim)

## 

###  composite module -  selected in  parameter.txt file 
if(  composite == 1):

##                reading the ENSO selected seasons in based on  
###                   output from get_nino_index  routine 
    now = datetime.datetime.now()
    print "  Starting Seasonal Observational ELNINO composites: "  + now.strftime("%Y-%m-%d %H:%M")
    
    hgt  = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "Z",  hgt, prefix1,  undef2)
    uu   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "U",  uu, prefix1,  undef2)
    vv   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "V",  vv, prefix1,  undef2)
    temp = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "T",  temp, prefix1, undef2)
    shum = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "Q",  shum, prefix1, undef2)
    vvel = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "OMG",  vvel, prefix1,  undef2)

## test composites and write out

    write_out(  "Z",  hgt,  prefixout1)
    write_out(  "U",   uu,  prefixout1)
    write_out(  "V",   vv,  prefixout1)
    write_out(  "T",  temp,  prefixout1)
    write_out(  "Q",  shum,  prefixout1)
    write_out(  "OMG", vvel,  prefixout1)

###  read in and composite the fluxes 
    pr  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "PR",  pr, prefix1,  undef2)
    ts  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "TS",  ts, prefix1,  undef2)
    shf = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "SHF",  shf, prefix1, undef2)
    lhf = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "LHF",  lhf, prefix1,  undef2)
    sw  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "SW",  sw, prefix1,  undef2)
    lw  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "LW",  lw, prefix1,  undef2)

##   add Frad 
    frad = sw + lw
    write_out(  "FRAD", frad,   prefixout1)

## output  fluxes  in corresponding directory 
    write_out( "PR",  pr,   prefixout1)
    write_out( "TS",  ts,   prefixout1)
    write_out( "SHF", shf,  prefixout1)
    write_out( "LHF", lhf,  prefixout1)
    write_out( "LW",  lw,   prefixout1)
    write_out( "SW",  sw,   prefixout1)

########   similarly the same for LA NINA composites
    now = datetime.datetime.now()
    print "  Starting Seasonal Observational LANINA composites: "  + now.strftime("%Y-%m-%d %H:%M")

    hgt  = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "Z",  hgt, prefix1, undef2)
    uu   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "U",  uu, prefix1,  undef2)
    vv   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "V",  vv, prefix1,  undef2)
    temp = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "T",  temp, prefix1, undef2)
    shum = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "Q",  shum, prefix1, undef2)
    vvel = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "OMG",  vvel, prefix1,  undef2)
## write out 
    write_out(  "Z",  hgt,  prefixout2)
    write_out(  "U",   uu,  prefixout2)
    write_out(  "V",   vv,  prefixout2)
    write_out(  "T",  temp,  prefixout2)
    write_out(  "Q",  shum,  prefixout2)
    write_out(  "OMG", vvel,  prefixout2)

###   LA NINA composite   fluxes 
 
    pr = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "PR",  pr, prefix1, undef2)
    ts  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "TS",  ts, prefix1, undef2)
    shf = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "SHF",  shf, prefix1, undef2)
    lhf = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "LHF",  lhf, prefix1, undef2)
    sw  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "SW",  sw, prefix1, undef2)
    lw  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "LW",  lw, prefix1, undef2)

##   add Frad
    frad = sw + lw
    write_out( "FRAD", frad,   prefixout2)

## output La NINA composites  in corresponding directory
    write_out( "PR",  pr,   prefixout2)
    write_out( "TS",  ts,   prefixout2)
    write_out( "SHF", shf,  prefixout2)
    write_out( "LHF", lhf,  prefixout2)
    write_out( "LW",  lw,   prefixout2)
    write_out( "SW",  sw,   prefixout2)

####  make the plots
    print( "finished Observational composite calculation  ")
    
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_composite_all_OBS.ncl")

    now = datetime.datetime.now()
    print "   Seasonal Observational ENSO composites completed:  " + now.strftime("%Y-%m-%d %H:%M")
    print "   plots of ENSO seasonal composites finished  "
    print "   resulting plots are located in : " +  wkdir_obs
    print "   with prefix composite  + ELNINO/LANINA +  variable name "
    
print " "    
####################################
########### all  data in ELNINO/LANINA composite + CLIMATOLOGY  
###   24 month  ENSO evolution if selected in parameters.txt file 
###    years 0 ( building phase of ENSO) and year 1 (decaying phase) are calculated

if( composite24 == 1):
    now = datetime.datetime.now()
    print "  Calculations of Observational 2 Year ENSO evolution begins "  + now.strftime("%Y-%m-%d %H:%M")
    print "  Depending on data time span and data volume this routine can take up 30-40 mins."
    print "  Approximately 5-10  minutes per one 3-dimensional variable   "

###   El Nino  case :
    hgt24  = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "Z", tmax24, hgt24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable Z completed " + now.strftime("%Y-%m-%d %H:%M")

    uu24   = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2,  "U",  tmax24, uu24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable U completed " + now.strftime("%Y-%m-%d %H:%M")

    vv24   = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "V", tmax24, vv24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable V completed " + now.strftime("%Y-%m-%d %H:%M")

    temp24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "T",  tmax24, temp24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable T completed " + now.strftime("%Y-%m-%d %H:%M")

    shum24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "Q",  tmax24, shum24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable Q completed " + now.strftime("%Y-%m-%d %H:%M")

    vvel24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "OMG", tmax24,   vvel24, prefix1, prefix2, undef2)
    now = datetime.datetime.now()
    print"  ELNINO: variable OMG completed " + now.strftime("%Y-%m-%d %H:%M")
##     24 month evolution output files written

    write_out( "Z", hgt24, prefixout11)
    write_out( "U", uu24, prefixout11)
    write_out( "V", vv24, prefixout11)
    write_out( "T", temp24, prefixout11)
    write_out( "Q", shum24, prefixout11)
    write_out( "OMG", vvel24, prefixout11)

#  the same for fluxes 
    pr24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "PR", tmax24,  pr24, prefix1, prefix2,  undef2)
    ts24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "TS", tmax24, ts24, prefix1, prefix2,  undef2)
    shf24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "SHF", tmax24, shf24, prefix1, prefix2,  undef2)
    lhf24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "LHF", tmax24, lhf24, prefix1, prefix2,  undef2)
    sw24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "SW",tmax24,  sw24, prefix1, prefix2,  undef2)
    lw24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "LW", tmax24, lw24, prefix1, prefix2,  undef2)
    
    now = datetime.datetime.now()
    print"  ELNINO: all flux variables completed " + now.strftime("%Y-%m-%d %H:%M")

#  write out   fluxes
    write_out(  "PR",  pr24, prefixout11)
    write_out( "TS",  ts24, prefixout11)
    write_out( "SHF",shf24, prefixout11)
    write_out( "LHF",lhf24, prefixout11)
    write_out( "LW",  lw24, prefixout11)
    write_out( "SW",  sw24, prefixout11)
###   copy the grads control files 
##    os.system("cp " + os.environ["POD_HOME"]+"/COMPOSITE/CTL/*.ctl "+ prefixout11  )

##########################
####    La Nina 4 evolution :
    hgt24  = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "Z", tmax24, hgt24, prefix1, prefix2,   undef2)
    now = datetime.datetime.now()
    print"  LANINA: variable  Z completed " + now.strftime("%Y-%m-%d %H:%M")

    uu24   = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "U",  tmax24, uu24, prefix1,  prefix2,  undef2)
    now = datetime.datetime.now()
    print"  LANINA: variable  U completed " + now.strftime("%Y-%m-%d %H:%M")

    vv24   = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "V", tmax24, vv24, prefix1,prefix2,   undef2)
    now = datetime.datetime.now()
    print"  LANINA: variable  V completed " + now.strftime("%Y-%m-%d %H:%M")

    temp24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "T",  tmax24, temp24, prefix1, prefix2,   undef2)
    now = datetime.datetime.now()
    print"  LANINA: variable  T completed " + now.strftime("%Y-%m-%d %H:%M")

    shum24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "Q",  tmax24, shum24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()    
    print"  LANINA: variable  Q completed " + now.strftime("%Y-%m-%d %H:%M")

    vvel24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "OMG", tmax24,   vvel24, prefix1, prefix2, undef2) 
    now = datetime.datetime.now()
    print"  LANINA: variable  OMG completed " + now.strftime("%Y-%m-%d %H:%M")
###  write output 
    write_out(  "Z", hgt24, prefixout22)
    write_out(  "U", uu24, prefixout22)
    write_out(  "V", vv24, prefixout22)
    write_out(  "T", temp24, prefixout22)
    write_out(  "Q", shum24, prefixout22)
    write_out(  "OMG", vvel24, prefixout22)
##  fluxes     calculation and output 
    pr24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2,  "PR", tmax24,  pr24, prefix1, prefix2,   undef2)
    ts24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "TS", tmax24, ts24, prefix1, prefix2,  undef2)
    shf24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "SHF", tmax24, shf24, prefix1, prefix2,   undef2)
    lhf24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "LHF", tmax24, lhf24, prefix1, prefix2,  undef2)
    sw24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "SW",tmax24,  sw24, prefix1, prefix2,  undef2)
    lw24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "LW", tmax24, lw24, prefix1, prefix2,  undef2)
    now = datetime.datetime.now()
    print"  LANINA: all flux variables completed " + now.strftime("%Y-%m-%d %H:%M")
#  write out 
    write_out(  "PR",  pr24, prefixout22)
    write_out(  "TS",  ts24, prefixout22)
    write_out(  "SHF",shf24, prefixout22)
    write_out(  "LHF",lhf24, prefixout22)
    write_out(  "LW",  lw24, prefixout22)
    write_out(  "SW",  sw24, prefixout22)
###    convert binaries to NetCDF
    generate_ncl_call(os.environ["POD_HOME"] +  "/COMPOSITE/NCL_CONVERT/write_24month_netcdf_OBS.ncl")

    print "  Calculation of observational data 2 year ENSO evolution completed  "
    print "  Resulting  data are located in : " + wkdir_obs +"/netCDF/24MONTH_ELNINO/"
    print "   and in in : " +wkdir_obs + "netCDF/24MONTH_ELNINO/"
    print "   only anomaly data are generated in this step   "

print " " 
##  endif 24 month composite

##########   seasonal correlation, calculations with seasonal NINO3.4 SST anomalies 
if( correlation == 1):
    now = datetime.datetime.now()
    print "   Seasonal  SST  correlations started  " + now.strftime("%Y-%m-%d %H:%M")
##      correlations with selected variables  El Nino case 
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "PR", "TS", correl, prefix1, prefix2,  undef2)
## output as data : 
    write_out(  "CORR_PR",  correl,   prefixout)
### 
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "SHF", "TS", correl, prefix1, prefix2,  undef2)
## output as data :
    write_out( "CORR_SHF",  correl,   prefixout)
#####    
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "LHF", "TS", correl, prefix1, prefix2,  undef2)
## output as data : 
    write_out(  "CORR_LHF",  correl,   prefixout)
####    
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "LW", "TS", correl, prefix1, prefix2,  undef2)
## output as data :
    write_out( "CORR_LW",  correl,   prefixout)
####   
    correl =  get_correlation(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "SW", "TS", correl, prefix1, prefix2, undef2)
## output   correlation data 
    write_out(   "CORR_SW",  correl,   prefixout)
###   plot correlations 
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_correlation_all_OBS.ncl")

    print "   Seasonal Observational SST  correlations completed  "
    print "   plots of  seasonal correlations  finished  "
    print "   resulting plots are located in : " + wkdir_obs
    print "     with prefix correlation + variable name "

print " "     
###  plotting routine  below:
###  call NCL plotting script    plot_composite_SST.ncl

##     regression calculation, if selected in parameters.txt  
##      regression of NINO3.4 SST anomaly on selected variables

if( regression == 1):
    now = datetime.datetime.now()
    print "   Seasonal Observational SST  regression calculations started  " + now.strftime("%Y-%m-%d %H:%M")
###  
    aregress = get_regression(imax, jmax, zmax, iy1, iy2,  im1, im2, ii1, ii2, jj1, jj2, "PR", "TS", aregress, prefix1, prefix2,  undef2)
##  output in composite directory 
    write_out(  "REGRESS_PR",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "SHF", "TS", aregress, prefix1, prefix2,  undef2)
##  output in composite directory
    write_out(   "REGRESS_SHF",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "LHF", "TS", aregress, prefix1, prefix2,  undef2)
##  output in composite directory
    write_out(  "REGRESS_LHF",  aregress,   prefixout)
###
    aregress = get_regression(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "LW", "TS", aregress, prefix1, prefix2,  undef2)
##  output in composite directory
    write_out(  "REGRESS_LW",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "SW", "TS", aregress, prefix1, prefix2,  undef2)
##  output 
    write_out(  "REGRESS_SW",  aregress,   prefixout)

##     plotting the regressions 
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_regression_all_OBS.ncl")

    print "   Seasonal Observational SST  regressions completed  "
    print "   plots of seasonal regressions  finished  "
    print "   resulting plots are located in : " + wkdir_obs
    print "     with prefix  regression  +  variable name "

#
##  print the flag to  external file so once season completed  it could be skipped
season_file =  wkdir_obs +"/season.txt"
f = open(season_file , 'w')
f.write(season)
f.close()

now = datetime.datetime.now()
print "   " 
print " ==================================================================="
print " Observational Composite Module Finished  " +  now.strftime("%Y-%m-%d %H:%M")
print " ==================================================================="
### 
