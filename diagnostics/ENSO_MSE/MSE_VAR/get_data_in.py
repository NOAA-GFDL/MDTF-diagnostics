import numpy as np
import os.path
import sys

def get_data_in(imax, jmax, mse, omse, madv, mdiv, tadv, prefix, undef):

##  read in all data 
 
    if (os.path.exists(prefix+"/MSE_mse.out")):
        f = open(prefix+'/MSE_mse.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mse = data[:, :]
        f.close() 
    else:
        print "missing file " + prefix+"/MSE_mse.out"
        print " exiting get_data_in.py "
        sys.exit()
    
    if (os.path.exists(prefix+"/MSE_omse.out")):
        f = open(prefix+'/MSE_omse.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        omse = data[:, :]
        f.close()
    else:
        print "missing file " + prefix+"/MSE_omse.out"
        print " exiting get_data_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_madv.out")):
        f = open(prefix+'/MSE_madv.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        madv = data[:, :]
        f.close()
    else:
        print  "missing file " + prefix+"/MSE_madv.out"
        print " exiting get_data_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_mdiv.out")):
        f = open(prefix+'/MSE_mdiv.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        mdiv = data[:, :]
        f.close()
    else:
        print "missing file " + prefix+"/MSE_mdiv.out"
        print " exiting get_data_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/MSE_tadv.out")):
        f = open(prefix+'/MSE_tadv.out', 'rb')
        data = np.fromfile(f, dtype='float32')
        tadv = data[:, :]
        f.close()
    else:
        print "missing file " + prefix+"/MSE_tadv.out"
        print " exiting get_data_in.py "
        sys.exit() 
    return mse, omse, madv, mdiv, tadv
 
