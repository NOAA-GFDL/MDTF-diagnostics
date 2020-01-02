import numpy as np
import os.path
import math
import sys

from fit_line import fit, gammln, gammq, gcf, gser


###   read in data and make composite  regression to variable2 = SST = x, variable1 = y 
##      output is the coefficient A in  y = a*x * + b
####

def get_regression(imax, jmax, zmax, iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, variable1, variable2, aregress, prefix, prefixclim, undef, undef2):

    ff = 1.
    if( variable1 ==  "PR"):    
        ff = 24.*60.*60.

    vvar1  = np.zeros( (imax,jmax),dtype='float32')
    vvar2  = np.zeros( (imax,jmax),dtype='float32')
###  time series for the linear fit   need only the first variable
##       the second is set as one time series of SST anomaly averages over ii1, ii2, jj1, jj2
    tmax = 12 * (iy2 - iy1 + 1)
    tvar1 = np.zeros( (imax,jmax, tmax),dtype='float32') 
    tvar2 = np.zeros( (tmax),dtype='float32')
    xx2 = np.zeros( (tmax),dtype='float32')
    yy2 = np.zeros( (tmax),dtype='float32')
    aregress = np.zeros((imax,jmax),dtype='float32')

#    
#     get in the climatology first :
    tmax12 = 12
    namein1 = prefixclim + variable1 + "_clim.grd"
    namein2 = prefixclim + variable2 + "_clim.grd"    
    clima1 = np.zeros( (imax,jmax, tmax12),dtype='float32')
    clima2 = np.zeros( (imax,jmax, tmax12),dtype='float32')    
    
    if (os.path.exists( namein1) and  os.path.exists( namein2)):
        f1 = open( namein1)
        clima1 = np.fromfile(f1, dtype='float32')    
        clima1 = clima1.reshape(tmax12,jmax,imax)
        clima1 = np.swapaxes(clima1, 0, 2)
        f1.close()    
        f2 = open( namein2)
        clima2 = np.fromfile(f2, dtype='float32')
        clima2 = clima2.reshape(tmax12,jmax,imax)
        clima2 = np.swapaxes(clima2, 0, 2)
        f2.close() 

    else:
        print " missing file 1 " + namein1
        print " or missing file 2 " + namein2
        print " exiting get_regression.py "
        sys.exit()

    it2 = 0
    for iy in range(iy1, iy2+1):
        for im in range (im1, im2+1):
            iyy = iy
            imm = im
            if( im > 12 ):
                iyy = iy + 1
                imm = im - 12
            if( iyy <= iy2 ):
                mm = "%02d" % imm
                month = str(mm)
                yy = "%04d" % iyy
                year = str(yy)
                namein1 = prefix + year+"/"+variable1+"_"+year+"-"+month+".grd"
                namein2 = prefix + year+"/"+variable2+"_"+year+"-"+month+".grd"
                if (os.path.exists( namein1) and os.path.exists( namein1)):
                    f1 = open( namein1)
                    f2 = open( namein2)
                    vvar1 = np.fromfile(f1, dtype='float32')
                    vvar1 = vvar1.reshape(jmax,imax)
                    vvar1 = np.swapaxes(vvar1, 0, 1)
                    vvar2 = np.fromfile(f2, dtype='float32')
                    vvar2 = vvar2.reshape(jmax,imax)
                    vvar2 = np.swapaxes(vvar2, 0, 1)
                ###  collect the global time series of anomalies
                ##  get the SST anomaly  based on ii, jj 
                    sst_anom = 0.
                    ss_anom = 0.
                    for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                            if( (vvar2[i,j] < undef) and (clima2[i, j, imm-1] < undef) ):
                                sst_anom = sst_anom + vvar2[i,j]  - clima2[i, j, imm-1]
                                ss_anom = ss_anom + 1.

                    if( ss_anom > 0.):
                        sst_anom = sst_anom/ss_anom
                    else:
                        sst_anom = undef2
                    tvar2[it2] = sst_anom
                ###    collect  global anomaly variable1 
                    for j in range(0, jmax):
                        for i in range(0, imax): 
                            if( vvar1[i,j] < undef and clima1[i,j, imm-1] < undef ):
                                tvar1[i,j, it2] = ff * (vvar1[i,j] -  clima1[i,j,imm-1])
                            else:
                                tvar1[i,j, it2] = undef2
                    f1.close()
                    f2.close()
                else:
                    print " missing file 1 " + namein1
                    print " of missing file 2 " + namein2
                    print " exiting get_regression.py"
                    sys.exit()
                        
            it2 = it2 + 1

#####
    tmax2 = it2
#############  make global regression output coeff A.
    a = 0.
    b = 0.
    for j in range(0, jmax):
        for i in range(0, imax):
            itt = 0
            for it in range( 0, tmax2):
                if( (tvar1[i, j, it] < undef) and (tvar2[it] < undef)):
                    yy2[itt] = tvar1[i, j, it]
                    xx2[itt] = tvar2[it]
                    itt = itt + 1
            ndata = itt
            if( ndata > 3 ):
                a, b =  fit( xx2, yy2, ndata, a, b)
                aregress[i,j] = b
            else:
                aregress[i,j] = undef2
    
    return aregress

