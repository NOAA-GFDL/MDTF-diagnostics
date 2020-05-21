import numpy as np
import os.path
import sys

def get_clima_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
    #print prefix
    if (os.path.exists(prefix+"/U_clim.gr")):
        f = open(prefix+'/U_clim.grd', 'rb')
        uu = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print " missing file " + prefix + "/U_clim.grd"
        print " exiting get_clima_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/V_clim.grd")):
        f = open(prefix+'/V_clim.grd', 'rb')
        vv = np.fromfile(f, dtype='float32')
        f.close()        
    else:
        print " missing file "  + prefix + "/V_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/T_clim.grd")):
        f = open(prefix+'/T_clim.grd', 'rb')
        temp = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print "missing file " + prefix + "/T_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/Q_clim.grd")):
        f = open(prefix+'/Q_clim.grd', 'rb')
        shum = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print "missing file " + prefix + "/Q_clim.grd"
        print " exiting get_clima_in.py"
        sys.exit()
        
    if (os.path.exists(prefix+"/Z_clim.grd")):
        f = open(prefix+'/Z_clim.grd', 'rb')
        hgt = np.fromfile(f, dtype='float32')
        f.close()        
    else:
        print "missing file " + prefix + "/Z_clim.grd"
        print  " exiting get_clima_in.py"
        sys.exit()

    if (os.path.exists(prefix+"/OMG_clim.grd")):
        f = open(prefix+'/OMG_clim.grd', 'rb')
        vvel = np.fromfile(f, dtype='float32')
        f.close()            
    else:
        print "missing file " + prefix + "/OMG_clim.grd"    
        print " exiting get_clima_in.py"
        sys.exit()    
    return hgt, uu, vv, temp, shum, vvel
 
