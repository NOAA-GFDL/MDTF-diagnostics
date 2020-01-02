import numpy as np
import os.path
import math
import sys

###   read in data and make composite average -  anomaly !!! 
####                   full 24 month evolution based on SST indices
def get_data_in_24(imax, jmax, zmax,  ttmax, years,  iy2, variable,  tmax24,  dataout, prefix,  prefix2, undef, undef2):
    this_func = "ENSO_MSE/COMPOSITE/get_data_in_24.py"

    im1 = 1
    im2 = 24
    tmax12 = 12
    ss    = np.zeros((imax,jmax,zmax,tmax24),dtype='float32')      
    vvar  = np.zeros((imax,jmax,zmax),dtype='float32')
    dataout = np.zeros((imax,jmax,zmax,tmax24),dtype='float32')
    clima = np.zeros((imax,jmax,zmax,tmax12),dtype='float32')

##  read in the clima values
    nameclima = prefix2 +  variable + "_clim.grd"
    if (os.path.exists( nameclima)):
        print(this_func," reading ",nameclima)
        f = open( nameclima)
        clima = np.fromfile(f, dtype='float32')
        clima = clima.reshape(tmax12, zmax,jmax,imax)
        clima = np.swapaxes(clima, 0, 3)
        clima = np.swapaxes(clima, 1, 2)
        f.close()
    else:
        print " missing file " + nameclima
        print " exiting get_data_in_24.py "
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
                print(this_func," reading ",namein)
                if (os.path.exists( namein)):
                    f = open( namein)
                    vvar = np.fromfile(f, dtype='float32')
                    vvar = vvar.reshape(zmax,jmax,imax)
                    vvar = np.swapaxes(vvar, 0, 2)
                    for k in range(0, zmax):
                        for j in range(0, jmax):
                            for i in range (0, imax):
                                if( vvar[i,j,k] < undef):
                                    dataout[i,j,k,im-1] = dataout[i,j,k,im-1] + vvar[i,j,k]
                                    ss[i,j,k,im-1] = ss[i,j,k,im-1] + 1.

                    f.close()
                else:
                    print " missing file " + namein
                    print " exiting  get_data_in_24.py" 
                    sys.exit()

    for im in range( im1-1, im2):
        imm = im 
        if( imm > 11 ):
            imm = imm - 12
        for k in range(0, zmax):
            for j in range(0, jmax):
                for i in range (0, imax):
                    if( ss[i,j,k, im] > 0. and clima[i,j,k,imm] < undef):
                        dataout[i,j,k,im] = dataout[i,j,k,im]/ss[i,j,k, im] 
                        dataout[i,j,k,im] = dataout[i,j,k,im] - clima[i, j, k, imm]
                    else:
                        dataout[i,j,k,im] = undef2
        print(this_func," returning ")
    return dataout

