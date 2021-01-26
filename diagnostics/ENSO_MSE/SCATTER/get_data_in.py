import os
import sys
import subprocess
import numpy as np

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


def   get_data_in(imax, jmax, variable, dataout, prefix1, suffix,  undef):

    dataout = np.zeros( (imax,jmax),dtype='float32',  order='F')
###  readin  the data and output anomaly
    if (os.path.exists(prefix1+"/ELNINO/" + variable + "." + suffix)):
        f = open(prefix1+'/ELNINO/' + variable + '.' + suffix, 'rb')
        data1 = np.fromfile(f, dtype='float32')
        data1 =  np.reshape( data1, (imax, jmax), order='F')
        data1 = np.ma.masked_greater_equal( data1,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix1+"/ELNINO/" + variable +"." + suffix)
        print (" exiting get_data_in.py ")
        sys.exit()

    if (os.path.exists(prefix1+ "/" + variable + "_clim." + suffix)):
        f = open(prefix1 + '/' + variable + '_clim.' + suffix, 'rb')
        data = np.fromfile(f, dtype='float32')
        clim = np.reshape( data, (imax, jmax), order='F')
        clim = np.ma.masked_greater_equal( clim,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix1+"/"+ variable + "_clim." + suffix)
        print (" exiting get_data_in.py ")
        sys.exit()
##   define as anomaly 
    dataout = data1 - clim

    return  dataout.filled(fill_value = undef)
###########################
