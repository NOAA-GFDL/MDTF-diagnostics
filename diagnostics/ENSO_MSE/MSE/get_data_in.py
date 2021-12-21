import numpy as np
import os.path
import sys

def get_data_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
    varlist = ["U", "V", "T", "Q", "Z", "OMG"]
    for v in varlist:
        filein = os.path.join(prefix, v + ".grd")
        try:
            os.path.exists(filein)
        except FileExistsError:
            print(" Missing file ", filein)
            print(" exiting MSE/get_data_in.py")
            sys.exit(1)
        f = open(filein, 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        aa1_reshape = np.reshape(aa1, (imax, jmax, zmax), order='F')
        if v == 'U':
            uu = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        elif v == 'V':
            vv = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        elif v == 'T':
            temp = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        elif v == 'Q':
            shum = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        elif v == 'Z':
            hgt = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        elif v == 'OMG':
            vvel = np.ma.masked_greater_equal(aa1_reshape, undef, copy=False)
        f.close() 

    return hgt, uu, vv, temp, shum, vvel
 
