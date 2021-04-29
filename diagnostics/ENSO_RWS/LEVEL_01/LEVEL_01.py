#
#      The code preprocesses the model input data to create
#      climatologies and corresponding anomalies.
#      Based on calculated anomalies, the code selects the El Nino/La Nina
#      years and construct corresponding seasonal composites.
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

import time
import datetime

import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from netCDF4 import Dataset

from get_parameters_in import get_parameters_in
from get_dims import get_dims
from get_nino_index import get_nino_index

from get_clima_in import get_clima_in
from get_flux_clima import get_flux_clima

from get_data_in import get_data_in
from get_flux_in import get_flux_in

from write_out import write_out

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
     VVEL - vertical velocity [Pa/s]

    2-dimensional variables  (fluxes)

      PRECIP precip. kg/m2/sec
      SST    Skin Surface Temperature   [K]

    all for full values.
    outputs are 3-dimensional composites and its 2-dimensional vertical integrals
'''

now = datetime.datetime.now()
print("=========== LEVEL_01.py =======================================")
print("   Start of LEVEL_01 calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

##  input data directory

datain =  os.environ["DATADIR"]

model =  os.environ["CASENAME"]
case = model

### print( " ENSO_RWS_WKDIR = " + os.environ["ENSO_RWS_WKDIR"] )

wkdir_model =  os.environ["ENSO_RWS_WKDIR"] + "/model"

##   output directories 
climadir =   wkdir_model + "/netCDF/CLIMA/"
datadir =   wkdir_model + "/netCDF/DATA/"
#   El Nino
elninodir = wkdir_model + "/netCDF/ELNINO/"
#  La Nina out
laninadir = wkdir_model + "/netCDF/LANINA/"

###  get DJF El Nino/La Nina years for composite calculations

iy1 =  os.environ["FIRSTYR"]
iy2 =  os.environ["LASTYR"]
iy1 = int(iy1)
iy2 = int(iy2)

##  read in all variables
## 3D vars
zgv  = "zg"  # os.environ["zg_var"]
uav  = "ua"  # os.environ["ua_var"]
vav  = "va"  # os.environ["va_var"]
tav  = "ta"  # os.environ["ta_var"]
wapv = "wap" # os.environ["omega_var"]
##     2D  vars
prv = "pr" #  os.environ["pr_var"]
tsv = "ts" # os.environ["ts_var"]

##  get 
undef = 1.1E+20
season = "NIL"
llon1 = undef
llon2 = undef
llat1 = undef
llat2 = undef
im1 = 0
im2 = 0
sigma = undef
prefix =  os.environ["POD_HOME"] + "/LEVEL_01/"
llon1, llon2, llat1, llat2, sigma, im1, im2, season  =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, im1, im2, season, prefix)

itmax = iy2 - iy1 + 1
ttmax1 = 0
ttmax2 = 0
years1 =  np.zeros((itmax), dtype='int32')
years2 =  np.zeros((itmax), dtype='int32')

##  first read in TS and get the elnino/lanina yearno_index
##  need to get imax, jmax, zmax, lon,lat, plevs
imax = 0
jmax = 0
zmax = 0
lon = 0
lat = 0
plevs = 0

namein = os.path.join( datain + "/mon/" + model + "." + zgv + ".mon.nc")
imax, jmax, zmax, lon, lat, plevs = get_dims( imax, jmax, zmax, lon, lat, plevs, namein) 

##  get the el nino/la nina  years  
ii1 = 0
ii2 = 0 
jj1 = 0
jj2 = 0

### print diagnostic message
print ("  The following parameters are set in the Composite Module Calculations  ")
print ("      the reference area for SST indices calculations is selected to:        ")
print ("      lon = ", llon1, " - ", llon2 , " E", "lat = ", llat1, " - ", llat2, "N" )
print ("      ENSO indices  based on SST reference anomalies +/- ", sigma, " of SST sigma")
print ("      Selected season  is : ", season   )
print ("      Selected year span for composites is : ", iy1,"/",  iy2 )
print ("      Selected model  : " , model  )
print ("   " )

ii1, ii2, jj1, jj2, ttmax1, years1, ttmax2, years2 = get_nino_index(imax, jmax, lon, lat,  itmax,  iy1, iy2, im1, im2, llon1, llon2, llat1, llat2, ii1, ii2, jj1, jj2, sigma, ttmax1, ttmax2, years1,  years2,  datadir, undef)

## added 2021-02-01  check for the selected years - the time series needs to be long enough
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

###  get the composites for all variables 3D + 2D 

now = datetime.datetime.now()
print (" Reading Climatologies  "  + now.strftime("%Y-%m-%d %H:%M"))

uuclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
tempclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
hgtclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvelclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
dtclim = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')

tsclim  = np.zeros((imax,jmax),dtype='float32',  order='F')
prclim  = np.zeros((imax,jmax),dtype='float32',  order='F')

hgtclim  = get_clima_in(imax, jmax, zmax, im1, im2, zgv,  hgtclim, climadir, undef)
uuclim   = get_clima_in(imax, jmax, zmax, im1, im2, uav,   uuclim , climadir, undef)
vvclim   = get_clima_in(imax, jmax, zmax, im1, im2, vav,   vvclim,  climadir, undef)
tempclim = get_clima_in(imax, jmax, zmax, im1, im2, tav,   tempclim, climadir, undef)
vvelclim = get_clima_in(imax, jmax, zmax, im1, im2, wapv,  vvelclim,  climadir, undef)
dtclim = get_clima_in(imax, jmax, zmax, im1, im2, "dT",  dtclim,  climadir, undef)

prclim  = get_flux_clima(imax, jmax, im1, im2, prv, prclim,  climadir,  undef)
tsclim  = get_flux_clima(imax, jmax, im1, im2, tsv, tsclim,  climadir,  undef)

## output as netCDF
prefixout =  wkdir_model + "/netCDF/"
##  p
unit = "[m]"
write_out( lon, lat, plevs, zgv, unit, hgtclim,  prefixout, undef)

unit = "[m/s]"
write_out( lon, lat, plevs, uav, unit, uuclim,  prefixout, undef)
write_out( lon, lat, plevs, vav, unit, vvclim,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tav, unit, tempclim,  prefixout, undef)

unit = "[Pa/s]"
write_out( lon, lat, plevs, wapv, unit, vvelclim,  prefixout, undef)

unit = "[K/s]"
write_out( lon, lat, plevs, "dT", unit, dtclim,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tsv, unit, tsclim,  prefixout, undef)

unit = "[kg/m2/sec]"
write_out( lon, lat, plevs, prv, unit, prclim,  prefixout, undef)

## El Nino 
now = datetime.datetime.now()
print ("  Starting Seasonal ELNINO/LANINA composites: "  + now.strftime("%Y-%m-%d %H:%M") )

####  declare the variable arrays
# 3d variables
uu   = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vv   = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
temp = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
hgt  = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
vvel = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')
dt   = np.zeros((imax,jmax,zmax),dtype='float32',  order='F')

ts  = np.zeros((imax,jmax),dtype='float32',  order='F')
pr  = np.zeros((imax,jmax),dtype='float32',  order='F')


hgt  = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, zgv,  hgt, datadir, undef)
uu   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, uav,  uu, datadir, undef)
vv   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, vav,  vv, datadir, undef)
temp = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, tav,  temp, datadir, undef)
vvel = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, wapv, vvel, datadir, undef)
dt   = get_data_in(imax, jmax, zmax, ttmax1, years1, iy2, im1, im2, "dT", dt, datadir, undef)

pr   = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, prv,  pr, datadir,  undef)
ts   = get_flux_in(imax, jmax, ttmax1, years1, iy2, im1, im2, tsv,  ts, datadir,  undef)

## output as netCDF 
prefixout = elninodir + "/" 
unit = "[m]"
write_out( lon, lat, plevs, zgv, unit, hgt,  prefixout, undef)

unit = "[m/s]"
write_out( lon, lat, plevs, uav, unit, uu,  prefixout, undef)
write_out( lon, lat, plevs, vav, unit, vv,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tav, unit, temp,  prefixout, undef)

unit = "[Pa/s]"
write_out( lon, lat, plevs, wapv, unit, vvel,  prefixout, undef)

unit = "[K/s]"
write_out( lon, lat, plevs, "dT", unit, dt,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tsv, unit, ts,  prefixout, undef)

unit = "[kg/m2/sec]"
write_out( lon, lat, plevs, prv, unit, pr,  prefixout, undef)

###  the same for La Nina 

hgt  = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, zgv,  hgt, datadir, undef)
uu   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, uav,  uu, datadir, undef)
vv   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, vav,  vv, datadir, undef)
temp = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, tav,  temp, datadir, undef)
vvel = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, wapv,  vvel, datadir, undef)
dt   = get_data_in(imax, jmax, zmax, ttmax2, years2, iy2, im1, im2, "dT",  dt, datadir, undef)

pr   = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, prv,  pr, datadir,  undef)
ts   = get_flux_in(imax, jmax, ttmax2, years2, iy2, im1, im2, tsv,  ts, datadir,  undef)

## output as netCDF
prefixout = laninadir + "/"
unit = "[m]"
write_out( lon, lat, plevs, zgv, unit, hgt,  prefixout, undef)

unit = "[m/s]"
write_out( lon, lat, plevs, uav, unit, uu,  prefixout, undef)
write_out( lon, lat, plevs, vav, unit, vv,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tav, unit, temp,  prefixout, undef)

unit = "[Pa/s]"
write_out( lon, lat, plevs, wapv, unit, vvel,  prefixout, undef)

unit = "[K/s]"
write_out( lon, lat, plevs, "dT", unit, dt,  prefixout, undef)

unit = "[K]"
write_out( lon, lat, plevs, tsv, unit, ts,  prefixout, undef)

unit = "[kg/m2/sec]"
write_out( lon, lat, plevs, prv, unit, pr,  prefixout, undef)

####   calling the plotting routine here : observations and model 

##  need to get Q1 vertically integrated 
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/Q1_routine.ncl")

now = datetime.datetime.now()
print (" Plotting routines start " + now.strftime("%Y-%m-%d %H:%M") )

generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_SST_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_HGT_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_Q1_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_stream_fnc_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_divergent_wind_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_divergence_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_adiv_aUVdiv_overlay.ncl")

generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_Hgt_Vanom_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_adiv_aUVdiv_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_aUVdiv_cvort_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_betastar_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_Uclima_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_wavenumber_overlay.ncl")

## copy the html file
file_src  = os.environ["POD_HOME"]+"/LEVEL_01/LEVEL_01.html"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/LEVEL_01.html"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)


now = datetime.datetime.now()
print (" LEVEL_01 completed " +  now.strftime("%Y-%m-%d %H:%M") )

