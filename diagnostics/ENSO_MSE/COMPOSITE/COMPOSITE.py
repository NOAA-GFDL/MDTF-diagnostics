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
#       last update : 2020-10-05
#
##      This package is distributed under the LGPLv3 license (see LICENSE.txt) 

import numpy as np
import sys
import math
import os

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

import time
import datetime

import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


from util import check_required_dirs
from util import check_required_dirs
from get_lon_lat_plevels_in import  get_lon_lat_plevels_in
from get_dimensions import get_dimensions
from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)
      The top driver code for the COMPOSITE module.

      The code preprocessed the model input data to create
      climatologies and corresponding anomalies.

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
print("=========== COMPOSITE.py =======================================")
print("   Start of Composite Module calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

### DRB: For debugging purposes, I added test_mode to flip switches within this
### script to turn off things that have already run. Some pieces can take
### several hours. To use, set test_mode = True, then search below to turn
### on/off exactly what you want
test_mode = False

if ( test_mode ):
        print(" WARNING: COMPOSITE.py in test_mode. Some portions of the code may be ommited")

### 
###     The code construct the 24 month ENSO evolution cycle Year(0)+Year(1) and 
###     the resulting plots are set for default  DJF season (Year(0) of the 24 month ENSO cycle
####    
####     

undef = float(1.1e+20)
iundef = -9999

##   the pointer to code directory 
prefix = os.path.join(os.environ["POD_HOME"],"COMPOSITE")

## base path of all the files written/read here
wkdir_model = os.path.join(os.environ["ENSO_MSE_WKDIR_COMPOSITE"],"model")

##  prefix1 =   input data (to other parts of package, really output dir too)
prefix1 =   os.path.join(wkdir_model,"netCDF","DATA")
##   prefix2 =   input CLIMA
prefix2 =   os.path.join(wkdir_model,"netCDF","CLIMA")

###  output  
prefixout = os.path.join(wkdir_model,"netCDF")

#   El Nino
prefixout1 = os.path.join(wkdir_model, "netCDF","ELNINO")
#  La Nina out
prefixout2 = os.path.join(wkdir_model, "netCDF","LANINA")
##  24 month evoution prefixes EL NINO
prefixout11 = os.path.join(wkdir_model, "netCDF","24MONTH_ELNINO")
prefixout111 = os.path.join(wkdir_model, "netCDF","24MONTH_ELNINO", "BIN")
#  La Nina out
prefixout22 = os.path.join(wkdir_model, "netCDF", "24MONTH_LANINA")
prefixout222 = os.path.join(wkdir_model, "netCDF", "24MONTH_LANINA", "BIN")

## climatology output
prefixclim = prefixout

###  the directory check ran already in get_directories.py
## dirs_to_create = [prefix1,prefix2,prefixout1,prefixout2, prefixout11, prefixout22, prefixout111, prefixout222]
## check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)

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

iy1 = os.environ["FIRSTYR"] 
iy2 = os.environ["LASTYR"] 
iy1 = int(iy1)
iy2 = int(iy2)

model = os.environ["CASENAME"] 
im1 = int( undef)
im2 = int( undef)  
#####
##   read in parameters    and the actual array dimensions imax, jmax, zmax, 
##    longitudes, latitudes,  plevels 
llon1, llon2, llat1, llat2, sigma, imindx1, imindx2,  composite, im1, im2, season,  composite24, regression, correlation,  undef =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, imindx1, imindx2, composite, im1, im2, season, composite24, regression, correlation,  undef, prefix)

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
print ("  The following parameters are set in the Composite Module Calculations  ")
print ("      the reference area for SST indices calculations is selected to:        ")
print ("      lon = ", llon1, " - ", llon2 , " E", "lat = ", llat1, " - ", llat2, "N" )
print ("      ENSO indices  based on SST reference anomalies +/- ", sigma, " of SST sigma")
print ("      Selected season  is : ", season   )
print ("      Selected year span for composites is : ", iy1,"/",  iy2 )
print ("      Selected model  : " , model  )
print ("   " )
print ("    The following elements will be calculated  " )
if( composite == 1):
    print ("       Seasonal Composites for El Nino/La Nina years ")
