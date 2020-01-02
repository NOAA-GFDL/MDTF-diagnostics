import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!) 
def get_flux_in(imax, jmax,  ttmax, years, iy2, im1, im2,  variable, datout, prefix, undef, undef2):

    ss    = np.zeros((imax,jmax),dtype='float32')      
    vvar  = np.zeros((imax,jmax),dtype='float32')
    dataout = np.zeros((imax,jmax),dtype='float32')
    for it in range(0, ttmax+1):
        for im in range (im1, im2+1):
            iyy = years[it]
            imm = im
            if( im > 12 ):
                iyy =  years[it] + 1
                imm = im - 12
            if( iyy <= iy2 ):
                mm = "%02d" % imm
                month = str(mm)
                yy = "%04d" % iyy
                year = str(yy)

                namein = prefix+"/"+year+"/"+variable+"_"+year+"-"+month+".grd"
                if (os.path.exists( namein)):
                    f = open( namein)
                    vvar = np.fromfile(f, dtype='float32')
                    vvar = vvar.reshape(jmax,imax)
                    vvar = np.swapaxes(vvar, 0, 1)
                    f.close()
                    for j in range(0, jmax):
                        for i in range(0, imax):
                            if( vvar[i,j] < undef):
                                dataout[i,j] =  dataout[i,j] + vvar[i,j]
                                ss[i,j] = ss[i,j] + 1.
                else:
                    print " missing file " + namein
                    print " exiting get_flux_in.py "
                    sys.exit()
    
#### 
    for j in range(0, jmax):
        for i in range(0, imax):
            if( ss[i,j] > 0.) :
                dataout[i,j] = dataout[i,j]/ss[i,j]
            else:
                dataout[i,j] = undef2
    return dataout

