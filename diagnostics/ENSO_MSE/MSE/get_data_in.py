import numpy as np
import os.path
import sys

def get_data_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
##    print prefix
    if (os.path.exists(prefix+"/U.grd")):
        f = open(prefix+'/U.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        uu = np.reshape( aa1, (imax, jmax, zmax), order='F')
        uu = np.ma.masked_greater_equal( uu,  undef, copy=False)
        f.close() 
    else:    
        print (" missing file " + prefix + "/U.grd")
        print (" exiting get_data_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/V.grd")):
        f = open(prefix+'/V.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        vv = np.reshape( aa1, (imax, jmax, zmax), order='F')
        vv = np.ma.masked_greater_equal( vv,  undef, copy=False)
        f.close()
    else:
        print (" missing file " +  prefix + "/V.grd" )   
        print (" exiting get_data_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/T.grd")):
        f = open(prefix+'/T.grd', 'rb')
        aa1 =  np.fromfile(f, dtype='float32')
        temp = np.reshape( aa1, (imax, jmax, zmax), order='F')
        temp = np.ma.masked_greater_equal( temp, undef, copy=False)
        f.close()
    else:
        print (" missing file " + prefix + "/T.grd")
        print (" exiting get_data_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/Q.grd")):
        f = open(prefix+'/Q.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        shum = np.reshape( aa1, (imax, jmax, zmax), order='F')
        shum = np.ma.masked_greater_equal( shum, undef, copy=False)
        f.close()
    else:
        print  (" missing file " +  prefix + "/Q.grd")
        print (" exiting get_data_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/Z.grd")):
        f = open(prefix+'/Z.grd', 'rb')
        aa1  = np.fromfile(f, dtype='float32')
        hgt = np.reshape( aa1, (imax, jmax, zmax), order='F')
        hgt = np.ma.masked_greater_equal( hgt, undef, copy=False)
        f.close()        
    else:
        print (" missing file " + prefix + "/Z.grd")
        print (" exiting get_data_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/OMG.grd")):
        f = open(prefix+'/OMG.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        vvel = np.reshape( aa1, (imax, jmax, zmax), order='F')
        vvel = np.ma.masked_greater_equal( vvel,  undef, copy=False)
        f.close()        
    else:
        print (" missing file " + prefix + "/OMG.grd")    
        print (" exiting get_data_in.py")
        sys.exit()                    
    return hgt, uu, vv, temp, shum, vvel
 
