import numpy as np
import os.path
import sys

def get_clima_in(imax, jmax,  mse, omse, madv, tadv, prefix, undef):

##  read in all data 
 
    if (os.path.exists(prefix+"/MSE_mse_clim.out")):
        f = open(prefix+'/MSE_mse_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mse = np.reshape( data, (imax, jmax), order='F')
        mse = np.ma.masked_greater_equal( mse,  undef, copy=False)
        f.close() 
    else:
        print (" missing file " + prefix+"/MSE_mse_clim.out")
        print (" exiting get_clima_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/MSE_omse_clim.out")):
        f = open(prefix+'/MSE_omse_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        omse = np.reshape( data, (imax, jmax), order='F')
        omse = np.ma.masked_greater_equal( omse,  undef, copy=False)
        f.close()
    else:    
        print (" missing file " + prefix+"/MSE_omse_clim.out")
        print ("exiting get_clima_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/MSE_madv_clim.out")):
        f = open(prefix+'/MSE_madv_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        madv = np.reshape( data, (imax, jmax), order='F')
        madv = np.ma.masked_greater_equal( madv,  undef, copy=False)
        f.close()
    else:
        print (" missing file " + prefix+"/MSE_madv_clim.out")
        print ("exiting get_clima_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/MSE_tadv_clim.out")):
        f = open(prefix+'/MSE_tadv_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        tadv = np.reshape( data, (imax, jmax), order='F')
        tadv = np.ma.masked_greater_equal( tadv,  undef, copy=False)
        f.close()
    else:
        print (" missing file " + prefix+"/MSE_tadv_clim.out")
        print ( "exiting get_clima_in.py ")
        sys.exit()

    return mse, omse, madv, tadv
 