if( composite24 == 1):
    print ("       2 Year life cycle of ENSO:  Year(0) and Year(1) " )
    print ("                Year (0) = developing phase and Year(1) = decaying phase ")
if( correlation == 1):
    print ("       Reference area SST correlations will be calculated ") 
if( regression == 1):
    print ("      Regressions to reference area SST will be calculated ")

print (" ") 

## composite years:
itmax = iy2 - iy1 + 1
ttmax1 = 0
ttmax2 = 0
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

ii1, ii2, jj1, jj2, ttmax1, years1, ttmax2, years2 = get_nino_index(imax, jmax, lon, lat,  itmax,  iy1, iy2, imindx1, imindx2, llon1, llon2, llat1, llat2, ii1, ii2, jj1, jj2, sigma, ttmax1, ttmax2, years1,  years2,  prefix1, undef)

## added 2020-09-08  check for the selected years - the time series needs to be long enough
##  to capture El Nino/La Nina events
if( ttmax1 <= 0 ):
    print ("WARNING: The number of  El Nino events is : ", ttmax1 )
    print ("At least 1 event is needed for calculation ")
    print ("and at least 2 events for sucessfull completion")
    print ("Please, extend the time span of your Model data")
    exit()

if( ttmax1 == 1 ):
    print ("WARNING: The number of  El Nino events is : ", ttmax1)
    print ("At least 2 events are needed for successful  calculations ")
    print ("The code will run just with 1 event, but with limited results")
    print ("You may  extend the time span of your Model data")

if( ttmax1 >= 2 ):
    print ("The number of  El Nino events is : ", ttmax1)
    print ("The code will proceed  with this number of El Nino events")
    time.sleep(4.)
 
if( ttmax2 <= 0 ):
    print ("WARNING: The number of La Nina events is : ",  ttmax2)
    print ("At least 1 event is needed for calculation ")
    print ("and at least 2 events for sucessfull completion")
    print ("Please, extend the time span of your Model data")
    exit()

if( ttmax2 == 1 ):
    print ("WARNING: The number of La Nina events is : ", ttmax2)
    print ("At least 2 events are needed for successful  calculations ")
    print ("The code will run just with 1 event, but with limited results")
    print ("You may  extend the time span of your Model data")

if( ttmax2 >= 2 ):
    print ("The number of  La Nina events is : ", ttmax2)
    print ("The code will proceed  with this number of La Nina events")
    time.sleep(4.)

######   CLIMATOLOGY:   reading pre-calculated total CLIMATOLOGY - output seasonal one
now = datetime.datetime.now()

if ( test_mode ):
        print("WARNING: test_mode not reading climatologies")
