import numpy as np
import os.path
import sys

def get_clima_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
    #print prefix
    if (os.path.exists(prefix+"/U_clim.grd")):
        f = open(prefix+'/U_clim.grd', 'rb')
        uu = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        uu = uu.reshape(zmax,jmax,imax)
        uu = np.swapaxes(uu, 0, 2)
        f.close()
    else:
        print " missing file " + prefix + "/U_clim.grd"
        print " exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/V_clim.grd")):
        f = open(prefix+'/V_clim.grd', 'rb')
        vv = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        vv = vv.reshape(zmax,jmax,imax)
        vv = np.swapaxes(vv, 0, 2)
        f.close()        
    else:
        print " missing file "  + prefix + "/V_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/T_clim.grd")):
        f = open(prefix+'/T_clim.grd', 'rb')
        temp = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        temp = temp.reshape(zmax,jmax,imax)
        temp = np.swapaxes(temp, 0, 2)
        f.close()
    else:
        print "missing file " + prefix + "/T_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/Q_clim.grd")):
        f = open(prefix+'/Q_clim.grd', 'rb')
        shum = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        shum = shum.reshape(zmax,jmax,imax)
        shum = np.swapaxes(shum, 0, 2)
        f.close()
    else:
        print "missing file " + prefix + "/Q_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()
        
    if (os.path.exists(prefix+"/Z_clim.grd")):
        f = open(prefix+'/Z_clim.grd', 'rb')
        hgt = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        hgt = hgt.reshape(zmax,jmax,imax)
        hgt = np.swapaxes(hgt, 0, 2)
        f.close()        
    else:
        print "missing file " + prefix + "/Z_clim.grd"
        print  " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/OMG_clim.grd")):
        f = open(prefix+'/OMG_clim.grd', 'rb')
        vvel = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        vvel = vvel.reshape(zmax,jmax,imax)
        vvel = np.swapaxes(vvel, 0, 2)
        f.close()            
    else:
        print "missing file " + prefix + "/OMG_clim.grd"    
        print " exiting get_clima_in.py"
        sys.exit()    
    return hgt, uu, vv, temp, shum, vvel
 
