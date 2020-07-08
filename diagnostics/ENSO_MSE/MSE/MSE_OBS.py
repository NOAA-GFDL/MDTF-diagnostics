#
#      The code utilizes the pre-processed data from Level 1 - COMPOSITE.
#      It calculates and plots Moist Static Energy (MSE) budget variables 
#      as seasonal ENSO composite anomalies and their vertical integrals: 
#      horizontal moisture advection, vertical MSE advection,  MSE,   
#      MSE divergence, MSE avection, temperature advection, moisture divergence 
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#      This package is distributed under the LGPLv3 license (see LICENSE.txt)

import numpy as np
import sys
import math

from get_data_in import get_data_in
from get_clima_in import get_clima_in
from write_out_mse import write_out_mse
from write_out_mse_clima import write_out_mse_clima

from moist_routine_mse import moisture_energy
from moist_routine_hadv import mse_adv
from moist_routine_hdiv import mse_div
from moist_routine_mdiv import moisture_div
from moist_routine_madv import moisture_adv
from moist_routine_tadv import temperature_adv
from moist_routine_omse import moisture_o_energy
from get_parameters_in import get_parameters_in

import datetime
 
import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from get_season import get_season
from get_dimensions import get_dimensions
from get_lon_lat_plevels_in import  get_lon_lat_plevels_in
from generate_ncl_plots import generate_ncl_plots

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)

      The top drived for the MSE budget component calculations
      input data are as follows:
      3-dimensional atmospheric variables dimensioned IMAX, JMAX, ZMAX
     HGT - geopotential height [m]
     UU  - U  wind  [m/s]
     VV  - V wind [m/s]
     TEMP  - temperature [K]
     SHUM - specific humidity [kg/kg]
     VVEL - vertical velocity [Pa/s]
 
    outputs are 3-dimensional MSE components and its 2-dimensional 
      vertical integrals

     MSE3 - Moist Static Energy   3-dimensional [J/kg]
     MSE2 - vertical integral of MSE  2-dimensional [J/m2]

     MSE3_ADV  MSE horizontal advection  3-dimensional [w/kg]
     MSE2_ADV  vertical integral of ADV_MSE3 2-dimensional [W/m2]

        MSE3_DIV  MSE horizontal divergence  3-dimensional [w/kg]
        MSE2_DIV  vertical integral of DIV_MSE3 2-dimensional [W/m2]

     MADV3 -  horizontal advection of moisture  3-dimensional [W/kg]
     MADV2 -  vertical integral of MADV3 2-dimensional [W/m2]

        MDIV3 -  horizontal  moisture  divergence  3-dimensional [W/kg]
        MDIV2 -  vertical integral of MDIV3 2-dimensional [W/m2]
 
        TADV3 -  horizontal advection of temperature  3-dimensional [W/kg]
        TADV2 -  vertical integral of TADV3 2-dimensional [W/m2]
        
        OMSE3 -  vertical advection of MSE  3-dimensional [W/kg]
        OMSE2 -  vertical integral of OMSE3 2-dimensional [W/m2]

     Additionally needed on input :
      LON - longitudes [deg.]
      LAT - latitudes [deg.]
      PLEV - pressure levels [mb]

     missing values are flagged by UNDEF which is a large number

