import numpy as np
import os.path
import sys

def get_data_in(imax, jmax, mse, omse, madv, tadv, prefix, undef):

##  read in all data 
 
    if (os.path.exists(prefix+"/MSE_mse.out")):
        f = open(prefix+'/MSE_mse.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mse =  np.reshape( data, (imax, jmax), order='F')
        mse = np.ma.masked_greater_equal( mse,  undef, copy=False)
        f.close() 
    else:
        print ("missing file " + prefix+"/MSE_mse.out")
        print (" exiting get_data_in.py ")
        sys.exit()
    
    if (os.path.exists(prefix+"/MSE_omse.out")):
        f = open(prefix+'/MSE_omse.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        omse = np.reshape( data, (imax, jmax), order='F')
        omse = np.ma.masked_greater_equal( omse,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/MSE_omse.out")
        print (" exiting get_data_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/MSE_madv.out")):
        f = open(prefix+'/MSE_madv.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        madv = np.reshape( data, (imax, jmax), order='F')
        madv = np.ma.masked_greater_equal( madv,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/MSE_madv.out")
        print (" exiting get_data_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/MSE_tadv.out")):
        f = open(prefix+'/MSE_tadv.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        tadv = np.reshape( data, (imax, jmax), order='F')
        tadv = np.ma.masked_greater_equal( tadv,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/MSE_tadv.out")
        print (" exiting get_data_in.py ")
        sys.exit() 
    return mse, omse, madv, tadv
 
