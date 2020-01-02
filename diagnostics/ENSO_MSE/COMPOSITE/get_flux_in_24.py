import numpy as np
import os.path
import math
import sys

###   read in data and make composite average - full  values (not anomaly !!) 
def get_flux_in_24(imax, jmax,  ttmax, years,  iy2,  variable,  tmax24, datout, prefix, prefix2,  undef, undef2):

    im1 = 1
    im2 = 24
    tmax12 = 12 
    ss    = np.zeros((imax,jmax, tmax24),dtype='float32')      
    vvar  = np.zeros((imax,jmax),dtype='float32')
    dataout = np.zeros((imax,jmax, tmax24),dtype='float32')
    clima  = np.zeros((imax,jmax, tmax12),dtype='float32')

    nameclima = prefix2 +  variable + "_clim.grd"

    if (os.path.exists( nameclima)):
        f = open( nameclima)
        clima = np.fromfile(f, dtype='float32')
        clima = clima.reshape( tmax12, jmax, imax)
        clima = np.swapaxes(clima, 0, 2)
        f.close()
    else:
        print " missing file " + nameclima
        print " exiting get_flux_in_24.py "
        sys.exit()

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
                    for j in range(0, jmax):
                        for i in range (0, imax):
                            if( vvar[i,j] < undef):
                                dataout[i,j,im-1] = dataout[i,j,im-1] + vvar[i,j]
                                ss[i,j,im-1] = ss[i,j,im-1] + 1.

                    f.close()
                else:
                    print " missing file " + namein
                    print " exiting get_flux_in_24.py "
                    sys.exit()
#### 
    for im in range( im1-1, im2):
        imm = im 
        if( imm > 11 ):
            imm = im - 12
        for j in range(0, jmax):
            for i in range (0, imax):
                if( ss[i,j,im]  > 0. and clima[i, j, imm] < undef):
                    dataout[i,j,im] = dataout[i,j,im]/ss[i,j,im]
                    dataout[i,j,im] = dataout[i,j,im] - clima[i, j, imm]
                else:
                    dataout[i,j,im] = undef2

    return dataout

