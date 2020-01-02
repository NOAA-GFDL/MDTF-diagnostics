import numpy as np
import os.path
import sys

def get_lon_lat_plevels_in( imax, jmax, zmax, lon, lat, plevs, prefix):
##  read in  all the domain dimensions and the actual values lon/lat/plevs

###  read in the lon/lat/plevs from binary 
    if (os.path.exists(prefix+"longitude.out")):
        file = open(prefix+'longitude.out', "rb")
        lon = np.fromfile(file, dtype='float32')
        file.close()
    else:
        print " missing file "+  prefix+"longitude.out"
        print " exiting get_plevels_in.py "
        sys.exit()

###    latitude
    if (os.path.exists(prefix+"latitude.out")):
        file = open(prefix+'latitude.out', "r")
        lat = np.fromfile(file, dtype='float32')
        file.close()
    else:
        print " missing file "+  prefix+"latitude.out"
        print " exiting get_plevels_in.py "
        sys.exit()
###   plevs
    if (os.path.exists(prefix+"plevels.out")):
        file = open(prefix+'plevels.out', "r")
        plevs = np.fromfile(file, dtype='float32')
        file.close()
    else:
        print " missing file "+  prefix+"plevels.out"
        print " exiting get_plevels_in.py "
        sys.exit()

    return lon, lat, plevs
 
