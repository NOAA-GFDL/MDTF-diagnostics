
import os
import math
import sys
import os.path


import numpy as np

from numpy import dtype
from netCDF4 import Dataset

def get_lonlat_in_OBS(imax, jmax, lon, lat, prefix, undef):

##  read in all data  pre-digested OBS data from netCDF files 
 
    if (os.path.exists(prefix+"/ts.nc")):
        filename = prefix+"/ts.nc"
        f = Dataset(filename, 'r', format="NETCDF4") 
        lon = f.variables['lon'][:]
        lat = f.variables['lat'][:]
        imax = len(lon)
        jmax = len(lat)
        f.close() 
    else:
        print ("missing file " + prefix+"/ts.nc")
        print (" exiting get_lonalat_in_OBS.py ")
        sys.exit()
    
    return  imax, jmax, lon, lat
 
