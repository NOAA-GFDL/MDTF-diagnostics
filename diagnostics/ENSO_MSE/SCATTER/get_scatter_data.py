import os
import sys
import subprocess
import numpy as np
import math

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from get_dimensions import get_dimensions
from get_lon_lat_plevels_in import  get_lon_lat_plevels_in
from get_data_in import get_data_in

def get_scatter_data( clon1, clon2, clat1, clat2, elon1, elon2, elat1, elat2, undef):

#============================================================
# get_ncl_data  - call to get the input data  full and climatology to make anomaly 
#============================================================
#   read and average Central and Eastern Pacific MSE variables for SCATTER plots 
    composite_dir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"] + "/model/"
    mse_dir       = os.environ["ENSO_MSE_WKDIR_MSE"] + "/model"
#######   output directory 
    scatter_dir   = os.environ["ENSO_MSE_WKDIR_SCATTER"] +  "/netCDF/"
##   conversion from kg/m2/s  to W/m2
    prfactor = 2.5E+06   

###  readin lon/lat data :
    prefix0 =  composite_dir + "/netCDF/DATA/"
    imax = -1
    jmax = -1
    zmax = -1
    imax, jmax, zmax = get_dimensions( imax,jmax, zmax, prefix0)
    lon    = np.zeros(imax,dtype='float32')
    lat    = np.zeros(jmax,dtype='float32')
    plevs   = np.zeros(zmax,dtype='float32')
    lon, lat, plevs = get_lon_lat_plevels_in( imax, jmax, zmax, lon, lat, plevs, prefix0)

    dataout = np.zeros( (imax,jmax),dtype='float32',  order='F')

    prefix1  = composite_dir + "/netCDF/"
    variable= 'PR'
    suffix = 'grd'
    dataout =  get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef)
    pr = dataout * prfactor

    variable= 'FRAD'
    suffix = 'grd'
    dataout =  get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef)
    frad = dataout
    
    variable= 'LHF'
    suffix = 'grd'
    dataout =  get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef)
    lhf = dataout

    variable= 'SHF'
    suffix = 'grd'
    dataout =  get_data_in(imax, jmax,  variable, dataout, prefix1, suffix,  undef)
    shf = dataout
################ 
##  MSE component
    prefix1  = mse_dir + "/netCDF/"

    variable= 'MSE_madv'
    suffix = 'out'
    dataout =  get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef)
    madv = dataout 

    variable= 'MSE_omse'
    suffix = 'out'
    dataout =  get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef)
    omse = dataout

######### 
##################################### 
###  select area boxes and write out 
###   extract the two  domain as area averages : Central and Eastern Pacific 
#     select the averaging indexes  over the respective boxes Central or Eastern Pacific 
#   Central first:
    for i in range(0, imax):
              if( lon[i] <= clon1 and lon[i+1] >= clon1):
                     ii1 = i+1
                     break
    for i in range(0, imax):
              if( lon[i] <= clon2 and lon[i+1] >= clon2):
                     ii2 = i
                     break
    for j in range(0, jmax):
              if( lat[j] <= clat1 and lat[j+1] >= clat1):
                     jj1 = j+1
                     break
    for j in range(0, jmax):
              if( lat[j] <= clat2 and lat[j+1] >= clat2):
                     jj2 = j
                     break
##  PR:
    yy = (pr[ii1:ii2, jj1:jj2]) 
    yy = yy.flatten('F')
    pr1 =  np.mean(yy)
#   moist advection 
    yy = madv[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    madv1 =  np.mean(yy)
##    Frad
    yy = frad[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    frad1 =  np.mean(yy)
##   omse vertical advection of MSE
    yy = omse[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    omse1 =  np.mean(yy)
##    LHF
    yy = lhf[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    lhf1 =  np.mean(yy)
##   SHF 
    yy = shf[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    shf1 =  np.mean(yy)
################  
#    Eastern Pacific 
    for i in range(0, imax):
              if( lon[i] <= elon1 and lon[i+1] >= elon1):
                     ii1 = i+1
                     break
    for i in range(0, imax):
              if( lon[i] <= elon2 and lon[i+1] >= elon2):
                     ii2 = i
                     break
    for j in range(0, jmax):
              if( lat[j] <= elat1 and lat[j+1] >= elat1):
                     jj1 = j+1
                     break
    for j in range(0, jmax):
              if( lat[j] <= elat2 and lat[j+1] >= elat2):
                     jj2 = j
                     break
##  PR:
    yy = (pr[ii1:ii2, jj1:jj2])
    yy = yy.flatten('F')
    pr2 =  np.mean(yy)
#   moist advection
    yy = madv[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    madv2 =  np.mean(yy)
##    Frad
    yy = frad[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    frad2 =  np.mean(yy)
##   omse vertical advection of MSE
    yy = omse[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    omse2 =  np.mean(yy)
##    LHF
    yy = lhf[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    lhf2 =  np.mean(yy)
##   SHF
    yy = shf[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    shf2 =  np.mean(yy)

##############  output to NEW MODEL  file ..  Central Pacific   with format
    nameout = scatter_dir + "central_pacific_MSE_terms_NEW_MODEL.txt"
    string_value = str(pr1) + " " + str(madv1) + " " + str(frad1) + " " + str(omse1) + " " + str(lhf1) + " " +  str(shf1) 
    f = open( nameout, 'w')
    f.write(  string_value )
    f.close()

    nameout = scatter_dir + "eastern_pacific_MSE_terms_NEW_MODEL.txt"
    string_value = str(pr2) + " " + str(madv2) + " " + str(frad2) + " " + str(omse2) + " " + str(lhf2) + " " +  str(shf2) 
    f = open( nameout, 'wt')
    f.write(  string_value )
    f.close()

    return 0

###########################
