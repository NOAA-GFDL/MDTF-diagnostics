import numpy as np
import os.path
import math
import sys

from read_netcdf_3D import read_netcdf_3D

###   read in data and make composite average -  anomaly !!! 
####               full 24 month evolution based on SST indices
def get_data_in_24(imax, jmax, zmax,  ttmax, years,  iy2, variable,  tmax24,  dataout, prefix,  prefix2, undef):
    this_func = "ENSO_MSE/COMPOSITE/get_data_in_24.py"

    im1 = 1
    im2 = 24
    tmax12 = 12
    # create masked arrays, initialized to all zeros
    # use fortran index order to match arrays read in from files
    ss      = np.ma.zeros( (imax,jmax,zmax,tmax24), dtype='float32', order='F')
    clima   = np.ma.zeros( (imax,jmax,zmax,tmax12),dtype='float32',  order='F')
    vvar    = np.ma.zeros( (imax,jmax,zmax,tmax12),dtype='float32',  order='F')
    dataout = np.ma.zeros( (imax,jmax,zmax,tmax24), dtype='float32', order='F')
    # not necessary to preallocate memory for arrays that are read in from files

##  read in the clima values
    nameclima = os.path.join(prefix2, variable + "_clim.nc")
    if (os.path.exists( nameclima)):
        # np.fromfile handles file open/close, memory allocation
        clima = read_netcdf_3D(imax, jmax,  zmax, tmax12,  variable,  nameclima, clima, undef)
    else:
        print (" missing file " + nameclima )
        print (" exiting get_data_in_24.py ")
        sys.exit()


    for it in range(0, ttmax):
        file_count = 0
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

                # data files now per-year, not per-month, so only load when year changes
                namein = os.path.join(prefix,year,variable+"_"+year+".nc")
                if (os.path.exists( namein)):
                        # np.fromfile handles file open/close, memory allocation
                        vvar = read_netcdf_3D(imax, jmax,  zmax, tmax12,  variable,  namein, vvar, undef)
                        vvar_invalid = (vvar >= undef)
                        vvar_valid = (vvar < undef)
                    # set invalid entries of vvar to zero so they don't contribute
                    # to the running sum in dataout (modifies in-place)
                        vvar[vvar_invalid] = 0.
                    # add 3D vvar to the 3D slice of 4D dataout corresponding to
                    # current month (im)
                        dataout[:,:,:, im-1] += vvar[:,:,:, imm-1] 
                    # increment entries of ss where entries of vvar were valid;
                    # note we can combine multi-dimensional masking and slicing
                        ss[:,:,:, im-1] += vvar_valid[:,:,:, imm-1]

                else:
                        print (" missing file " + namein)
                        print (" exiting  get_data_in_24.py" )
                        sys.exit()


    # element-wise division
    # all occurrences of division by zero are converted to a masked (invalid) 
    # element - no errors are raised
    dataout = dataout/ss
    # assign to 12-mo hyperslab instead of looping over month index
    # subtraction by invalid entries in clima produces invalid entries in dataout
    dataout[:,:,:, 0:tmax12] -= clima[:,:,:, 0:tmax12]
    dataout[:,:,:, tmax12:(2*tmax12)] -= clima[:,:,:, 0:tmax12]
    print(this_func+" returning ")
    # fill in masked (invalid) entries with value undef
    # convert from maskedarray to ordinary numpy array for compatibility with 
    # rest of code
    return dataout.filled(fill_value = undef)

