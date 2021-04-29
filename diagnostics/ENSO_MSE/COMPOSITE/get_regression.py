import numpy as np
import os.path
import math
import sys

from scipy import stats

from read_netcdf_2D import read_netcdf_2D

###   read in data and make composite  regression to variable2 = SST = x, variable1 = y
##      output is the coefficient A in  y = a*x * + b
####

def get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, variable1, variable2, aregress, prefix, prefixclim, undef):

    ff = 1.
    if( variable1 ==  "pr"):
        ff = 24.*60.*60.

    vvar1  = np.zeros( (imax,jmax),dtype='float32', order='F')
    vvar2  = np.zeros( (imax,jmax),dtype='float32', order='F')
###  time series for the linear fit   need only the first variable
##       the second is set as one time series of SST anomaly averages over ii1, ii2, jj1, jj2
    tmax = 12 * (iy2 - iy1 + 1)
    tmax12 = 12
    tvar1 = np.ma.zeros( (imax,jmax, tmax),dtype='float32', order='F')
    tvar2 = np.ma.zeros( (tmax), dtype='float32', order='F')
    aregress = np.ma.zeros((imax,jmax),dtype='float32', order='F')

#
#     get in the climatology first :
    clima1  = np.ma.zeros( (imax,jmax,tmax12), dtype='float32', order='F')
    clima2  = np.ma.zeros( (imax,jmax,tmax12), dtype='float32', order='F')
    namein1 = os.path.join(prefixclim, variable1 + "_clim.nc")
    namein2 = os.path.join(prefixclim, variable2 + "_clim.nc")

    if (os.path.exists( namein1) and  os.path.exists( namein2)):
        clima1 = read_netcdf_2D(imax, jmax, tmax12,  variable1,  namein1, clima1, undef)
        clima2 = read_netcdf_2D(imax, jmax, tmax12,  variable2,  namein2, clima2, undef)
        clima1 = np.ma.masked_greater_equal( clima1, undef, copy=False)
        clima2 = np.ma.masked_greater_equal( clima2, undef, copy=False)
        #clima1_valid = (clima1 < undef)
        #clima1_invalid = (clima1 >= undef)
        #clima1[clima1_invalid] = 0.
        #clima2_valid = (clima2 < undef)
        #clima2_invalid = (clima2 >= undef)
        #clima2[clima2_invalid] = 0.

    else:
        print (" missing file 1 " + namein1 )
        print (" or missing file 2 " + namein2 )
        print (" exiting get_regression.py ")
        sys.exit()

###################################################
    it2 = 0
    for iy in range(iy1, iy2):
        for im in range (im1, im2+1):
            iyy = iy
            imm = im
            if( im > 12 ):
                iyy = iy + 1
                imm = im - 12
            if( iyy <= iy2 ):
                yy = "%04d" % iyy
                year = str(yy)
                namein1 = os.path.join(prefix,year,variable1+"_"+year+".nc")
                namein2 = os.path.join(prefix,year,variable2+"_"+year+".nc")

                if (os.path.exists( namein1) and os.path.exists( namein1)):
                    vvar1 = read_netcdf_2D(imax, jmax, tmax12,  variable1,  namein1, vvar1, undef)
                    vvar2 = read_netcdf_2D(imax, jmax, tmax12,  variable2,  namein2, vvar2, undef)
                    vvar1 = np.ma.masked_greater_equal( vvar1, undef, copy=False)
                    vvar2 = np.ma.masked_greater_equal( vvar2, undef, copy=False)

                ###  collect the global time series of anomalies
                ##  get the SST anomaly  based on ii, jj
                    sst_anom = np.mean( vvar2[ii1:ii2,jj1:jj2, imm-1]  - clima2[ii1:ii2, jj1:jj2, imm-1] )
                    tvar2[it2] = sst_anom
                ###    collect  global anomaly variable1
                    tvar1[:,:, it2]  = ff * (vvar1[:,:,imm-1] - clima1[:,:,imm-1])
                    it2 = it2 + 1
                else:
                    print (" missing file 1 " + namein1 )
                    print (" of missing file 2 " + namein2 )
                    print (" exiting get_regression.py" )
                    sys.exit()


#####
    tmax2 = it2 - 1
#############  make global regression output coeff A.
######         (a_s, b_s, r, tt, stderr) = stats.linregress(t, xn)

    for j in range (0, jmax):
        for i in range (0, imax):
            aregress[i,j], intercept, r_value, p_value, std_err = stats.linregress( tvar2[0:tmax2-1], tvar1[i,j,0:tmax2-1])

    return aregress.filled(fill_value = undef)


