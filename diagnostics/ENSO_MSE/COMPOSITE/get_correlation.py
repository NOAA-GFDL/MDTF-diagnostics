import numpy as np
import os.path
import math
import sys

from read_netcdf_2D import read_netcdf_2D
from read_netcdf_3D import read_netcdf_3D


###   read in data and make composite  correlations need anomalies to calculate

def get_correlation(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, variable1, variable2, correl, prefix, prefixclim, undef):

    ss     = np.zeros( (imax,jmax),dtype='float32', order='F')      
    vvar1  = np.zeros( (imax,jmax),dtype='float32', order='F')
    vvar2  = np.zeros( (imax,jmax),dtype='float32', order='F')
    correl = np.zeros( (imax,jmax),dtype='float32', order='F')
    variance1 = np.zeros((imax,jmax),dtype='float32')
##    variance2 = np.zeros((imax,jmax),dtype='float32')
    ss2 = np.zeros( (imax,jmax),dtype='float32', order='F')
    variance2 = 0.
    ss22 = 0.

#    
#     get in the climatology first :
    tmax = 12
    namein1 = prefixclim + variable1 + "_clim.nc"
    namein2 = prefixclim + variable2 + "_clim.nc"    
    clima1 = np.zeros( (imax,jmax, tmax),dtype='float32', order='F')
    clima2 = np.zeros( (imax,jmax, tmax),dtype='float32', order='F')    
    
    if (os.path.exists( namein1) and  os.path.exists( namein2)):
        clima1 = read_netcdf_3D(imax, jmax,  zmax, tmax,  variable1,  namein1, clima1, undef)       
        clima2 = read_netcdf_3D(imax, jmax,  zmax, tmax,  variable2,  namein1, clima2, undef)
    else:
        print "    missing file 1 " + namein1 
        print " or missing file 2 " + namein2
        print "exiting get_correlation.py "
        sys.exit()

    for iy in range(iy1, iy2):
        for im in range (im1, im2+1):
            iyy =  iy
            imm = im
            if( im > 12 ):
                iyy =  iy + 1
                imm = im - 12
            if( iyy <= iy2 ):
                mm = "%02d" % imm
                month = str(mm)
                yy = "%04d" % iyy
                year = str(yy)
                namein1 = prefix + year + "/"+variable1+"_"+year+".nc"
                namein2 = prefix + year + "/"+variable2+"_"+year+".nc"
                if (os.path.exists( namein1) and os.path.exists( namein1)):
                    vvar1 = read_netcdf_2D(imax, jmax, tmax,  variable1,  namein1, vvar1, undef)
                    vvar2 = read_netcdf_2D(imax, jmax, tmax,  variable2,  namein2, vvar2, undef)
##               get the index SST based on ii, jj 
##                     average SST anomaly 
                    sst_anom = np.mean( vvar2[ii1:ii2,jj1:jj2, imm-1] - clima2[ii1:ii2, jj1:jj2, imm-1] )
                    variance2 = variance2 + sst_anom*sst_anom    
                    ss22 = ss22 + 1.

####################################
###                       collect summations for the variances and covariances
                    variance1 = variance1 + np.mean( (vvar1[:,:, imm-1]   - clima1[:,:, imm-1])* (vvar1[:,:, imm-1] - clima1[:,:, imm-1]) ) 
                    correl = correl + np.mean( (vvar1[:,:, imm-1] - clima1[:,:, imm-1]) * sst_anom )
                else:
                    print "    missing file 1 " + namein1
                    print " or missing file 2 " + namein2
                    print "exiting get_correlation.py"
                    sys.exit()

############# average and output  
        variance2 = variance2/ss22
        variance2 = math.sqrt(variance2)

    correl = correl/ss2
    variance1 = variance1/ss2
    variance1 = math.sqrt(variance1 ) 
    correl = correl/(variance1 * variance2) 

    return correl.filled(fill_value = undef)

