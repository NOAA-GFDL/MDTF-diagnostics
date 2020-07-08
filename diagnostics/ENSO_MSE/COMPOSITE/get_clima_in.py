import numpy as np
import os.path
import math
import sys

from read_netcdf_3D import read_netcdf_3D

###   read in data and make composite average - full  values (not anomaly !!) 
def get_clima_in(imax, jmax, zmax, im1, im2, variable,  dataout, prefixclim,  undef):
    tmax = 12
    ss    = np.ma.zeros((imax,jmax,zmax),dtype='float32', order='F')      
    vvar  = np.ma.zeros((imax,jmax,zmax, tmax),dtype='float32', order='F')
    dataout = np.ma.zeros((imax,jmax,zmax),dtype='float32', order='F')
##  read x, y, z, t dimensioned data 
    namein = prefixclim + variable + ".nc"
    if (os.path.exists( namein)):
        vvar =  read_netcdf_3D(imax, jmax, zmax, tmax,  variable,  namein, vvar, undef) 
        vvar1_invalid = (vvar >= undef)
   
        for im in range (im1, im2+1):
            imm = im
            if( im > 12 ):
                imm = im - 12
            dataout[:,:,:] += vvar[:,:,:, imm-1]
            ss[~vvar1_invalid, im-1] += 1.
    else:
        print " missing file " +  namein
        print " exiting  get_clima_in.py"
        sys.exit()


##############   now average 
    dataout = dataout/ss
###  
    return dataout.filled(fill_value = undef)

