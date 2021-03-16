import numpy as np
import os.path
import sys

import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from read_netcdf_2D import read_netcdf_2D

from numpy import dtype

def get_data_in_OBS(imax, jmax, mse, omse, madv, tadv, prefix, undef):

##  read in all data  pre-digested OBS data from netCDF files 
 
    filename = prefix+"/MSE_mse.nc"
    mse = read_netcdf_2D(imax, jmax, 1,  "mse",  filename, mse, undef)

    filename = prefix+"/MSE_omse.nc"
    omse = read_netcdf_2D(imax, jmax, 1,  "omse",  filename, omse, undef)
    
    filename = prefix+"/MSE_madv.nc"
    madv = read_netcdf_2D(imax, jmax, 1,  "madv",  filename, madv, undef)

    filename = prefix+"/MSE_tadv.nc"
    tadv = read_netcdf_2D(imax, jmax, 1,  "tadv",  filename, tadv, undef)
    
    return mse, omse, madv, tadv
 
