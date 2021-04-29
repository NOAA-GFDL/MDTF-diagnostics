import numpy as np
import os.path
import math
import sys

from read_netcdf_3D import read_netcdf_3D

###   read in data and make composite average - full  values (not anomaly !!)
def get_data_in(imax, jmax, zmax,  ttmax, years, iy2, im1, im2,  variable, datout, prefix, undef):

    im12 = 12
    ss      = np.ma.zeros( (imax,jmax,zmax), dtype='float32',  order='F')
    vvar    = np.ma.zeros( (imax,jmax,zmax, im12), dtype='float32',  order='F')
    dataout = np.ma.zeros( (imax,jmax,zmax), dtype='float32',  order='F')

    for it in range(0, ttmax):
        for im in range (im1, im2+1):
            iyy = years[it]
            imm = im
            if( im > 12 ):
                iyy =  years[it] + 1
                imm = im - 12
            if( iyy <= iy2 ):
                yy = "%04d" % iyy
                year = str(yy)

                # data files now per-year, not per-month, so only load when year changes
                #if (file_count == 0) or (im > 12  and file_count == 1):
                namein = os.path.join(prefix,year,variable + "_" + year + ".nc")
                if (os.path.exists( namein)):
                    vvar = read_netcdf_3D(imax, jmax, zmax, im12, variable, namein, vvar, undef)
                    vvar_valid = (vvar < undef)
                    vvar_invalid = (vvar >= undef)
                    vvar[vvar_invalid] = 0.

                    # set invalid entries of vvar to zero so they don't contribute
                    # to the running sum in dataout (modifies in-place)
                    dataout[:,:,:] += vvar[:,:,:, imm-1]
                    ss[:,:,:] += vvar_valid[:,:,:, imm-1]
                    #file_count += 1
                else:
                    print (" missing file " + namein )
                    print (" exiting get_data_in.py ")
                    sys.exit()

#                dataout[:,:,:] += vvar[:,:,:, imm-1]
#                ss[:,:,:] += vvar_valid[:,:,:, imm-1]

########### average
    dataout = dataout/ss

    return dataout.filled(fill_value = undef)

