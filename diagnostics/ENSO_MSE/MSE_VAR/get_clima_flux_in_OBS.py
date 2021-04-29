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

def get_clima_flux_in_OBS(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    filename = prefix+"/pr_clim.nc"
    pr = read_netcdf_2D(imax, jmax, 1,  "pr",  filename, pr, undef)
    pr =  pr * 24.*60.*60.
##   convert to mm/day   from kg/m2/sec

    filename = prefix+"/ts_clim.nc"
    ts = read_netcdf_2D(imax, jmax, 1,  "ts",  filename, ts, undef)

    filename = prefix+"/hfss_clim.nc"
    shf =  read_netcdf_2D(imax, jmax, 1,  "hfss",  filename, shf, undef)

    filename = prefix+"/hfls_clim.nc"
    lhf =  read_netcdf_2D(imax, jmax, 1,  "hfls",  filename, lhf, undef)

    filename = prefix+"/sw_clim.nc"
    sw =  read_netcdf_2D(imax, jmax, 1,  "sw",  filename, sw, undef)
 
    filename = prefix+"/lw_clim.nc"
    lw =  read_netcdf_2D(imax, jmax, 1,  "lw",  filename, lw, undef)

##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
