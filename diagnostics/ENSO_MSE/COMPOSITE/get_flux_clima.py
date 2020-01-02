import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!) 
def get_flux_clima(imax, jmax, im1, im2, variable,  dataout, prefixclim, undef, undef2):

    itmax = 12
    ss    = np.zeros((imax,jmax),dtype='float32')      
    vvar  = np.zeros((imax,jmax, itmax),dtype='float32')
    dataout = np.zeros((imax,jmax),dtype='float32')
##  read x, y, t dimensioned data 
    namein = prefixclim + variable + ".grd"

    if (os.path.exists( namein)):
        f = open( namein)
        vvar1 = np.fromfile(f, dtype='float32')
        vvar1 = vvar1.reshape( itmax, jmax, imax)
        vvar = np.swapaxes(vvar1, 0, 2)
        f.close()
        for im in range (im1, im2+1):
            imm = im
            if( im > 12 ):
                imm = im - 12
            for j in range(0, jmax):
                for i in range(0, imax):
                    if( vvar[i,j,imm-1] < undef) :
                        dataout[i,j] =  dataout[i,j]  + vvar[i,j, imm-1]
                        ss[i,j] = ss[i,j] + 1.

    else:
        print " missing file " +  namein
        print " exiting get_flux_clima.py "
        sys.exit()

###  
    for j in range(0, jmax):
        for i in range(0, imax):
            if( ss[i,j] > 0.) :
                dataout[i,j] = dataout[i,j]/ss[i,j]
            else:
                dataout[i,j] = undef2
    return dataout

