import numpy as np
import os.path
import math
import sys

from read_netcdf_2D import read_netcdf_2D

###   read in data and make composite average - full  values (not anomaly !!) 
def get_flux_in_24(imax, jmax,  ttmax, years,  iy2,  variable,  tmax24, datout, prefix, prefix2,  undef):

    im1 = 1
    im2 = 24
    tmax12 = 12 
    ss    = np.ma.zeros((imax,jmax,zmax,tmax24), dtype='float32', order='F')
    clima   = np.ma.zeros((imax,jmax,tmax12),dtype='float32',  order='F')
    vvar    = np.ma.zeros((imax,jmax,tmax12),dtype='float32',  order='F')
    dataout = np.ma.zeros((imax,jmax,zmax,tmax24), dtype='float32', order='F')

    nameclima = prefix2 +  variable + "_clim.nc"

    if (os.path.exists( nameclima)):
        clima = read_netcdf_2D(imax, jmax, tmax12,  variable,  nameclima, clima, undef)
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

                namein = prefix+"/"+year+"/"+variable+"_"+year+".nc"
                if (os.path.exists( namein)):
                    vvar = read_netcdf_2D(imax, jmax,  tmax12,  variable,  namein, vvar, undef)
                    vvar_invalid = (vvar >= undef)
                    dataout[:,:,:, im-1] += vvar[:,:,:, im-1]
                    ss[~vvar_invalid, im-1] += 1.
                    
                else:
                    print " missing file " + namein
                    print " exiting get_flux_in_24.py "
                    sys.exit()
#### 
    dataout = dataout/ss

    return dataout.filled(fill_value = undef)