'''
imax = 180
jmax = 90
zmax = 17

###  plev = [1000.0, 925.0, 850.0, 700.0, 600.0, 500.0, 400.0, 300.0, 250.0, 200.0, 150.0, 100.0, 70.0,  50.0,  30.0,  20.0,  10.0]

undef2 = 1.1E+20

### declaration and set up of relavant directories 
##
prefix = os.environ["POD_HOME"] + "/MSE/"

## base path of all input files (created by COMPOSITE package)
composite_dir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"] + "/obs"

prefix1 =  composite_dir + "/netCDF/DATA/"
prefix01 = composite_dir + "/netCDF/DATA/"
prefix2 =  composite_dir + "/netCDF/"

convert_file = prefix1 + "/preprocess.txt"

#   El Nino
prefix11 = composite_dir + "/netCDF/ELNINO/"
#  La Nina out
prefix22 = composite_dir + "/netCDF/LANINA/"
##  24 month evoution prefixes EL NINO
prefixin111 =  composite_dir + "/netCDF/24MONTH_ELNINO/"
#  La Nina out
prefixin222 =  composite_dir + "/netCDF/24MONTH_LANINA/"

# base path of output
outdir = os.environ["ENSO_MSE_WKDIR_MSE"] + "/obs"
prefixout = outdir + "/netCDF/"

prefixout1 = prefixout  + "/ELNINO/"
prefixout2 = prefixout  + "/LANINA/"

rearth = 6378000.0
dx = -9999.
dy = -9999.
lon1 = 0.0 + 0.5 * dx
lat1 = -90.0 + 0.5 * dy

dummy1 = undef2
dummy2 = undef2
dummy3 = undef2
dummy4 = undef2
season = "NIL"
model = "NIL"
llon1 = undef2
llon2 = undef2
llat1 = undef2
llat2 = undef2
imindx1 = undef2
imindx2 = undef2
im1 = undef2
im2 = undef2
sigma = undef2
composite = 0
composite24 = 0
regression = 0
correlation = 0

##iy1 = os.environ["FIRSTYR"]
##iy2 = os.environ["FIRSTYR"]
##model = os.environ["CASENAME"]

flag0  = 0
##############  check for preprocessed data 
if( os.path.isfile( convert_file) ):
    f = open(convert_file , 'r')
    flag0  = f.read()
    print( " MSE_OBS.py preprocessing flag =",  flag0," ",convert_file)
    f.close()
#############################################3 
if( flag0 == '1'):
### print diagnostic message
    print "  The NetCDF data have already been converted (MSE_OBS.py) "
    print "   "
    print " "
else:
### print diagnostic message
    print "  NOTE  the MSE package requires pre-processed data. " 
    print "  The pre-processed OBS input data were not preprocessed. "
    print "  Please, run the COMPOSITE element with COMPOSITE = 1 "
    print "  in mdtf.py script.                                  "  
    print "   "
    print "   "
    sys.exit()

###  checking the seasonal composites in MSE 
flag0 = -1

season = "XXX"
season = get_season( season, prefix)

season_file = outdir + "/season.txt"

if( os.path.isfile( season_file) ):
    f = open(season_file , 'r')
    line = f.readline()
    line = line.strip()
    column = line.split()
    season_obs = column[0]
    f.close()
    ##print( season_obs ,  season)
    ## print( " preprocessing flag =",  flag0)
    if( season_obs == season ):
        flag0 = 1
else:
    print("MSE_OBS.py missing season_file: "+season_file)

if( flag0 == 1):
### print diagnostic message
    print "  The Observational MSE Composites have been already completed  "
    print "  for  ", season, " season"
    print "   "
    exit()
    #### exit the routine
else:
### print diagnostic message
    print "  The Observational MSE Composites to be processed "
    print "    for  ", season, " season"
    print " "


############################################
now = datetime.datetime.now()
print("===============================================================")
print("      Start of Observational Moist Static Energy  Module calculations  " +  now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")
print "  "


## optionally read in the parameters from parameter.txt file 

llon1, llon2, llat1, llat2, sigma, imindx1, imindx2,  composite, im1, im2, season, composite24,  regression, correlation,   undef2 =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, imindx1, imindx2, composite, im1, im2, season, composite24, regression, correlation,  undef2, prefix)

imax = 0
jmax = 0
zmax = 0
imax, jmax, zmax = get_dimensions( imax,jmax, zmax, prefix01)

### print( imax,  " " , jmax , " " , zmax )

lon    = np.zeros(imax,dtype='float32')
lat    = np.zeros(jmax,dtype='float32')
plevs  = np.zeros(zmax,dtype='float32')

lon, lat, plevs = get_lon_lat_plevels_in( imax, jmax, zmax, lon, lat, plevs, prefix01)


# 3d variables
uu = np.zeros((imax,jmax,zmax),dtype='float32')
vv = np.zeros((imax,jmax,zmax),dtype='float32')
temp = np.zeros((imax,jmax,zmax),dtype='float32')
hgt = np.zeros((imax,jmax,zmax),dtype='float32')
shum = np.zeros((imax,jmax,zmax),dtype='float32')
vvel = np.zeros((imax,jmax,zmax),dtype='float32')

omse3 = np.zeros((imax,jmax,zmax),dtype='float32')
omse2 = np.zeros((imax,jmax),dtype='float32')

mse3 = np.zeros((imax,jmax,zmax),dtype='float32')
mse2 = np.zeros((imax,jmax),dtype='float32')

mse3_adv = np.zeros((imax,jmax,zmax),dtype='float32')
mse2_adv = np.zeros((imax,jmax),dtype='float32')

mse3_div = np.zeros((imax,jmax,zmax),dtype='float32')
mse2_div = np.zeros((imax,jmax),dtype='float32')

madv3 = np.zeros((imax,jmax,zmax),dtype='float32')
madv2 = np.zeros((imax,jmax),dtype='float32')

mdiv3 = np.zeros((imax,jmax,zmax),dtype='float32')
mdiv2 = np.zeros((imax,jmax),dtype='float32')

tadv3 = np.zeros((imax,jmax,zmax),dtype='float32')
tadv2 = np.zeros((imax,jmax),dtype='float32')

mse3 = np.zeros((imax,jmax,zmax),dtype='float32')
mse2 = np.zeros((imax,jmax),dtype='float32')


##  climatology  array declaration 
uu = np.zeros((imax,jmax,zmax),dtype='float32')
vv = np.zeros((imax,jmax,zmax),dtype='float32')
temp = np.zeros((imax,jmax,zmax),dtype='float32')
hgt = np.zeros((imax,jmax,zmax),dtype='float32')
shum = np.zeros((imax,jmax,zmax),dtype='float32')
vvel = np.zeros((imax,jmax,zmax),dtype='float32')

### readin in pre-calculated climatologies all basic variables  needed for MSE calculations
hgt, uu, vv, temp, shum, vvel = get_clima_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix2, undef2)

###   calculation of MSE compoments  - CLIMATOLOGY 
mse2, mse3 = moisture_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2, mse3, undef2)

mse2_adv, mse3_adv = mse_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_adv, mse3_adv,  undef2)

mse2_div, mse3_div = mse_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_div, mse3_div,  undef2)

mdiv2, mdiv3 = moisture_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mdiv2, mdiv3,  undef2)

madv2, madv3 = moisture_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, madv2, madv3,  undef2)

tadv2, tadv3 = temperature_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, tadv2, tadv3,  undef2)

omse2, omse3 = moisture_o_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, vvel, rearth, omse2, omse3,  undef2)

### output calculated climatologies
write_out_mse_clima(imax, jmax, zmax, mse2, mse2_adv, mse2_div, mdiv2, madv2, tadv2, omse2, prefixout)
    
###    the calculation of  El Nino/La Nina + 24 month evolution  composites
##     for El Nino/La Nina cases 
##     
if(  composite == 1):
    now = datetime.datetime.now()
    print "  Observational MSE composite calculation begins " + now.strftime("%Y-%m-%d %H:%M")

    uu = np.zeros((imax,jmax,zmax),dtype='float32')
    vv = np.zeros((imax,jmax,zmax),dtype='float32')
    temp = np.zeros((imax,jmax,zmax),dtype='float32')
    hgt = np.zeros((imax,jmax,zmax),dtype='float32')
    shum = np.zeros((imax,jmax,zmax),dtype='float32')
    vvel = np.zeros((imax,jmax,zmax),dtype='float32')

##   reading the data in for calculations
    hgt, uu, vv, temp, shum, vvel = get_data_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix11, undef2)
##    components of MSE composite calculated here :
    mse2, mse3 = moisture_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2, mse3,  undef2)

    mse2_adv, mse3_adv = mse_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_adv, mse3_adv,  undef2)

    mse2_div, mse3_div = mse_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_div, mse3_div,  undef2)

    mdiv2, mdiv3 = moisture_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mdiv2, mdiv3,  undef2)

    madv2, madv3 = moisture_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, madv2, madv3,  undef2)

    tadv2, tadv3 = temperature_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, tadv2, tadv3, undef2)

    omse2, omse3 = moisture_o_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, vvel, rearth, omse2, omse3,  undef2)

###  writting out the MSE El Nino composites 
    write_out_mse(imax, jmax, zmax, mse2, mse2_adv,  mse2_div, mdiv2, madv2, tadv2,  omse2, prefixout1)

##   the same calculations for La Nina case,  
    uu = np.zeros((imax,jmax,zmax),dtype='float32')
    vv = np.zeros((imax,jmax,zmax),dtype='float32')
    temp = np.zeros((imax,jmax,zmax),dtype='float32')
    hgt = np.zeros((imax,jmax,zmax),dtype='float32')
    shum = np.zeros((imax,jmax,zmax),dtype='float32')
    vvel = np.zeros((imax,jmax,zmax),dtype='float32')

##   reading in  input data - as composites
    hgt, uu, vv, temp, shum, vvel = get_data_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix22, undef2)

##    MSE components  calculated 
    mse2, mse3 = moisture_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2, mse3, undef2)

    mse2_adv, mse3_adv = mse_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_adv, mse3_adv, undef2)

    mse2_div, mse3_div = mse_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mse2_div, mse3_div, undef2)

    mdiv2, mdiv3 = moisture_div(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, mdiv2, mdiv3, undef2)

    madv2, madv3 = moisture_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, madv2, madv3, undef2)

    tadv2, tadv3 = temperature_adv(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, uu, vv, rearth, tadv2, tadv3, undef2)

    omse2, omse3 = moisture_o_energy(imax, jmax, zmax, lon, lat, plevs, hgt, temp, shum, vvel, rearth, omse2, omse3,  undef2)

###    data written out to file 
    write_out_mse(imax, jmax, zmax, mse2,  mse2_adv,  mse2_div, mdiv2, madv2, tadv2, omse2, prefixout2)

###     plotting routine for all El Nino/La Nina cases 
    generate_ncl_plots(os.environ["POD_HOME"]+ "/MSE/NCL/plot_composite_all_OBS.ncl")
    
    now = datetime.datetime.now()
    print "   Seasonal Observational ENSO MSE composites completed  " + now.strftime("%Y-%m-%d %H:%M")
    print "   plots of ENSO seasonal MSE anomalies finished  "
    print "   resulting plots are located in : " +outdir
    print "   with prefix composite  + ELNINO/LANINA +  variable name "
print "  " 
##  put the season in season.txt file 
f = open(season_file , 'w')  #already set above when it checks for it
f.write(season)
f.close()

#============================================================
############  end 
