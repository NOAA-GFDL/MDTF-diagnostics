import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!) 
def get_clima_in(imax, jmax, zmax, im1, im2, variable,  dataout, prefixclim, undef, undef2):
    tmax = 12
    ss    = np.zeros((imax,jmax,zmax),dtype='float32')      
    vvar  = np.zeros((imax,jmax,zmax, tmax),dtype='float32')
    dataout = np.zeros((imax,jmax,zmax),dtype='float32')
##  read x, y, z, t dimensioned data 
    namein = prefixclim + variable + ".grd"
    if (os.path.exists( namein)):
        f = open( namein)
        vvar = np.fromfile(f, dtype='float32')
        vvar = vvar.reshape(tmax, zmax,jmax,imax)
        vvar = np.swapaxes(vvar, 0, 3)
        vvar = np.swapaxes(vvar, 1, 2)
        f.close()
    
        for im in range (im1, im2+1):
            imm = im
            if( im > 12 ):
                imm = im - 12
            for k in range(0, zmax):
                for j in range(0, jmax):
                    for i in range(0, imax):
                        if( vvar[i,j,k,imm-1] < undef) :
                            dataout[i,j,k] =  dataout[i,j,k]  + vvar[i,j,k, imm-1]    
                            ss[i,j,k] = ss[i,j,k] + 1.
    else:
        print " missing file " +  namein
        print " exiting  get_clima_in.py"
        sys.exit()


##############   now average 
    for k in range(0, zmax):
        for j in range(0, jmax):
            for i in range(0, imax):
                if( ss[i,j,k] > 0.) :
                    dataout[i,j,k] = dataout[i,j,k]/ss[i,j,k]
                else:
                    dataout[i,j,k] = undef2

###    dataout = dataout/ss
    return dataout

