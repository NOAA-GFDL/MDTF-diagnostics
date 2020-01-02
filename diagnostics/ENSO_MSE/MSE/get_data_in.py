import numpy as np
import os.path
import sys

def get_data_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
##    print prefix
    if (os.path.exists(prefix+"/U.grd")):
        f = open(prefix+'/U.grd', 'rb')
        uu = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        uu = uu.reshape(zmax,jmax,imax)
        uu = np.swapaxes(uu, 0, 2)
        f.close() 
    else:    
        print " missing file " + prefix + "/U.grd"
        print " exiting get_data_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/V.grd")):
        f = open(prefix+'/V.grd', 'rb')
        vv = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        vv = vv.reshape(zmax,jmax,imax)
        vv = np.swapaxes(vv, 0, 2)
        f.close()
    else:
        print " missing file " +  prefix + "/V.grd"    
        print " exiting get_data_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/T.grd")):
        f = open(prefix+'/T.grd', 'rb')
        temp = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        temp = temp.reshape(zmax,jmax,imax)
        temp = np.swapaxes(temp, 0, 2)
        f.close()
    else:
        print " missing file " + prefix + "/T.grd"
        print " exiting get_data_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/Q.grd")):
        f = open(prefix+'/Q.grd', 'rb')
        shum = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        shum = shum.reshape(zmax,jmax,imax)
        shum = np.swapaxes(shum, 0, 2)
        f.close()
    else:
        print  " missing file " +  prefix + "/Q.grd"
        print " exiting get_data_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/Z.grd")):
        f = open(prefix+'/Z.grd', 'rb')
        hgt = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        hgt = hgt.reshape(zmax,jmax,imax)
        hgt = np.swapaxes(hgt, 0, 2)
        f.close()        
    else:
        print " missing file " + prefix + "/Z.grd"
        print " exiting get_data_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/OMG.grd")):
        f = open(prefix+'/OMG.grd', 'rb')
        vvel = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        vvel = vvel.reshape(zmax,jmax,imax)
        vvel = np.swapaxes(vvel, 0, 2)
        f.close()        
    else:
        print " missing file " + prefix + "/OMG.grd"    
        print " exiting get_data_in.py"
        sys.exit()                    
    return hgt, uu, vv, temp, shum, vvel
 