else:
        print (" Reading Climatologies  "  + now.strftime("%Y-%m-%d %H:%M"))

        hgtclim  = get_clima_in(imax, jmax, zmax,  im1, im2, "zg",  hgtclim, prefix2, undef)
        uuclim   = get_clima_in(imax, jmax, zmax, im1, im2, "ua",   uuclim , prefix2, undef)
        vvclim   = get_clima_in(imax, jmax, zmax, im1, im2, "va",   vvclim,  prefix2, undef)
        tempclim = get_clima_in(imax, jmax, zmax, im1, im2, "ta",   tempclim, prefix2, undef)
        shumclim = get_clima_in(imax, jmax, zmax, im1, im2, "hus",   shumclim, prefix2,  undef)
        vvelclim = get_clima_in(imax, jmax, zmax, im1, im2, "wap", vvelclim, prefix2, undef)
        ## and the clima fluxes  average over im1, im2
        prclim  = get_flux_clima(imax, jmax, im1, im2, "pr",   prclim,  prefix2,  undef)
        tsclim  = get_flux_clima(imax, jmax, im1, im2, "ts",   tsclim,  prefix2,  undef)
        shfclim = get_flux_clima(imax, jmax, im1, im2, "hfss",  shfclim, prefix2,  undef)
        lhfclim = get_flux_clima(imax, jmax, im1, im2, "hfls",  lhfclim, prefix2,  undef)
        swclim  = get_flux_clima(imax, jmax, im1, im2, "sw",   swclim,  prefix2,  undef)
        lwclim  = get_flux_clima(imax, jmax, im1, im2, "lw",   lwclim,  prefix2,  undef)
        
        ###  write seasonal climatology for further processing 
        write_out( "Z_clim",    hgtclim,  prefixclim)
        write_out( "U_clim",     uuclim,  prefixclim)
        write_out( "V_clim",     vvclim,  prefixclim)
        write_out( "T_clim",   tempclim,  prefixclim)
        write_out( "Q_clim",   shumclim,  prefixclim)
        write_out(  "OMG_clim", vvelclim,  prefixclim)
        ## similarly the fluxes
        write_out(  "PR_clim",   prclim,  prefixclim)
        write_out(  "TS_clim",   tsclim,  prefixclim)
        write_out(  "SHF_clim", shfclim,  prefixclim)
        write_out(  "LHF_clim", lhfclim,  prefixclim)
        write_out(  "LW_clim",   lwclim,  prefixclim)
        write_out(  "SW_clim",   swclim,  prefixclim)
        ##   add Frad
        #lwclim = np.ma.masked_greater_equal(lwclim, undef, copy=False)
        #swclim = np.ma.masked_greater_equal(swclim, undef, copy=False)
        fradclim = lwclim  +  swclim
        write_out(  "FRAD_clim", fradclim,   prefixclim)

## 

if ( test_mode ):
        print ("WARNING: test_mode setting composite = 0 to prevent calculations")
        composite = 0

###  composite module -  selected in  parameter.txt file 
if(  composite == 1):

##                reading the ENSO selected seasons in based on  
###                   output from get_nino_index  routine 
    now = datetime.datetime.now()
    print ("  Starting Seasonal ELNINO composites: "  + now.strftime("%Y-%m-%d %H:%M") )
    
    hgt  = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "zg",  hgt, prefix1, undef)
    uu   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "ua",  uu, prefix1, undef)
    vv   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "va",  vv, prefix1, undef)
    temp = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "ta",  temp, prefix1, undef)
    shum = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "hus",  shum, prefix1, undef)
    vvel = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "wap",  vvel, prefix1, undef)

## test composites and write out

    write_out(  "Z",  hgt,  prefixout1)
    write_out(  "U",   uu,  prefixout1)
    write_out(  "V",   vv,  prefixout1)
    write_out(  "T",  temp,  prefixout1)
    write_out(  "Q",  shum,  prefixout1)
    write_out(  "OMG", vvel,  prefixout1)

###  read in and composite the fluxes 
    pr  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "pr",  pr, prefix1,  undef)
    ts  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "ts",  ts, prefix1,  undef)
    shf = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "hfss",  shf, prefix1, undef)
    lhf = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "hfls",  lhf, prefix1, undef)
    sw  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "sw",  sw, prefix1,  undef)
    lw  = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, "lw",  lw, prefix1,  undef)

##   add Frad 
    frad = sw + lw
    write_out( "FRAD", frad,   prefixout1)

## output  fluxes  in corresponding directory 
    write_out( "PR",  pr,   prefixout1)
    write_out( "TS",  ts,   prefixout1)
    write_out( "SHF", shf,  prefixout1)
    write_out( "LHF", lhf,  prefixout1)
    write_out( "LW",  lw,   prefixout1)
    write_out( "SW",  sw,   prefixout1)

########   similarly the same for LA NINA composites
    now = datetime.datetime.now()
    print ("  Starting Seasonal LANINA composites: "  + now.strftime("%Y-%m-%d %H:%M") )

    hgt  = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "zg",  hgt, prefix1, undef)
    uu   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "ua",  uu, prefix1, undef)
    vv   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "va",  vv, prefix1, undef)
    temp = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "ta",  temp, prefix1, undef)
    shum = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "hus",  shum, prefix1, undef)
    vvel = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "wap",  vvel, prefix1, undef)
