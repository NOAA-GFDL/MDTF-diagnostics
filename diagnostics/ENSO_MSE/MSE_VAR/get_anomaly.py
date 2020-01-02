import numpy as np
import os.path

def get_anomaly(imax, jmax, zmax,  varin, varin_clim, undef):
    
    for j in range(0, jmax):
        for i in range (0, imax):
            if( varin[i,j]  < undef):
                varin[i,j] = varin[i,j] - varin_clim[i,j]
            else:
                varin[i,j] = undef
####
    return varin
 
