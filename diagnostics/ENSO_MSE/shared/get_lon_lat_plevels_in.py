import numpy as np
import os.path
import sys

def get_lon_lat_plevels_in( imax, jmax, zmax, lon, lat, plevs, prefix):
##  read in  all the domain dimensions and the actual values lon/lat/plevs

###  read in the lon/lat/plevs from binary
    lon_path = os.path.join(prefix,"longitude.out")
    if( os.path.exists( lon_path)):
        os.path.isfile( lon_path)
    else:
        print (" missing file ", lon_path)
        print (" exiting get_lon_lat_plevels_in.py ")
        sys.exit()

    f = open(lon_path, "rb")
    lon = np.fromfile(f, dtype='float32')
    f.close()

###    latitude
    lat_path = os.path.join(prefix,"latitude.out")
    if( os.path.exists( lat_path)):
        os.path.isfile(lat_path) 
    else:
        print (" missing file ", lat_path)
        print (" exiting get_lon_lat_plevels_in.py ")
        sys.exit()
    f = open(lat_path, "rb")
    lat = np.fromfile(f, dtype='float32')
    f.close()

###   plevs
    plevs_path = os.path.join(prefix, "plevels.out")
    if( os.path.exists(plevs_path)):
        os.path.isfile(plevs_path)
    else:
        print (" missing file ", plevs_path)
        print (" exiting get_lon_lat_plevels_in.py ")
        sys.exit()

    f = open(plevs_path, "rb")
    plevs = np.fromfile(f, dtype='float32')
    f.close()

    return lon, lat, plevs