## write out 
    write_out( "Z",  hgt,  prefixout2)
    write_out( "U",   uu,  prefixout2)
    write_out( "V",   vv,  prefixout2)
    write_out( "T",  temp,  prefixout2)
    write_out( "Q",  shum,  prefixout2)
    write_out( "OMG", vvel,  prefixout2)

###   LA NINA composite   fluxes 
 
    pr = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "pr",  pr, prefix1,  undef)
    ts  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "ts",  ts, prefix1,  undef)
    shf = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "hfss",  shf, prefix1,  undef)
    lhf = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "hfls",  lhf, prefix1,  undef)
    sw  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "sw",  sw, prefix1,  undef)
    lw  = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, "lw",  lw, prefix1,  undef)

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
    print( "finished composite calculation  ")
    
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_composite_all.ncl")

    now = datetime.datetime.now()
    print ("   Seasonal ENSO composites completed:  " + now.strftime("%Y-%m-%d %H:%M") )
    print ("   plots of ENSO seasonal composites finished  ")
    print ("   resulting plots are located in : " + wkdir_model)
    print ("   with prefix composite  + ELNINO/LANINA +  variable name " )

    
print (" ")
####################################3333
########### all  data in ELNINO/LANINA composite + CLIMATOLOGY  
###   24 month  ENSO evolution if selected in parameters.txt file 
###    years 0 ( building phase of ENSO) and year 1 (decaying phase) are calculated

if (test_mode) :
        print ("WARNING: test_mode setting composite24 = 0 to prevent calculations")
        composite24 = 0

if( composite24 == 1):
    now = datetime.datetime.now()
    print ("  Calculations of  2 Year ENSO evolution begins "  + now.strftime("%Y-%m-%d %H:%M") )
    print ("  Depending on data time span and data volume this routine can take up 30-40 mins.")
    print ("  Approximately 5-10  minutes per one 3-dimensional variable   ")

###   El Nino  case :
    hgt24  = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "zg", tmax24, hgt24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable Z completed " + now.strftime("%Y-%m-%d %H:%M") )

    uu24   = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2,  "ua",  tmax24, uu24, prefix1, prefix2, undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable U completed " + now.strftime("%Y-%m-%d %H:%M") )

    vv24   = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "va", tmax24, vv24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable V completed " + now.strftime("%Y-%m-%d %H:%M") )

    temp24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "ta",  tmax24, temp24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable T completed " + now.strftime("%Y-%m-%d %H:%M") )

    shum24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "hus",  tmax24, shum24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable Q completed " + now.strftime("%Y-%m-%d %H:%M"))

    vvel24 = get_data_in_24(imax, jmax, zmax, ttmax1, years1, iy2, "wap", tmax24,   vvel24, prefix1, prefix2, undef)
    now = datetime.datetime.now()
    print ("  ELNINO: variable OMG completed " + now.strftime("%Y-%m-%d %H:%M") )
##     24 month evolution output files written
    write_out( "zg", hgt24, prefixout111)
    write_out( "ua", uu24, prefixout111)
    write_out( "va", vv24, prefixout111)
    write_out( "ta", temp24, prefixout111)
    write_out( "hus", shum24, prefixout111)
    write_out( "wap", vvel24, prefixout111)

#  the same for fluxes 
    pr24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "pr", tmax24,  pr24, prefix1, prefix2, undef)
    ts24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "ts", tmax24, ts24, prefix1, prefix2, undef)
    shf24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "hfss", tmax24, shf24, prefix1, prefix2, undef)
    lhf24 = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "hfls", tmax24, lhf24, prefix1, prefix2, undef)
    sw24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "sw",tmax24,  sw24, prefix1, prefix2, undef)
    lw24  = get_flux_in_24(imax, jmax, ttmax1, years1, iy2, "lw", tmax24, lw24, prefix1, prefix2, undef)
    
    now = datetime.datetime.now()
    print ("  ELNINO: all flux variables completed " + now.strftime("%Y-%m-%d %H:%M") )

