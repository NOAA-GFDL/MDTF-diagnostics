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

def get_flux_in_OBS(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    filename = prefix+"/pr.nc"
    pr = read_netcdf_2D(imax, jmax, 1,  "pr",  filename, pr, undef)

    filename = prefix+"/ts.nc"
    ts = read_netcdf_2D(imax, jmax, 1,  "ts",  filename, ts, undef)

    filename = prefix+"/hfss.nc"
    shf =  read_netcdf_2D(imax, jmax, 1,  "hfss",  filename, shf, undef)

    filename = prefix+"/hfls.nc"
    lhf =  read_netcdf_2D(imax, jmax, 1,  "hfls",  filename, lhf, undef)

    filename = prefix+"/sw.nc"
    sw =  read_netcdf_2D(imax, jmax, 1,  "sw",  filename, sw, undef)

    filename = prefix+"/lw.nc"
    lw =  read_netcdf_2D(imax, jmax, 1,  "lw",  filename, lw, undef)


##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
