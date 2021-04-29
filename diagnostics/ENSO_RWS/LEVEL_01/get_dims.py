import numpy as np
import os.path
import math
import sys

import xarray as xr
##import datatime as dt

from netCDF4 import Dataset

###   read in all data  
def  get_dims( imax, jmax, zmax, lon, lat, plevs, namein):

    if (os.path.exists(namein)):
        filename = namein
        f = Dataset(filename, 'r', format="NETCDF4")
        lon = f.variables['lon'][:]
        lat = f.variables['lat'][:]
        plevs = f.variables['lev'][:]
        units = f.variables['lev'].units
        ff = 1.
        if( units == "Pa"):
            ff = 0.01
        plevs = plevs * ff
        imax = len(lon)
        jmax = len(lat)
        zmax = len(plevs)
        f.close()
    else:
        print ("missing file " + " " + namein)
        print (" exiting get_dims.py ")
        sys.exit()


    return imax, jmax, zmax, lon, lat, plevs

