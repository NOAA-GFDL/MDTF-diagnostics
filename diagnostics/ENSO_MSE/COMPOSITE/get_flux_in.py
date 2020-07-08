import numpy as np
import os.path
import math
import sys

from read_netcdf_2D import read_netcdf_2D

###   read in data and make composite average - full  values (not anomaly !!) 
def get_flux_in(imax, jmax,  ttmax, years, iy2, im1, im2,  variable, datout, prefix, undef):

    ss    = np.zeros((imax,jmax),dtype='float32',  order='F')      
    vvar  = np.zeros((imax,jmax),dtype='float32',  order='F')
    dataout = np.zeros((imax,jmax),dtype='float32',  order='F')
    im12 = 12 
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

                namein = prefix+"/"+year+"/"+variable+"_"+year+".nc"
                if (os.path.exists( namein)):
                    vvar = read_netcdf_2D(imax, jmax,  im12,  variable,  namein, vvar, undef)
                    vvar_invalid = (vvar >= undef)

                    dataout[:,:,:] += vvar[:,:,:, imm-1]
                    ss[~vvar_invalid, im-1] += 1.
                else:
                    print " missing file " + namein
                    print " exiting get_flux_in.py "
                    sys.exit()
    
#### 
    dataout = dataout/ss

    return dataout.filled(fill_value = undef)