#  write out   fluxes
    write_out( "pr",  pr24, prefixout111)
    write_out( "ts",  ts24, prefixout111)
    write_out( "hfss",shf24, prefixout111)
    write_out( "hfls",lhf24, prefixout111)
    write_out( "lw",  lw24, prefixout111)
    write_out( "sw",  sw24, prefixout111)
###   copy the grads control files 
###    os.system("cp " + os.environ["POD_HOME"]+"/COMPOSITE/CTL/*.ctl "+ prefixout11  )

##########################
####    La Nina 4 evolution :
    hgt24  = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "zg", tmax24, hgt24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  LANINA: variable  Z completed " + now.strftime("%Y-%m-%d %H:%M") )

    uu24   = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "ua",  tmax24, uu24, prefix1,  prefix2, undef)
    now = datetime.datetime.now()
    print ("  LANINA: variable  U completed " + now.strftime("%Y-%m-%d %H:%M") )

    vv24   = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "va", tmax24, vv24, prefix1,prefix2,  undef)
    now = datetime.datetime.now()
    print ("  LANINA: variable  V completed " + now.strftime("%Y-%m-%d %H:%M") )

    temp24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "ta",  tmax24, temp24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  LANINA: variable  T completed " + now.strftime("%Y-%m-%d %H:%M") )

    shum24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "hus",  tmax24, shum24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()    
    print ("  LANINA: variable  Q completed " + now.strftime("%Y-%m-%d %H:%M") )

    vvel24 = get_data_in_24(imax, jmax, zmax, ttmax2, years2, iy2, "wap", tmax24,   vvel24, prefix1, prefix2,  undef) 
    now = datetime.datetime.now()
    print ("  LANINA: variable  OMG completed " + now.strftime("%Y-%m-%d %H:%M") )
###  write output 
    write_out( "zg", hgt24, prefixout222)
    write_out( "ua", uu24, prefixout222)
    write_out( "va", vv24, prefixout222)
    write_out( "ta", temp24, prefixout222)
    write_out( "hus", shum24, prefixout222)
    write_out( "wap", vvel24, prefixout222)
##  fluxes     calculation and output 
    pr24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2,  "pr", tmax24,  pr24, prefix1, prefix2,  undef)
    ts24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "ts", tmax24, ts24, prefix1, prefix2, undef)
    shf24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "hfss", tmax24, shf24, prefix1, prefix2,  undef)
    lhf24 = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "hfls", tmax24, lhf24, prefix1, prefix2, undef)
    sw24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "sw",tmax24,  sw24, prefix1, prefix2, undef)
    lw24  = get_flux_in_24(imax, jmax, ttmax2, years2, iy2, "lw", tmax24, lw24, prefix1, prefix2,  undef)
    now = datetime.datetime.now()
    print ("  LANINA: all flux variables completed " + now.strftime("%Y-%m-%d %H:%M") )
#  write out 
    write_out(  "pr",  pr24, prefixout222)
    write_out(  "ts",  ts24, prefixout222)
    write_out(  "hfss",shf24, prefixout222)
    write_out(  "hfls",lhf24, prefixout222)
    write_out(  "lw",  lw24, prefixout222)
    write_out(  "sw",  sw24, prefixout222)
###    convert binaries to NetCDF 
    generate_ncl_call(os.environ["POD_HOME"] +  "/COMPOSITE/NCL_CONVERT/write_24month_netcdf.ncl")

    print ("   calculation of 2 year  ENSO evolution completed  " )
    print ("   resulting  data are   located in : " + wkdir_model + "/netCDF/24MONTH_ELNINO/" )
    print ("   and in : " + wkdir_model + "/netCDF/24MONTH_ELNINO/" )
    print ("   only anomaly data are generated in this step   " )

