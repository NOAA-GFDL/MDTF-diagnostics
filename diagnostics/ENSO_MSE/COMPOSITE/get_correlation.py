import numpy as np
import os.path
import math
import sys

###   read in data and make composite  correlations need anomalies to calculate

def get_correlation(imax, jmax, zmax,  iy1, iy2, im1, im2, ii1, ii2, jj1, jj2, variable1, variable2, correl, prefix, prefixclim, undef, undef2):

    ss    = np.zeros( (imax,jmax),dtype='float32')      
    vvar1  = np.zeros( (imax,jmax),dtype='float32')
    vvar2  = np.zeros( (imax,jmax),dtype='float32')
    correl = np.zeros((imax,jmax),dtype='float32')
    variance1 = np.zeros((imax,jmax),dtype='float32')
##    variance2 = np.zeros((imax,jmax),dtype='float32')
    ss2 = np.zeros( (imax,jmax),dtype='float32')
    variance2 = 0.
    ss22 = 0.

#    
#     get in the climatology first :
    tmax = 12
    namein1 = prefixclim + variable1 + "_clim.grd"
    namein2 = prefixclim + variable2 + "_clim.grd"    
    clima1 = np.zeros( (imax,jmax, tmax),dtype='float32')
    clima2 = np.zeros( (imax,jmax, tmax),dtype='float32')    
    
    if (os.path.exists( namein1) and  os.path.exists( namein2)):
        f1 = open( namein1)
        clima1 = np.fromfile(f1, dtype='float32')    
        clima1 = clima1.reshape(tmax,jmax,imax)
        clima1 = np.swapaxes(clima1, 0, 2)
        f1.close()    
        f2 = open( namein2)
        clima2 = np.fromfile(f2, dtype='float32')
        clima2 = clima2.reshape(tmax,jmax,imax)
        clima2 = np.swapaxes(clima2, 0, 2)
        f2.close() 
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
                namein1 = prefix + year + "/"+variable1+"_"+year+"-"+month+".grd"
                namein2 = prefix + year + "/"+variable2+"_"+year+"-"+month+".grd"
                if (os.path.exists( namein1) and os.path.exists( namein1)):
                    f1 = open( namein1)
                    f2 = open( namein2)
                    vvar1 = np.fromfile(f1, dtype='float32')
                    vvar1 = vvar1.reshape(jmax,imax)
                    vvar1 = np.swapaxes(vvar1, 0, 1)
                    vvar2 = np.fromfile(f2, dtype='float32')
                    vvar2 = vvar2.reshape(jmax,imax)
                    vvar2 = np.swapaxes(vvar2, 0, 1)
##                            get the index SST based on ii, jj 
##                     average SST anomaly 
                    sst_anom = 0.
                    ss_anom = 0.
                    for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                            if( (vvar2[i,j] < undef) and (clima2[i, j, imm-1] < undef) ):
                                sst_anom = sst_anom + vvar2[i,j]  - clima2[i, j, imm-1]
                                ss_anom = ss_anom + 1.

                    if( ss_anom > 0.):
                        sst_anom = sst_anom/ss_anom
                        variance2 = variance2 + sst_anom*sst_anom    
                        ss22 = ss22 + 1.
                    else:
                        sst_anom = undef             
####################################
###                       collect summations for the variances and covariances
                    for j in range(0, jmax):
                        for i in range(0, imax): 
                            if( vvar1[i,j] < undef and clima1[i,j, imm-1] < undef and sst_anom < undef ):
                                variance1[i,j] =  variance1[i,j] + (vvar1[i,j] -  clima1[i,j,imm-1])*(vvar1[i,j] -  clima1[i,j, imm-1])
                                correl[i,j] =  correl[i,j] + (vvar1[i,j] -  clima1[i,j, imm-1])*sst_anom

                                ss2[i,j] = ss2[i,j] + 1.
                    f1.close()
                    f2.close()
                else:
                    print "    missing file 1 " + namein1
                    print " or missing file 2 " + namein2
                    print "exiting get_correlation.py"
                    sys.exit()

############# average and output 
    if(  ss22 > 0.):
        variance2 = variance2/ss22
        variance2 = math.sqrt(variance2)
    else:
        variance2 = undef 

    for j in range(0, jmax):
        for i in range(0, imax):
            if( ss2[i,j] > 0.  and variance2 < undef and variance2 > 0. and variance1[i,j] > 0.) :
                correl[i,j] = correl[i,j]/ss2[i,j]
                variance1[i,j] = variance1[i,j]/ss2[i,j]
                variance1[i,j] = math.sqrt(variance1[i,j])
                correl[i,j] =  correl[i,j]/( variance1[i,j]*variance2)
            else:    
                correl[i,j] = undef2

    return correl

