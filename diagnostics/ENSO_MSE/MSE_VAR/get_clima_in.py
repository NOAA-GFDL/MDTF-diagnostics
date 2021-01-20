import numpy as np
import os.path
import sys

def get_clima_in(imax, jmax,  mse, omse, madv, mdiv, tadv, prefix, undef):

##  read in all data 
 
    if (os.path.exists(prefix+"/MSE_mse_clim.out")):
        f = open(prefix+'/MSE_mse_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mse = np.reshape( data, (imax, jmax), order='F')
        f.close() 
    else:
        print " missing file " + prefix+"/MSE_mse_clim.out"
        print " exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_omse_clim.out")):
        f = open(prefix+'/MSE_omse_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        omse = np.reshape( data, (imax, jmax), order='F')
        f.close()
    else:    
        print " missing file " + prefix+"/MSE_omse_clim.out"
        print "exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_madv_clim.out")):
        f = open(prefix+'/MSE_madv_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        madv = np.reshape( data, (imax, jmax), order='F')
        f.close()
    else:
        print " missing file " + prefix+"/MSE_madv_clim.out"
        print "exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_mdiv_clim.out")):
        f = open(prefix+'/MSE_mdiv_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mdiv = np.reshape( data, (imax, jmax), order='F')
        f.close()
    else:
        print " missing file " + prefix+"/MSE_mdiv_clim.out"
        print  "exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_tadv_clim.out")):
        f = open(prefix+'/MSE_tadv_clim.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        tadv = np.reshape( data, (imax, jmax), order='F')
        f.close()
    else:
        print " missing file " + prefix+"/MSE_tadv_clim.out"
        print  "exiting get_clima_in.py "
        sys.exit()

    return mse, omse, madv, mdiv, tadv
 