print (" " )
##  endif 24 month composite

##########   seasonal correlation, calculations with seasonal NINO3.4 SST anomalies 

if (test_mode) :
        correlation = 0
        print ("WARNING: test_mode setting correlation = ",correlation," to prevent computations")

if( correlation == 1):
    now = datetime.datetime.now()
    print ("   Seasonal  SST  correlations started  " + now.strftime("%Y-%m-%d %H:%M") )
##      correlations with selected variables  El Nino case 
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "pr", "ts", correl, prefix1, prefix2, undef)
## output as data : 
    write_out(  "CORR_PR",  correl,   prefixout)
### 
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "hfss", "ts", correl, prefix1, prefix2, undef)
## output as data :
    write_out( "CORR_SHF",  correl,   prefixout)
#####    
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "hfls", "ts", correl, prefix1, prefix2, undef)
## output as data : 
    write_out(  "CORR_LHF",  correl,   prefixout)
####    
    correl =  get_correlation(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "lw", "ts", correl, prefix1, prefix2, undef)
## output as data :
    write_out(  "CORR_LW",  correl,   prefixout)
####   
    correl =  get_correlation(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "sw", "ts", correl, prefix1, prefix2, undef)
## output   correlation data 
    write_out( "CORR_SW",  correl,   prefixout)
###   plot correlations 
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_correlation_all.ncl")

    print ("   Seasonal  SST  correlations completed  " + now.strftime("%Y-%m-%d %H:%M") )
    print ("   plots of  seasonal correlations  finished  " )
    print ("   resulting plots are located in : " + wkdir_model )
    print ("     with prefix correlation + variable name " )

print (" ")     
###  plotting routine  below:
###  call NCL plotting script    plot_composite_SST.ncl

##     regression calculation, if selected in parameters.txt  
##      regression of NINO3.4 SST anomaly on selected variables

print("DRBDBG COMPOSITE.py regression ",regression)
if( regression == 1):
    now = datetime.datetime.now()
    print ("   Seasonal  SST  regression calculations started  " + now.strftime("%Y-%m-%d %H:%M") )
###  
    aregress = get_regression(imax, jmax, zmax, iy1, iy2,  im1, im2, ii1, ii2, jj1, jj2, "pr", "ts", aregress, prefix1, prefix2, undef)
##  output in composite directory 
    write_out(  "REGRESS_PR",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "hfss", "ts", aregress, prefix1, prefix2, undef)
##  output in composite directory
    write_out( "REGRESS_SHF",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "hfls", "ts", aregress, prefix1, prefix2,  undef)
##  output in composite directory
    write_out( "REGRESS_LHF",  aregress,   prefixout)
###
    aregress = get_regression(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "lw", "ts", aregress, prefix1, prefix2,  undef)
##  output in composite directory
    write_out( "REGRESS_LW",  aregress,   prefixout)
##
    aregress = get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, "sw", "ts", aregress, prefix1, prefix2,  undef)
##  output 
    write_out( "REGRESS_SW",  aregress,   prefixout)

##     plotting the regressions 
##     print("DRBDBG calling ",os.environ["POD_HOME"],"/COMPOSITE/NCL/plot_regression_all.ncl")
    generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_regression_all.ncl")

    print ("   Seasonal SST  regressions completed  " + now.strftime("%Y-%m-%d %H:%M") )
    print ("   plots of seasonal regressions  finished  ")
    print ("   resulting plots are located in : " + wkdir_model)
    print ("     with prefix  regression  +  variable name " )

    print(os.system("ls "+wkdir_model))

file_src  = os.environ["POD_HOME"]+"/COMPOSITE/COMPOSITE.html"
file_dest = os.environ["ENSO_MSE_WKDIR"]+"/COMPOSITE.html" 
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)

#============================================================
#
now = datetime.datetime.now()
print ("   ") 
print (" ===================================================================")
print ("         Composite Module Finished  " +  now.strftime("%Y-%m-%d %H:%M") )
print (" ===================================================================")
### 
