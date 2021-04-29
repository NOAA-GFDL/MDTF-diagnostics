import numpy as np
import os.path
import sys

def get_clima_in(imax, jmax, zmax, hgt, uu, vv, temp, shum, vvel, prefix, undef):
    #print prefix
    if (os.path.exists(prefix+"/U_clim.grd")):
        f = open(prefix+'/U_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        uu = np.reshape( aa1, (imax, jmax, zmax), order='F')
        uu = np.ma.masked_greater_equal( uu, undef, copy=False)
        f.close()
    else:
        print (" missing file " + prefix + "/U_clim.grd")
        print (" exiting get_clima_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/V_clim.grd")):
        f = open(prefix+'/V_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        vv = np.reshape( aa1, (imax, jmax, zmax), order='F')
        vv = np.ma.masked_greater_equal( vv, undef, copy=False)
        f.close()        
    else:
        print (" missing file "  + prefix + "/V_clim.grd")
        print (" exiting get_clima_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/T_clim.grd")):
        f = open(prefix+'/T_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        temp = np.reshape( aa1, (imax, jmax, zmax), order='F')
        temp = np.ma.masked_greater_equal(  temp,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix + "/T_clim.grd")
        print (" exiting get_clima_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/Q_clim.grd")):
        f = open(prefix+'/Q_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        shum = np.reshape( aa1, (imax, jmax, zmax), order='F')
        shum = np.ma.masked_greater_equal( shum, undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix + "/Q_clim.grd")
        print (" exiting get_clima_in.py")
        sys.exit()
        
    if (os.path.exists(prefix+"/Z_clim.grd")):
        f = open(prefix+'/Z_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        hgt = np.reshape( aa1, (imax, jmax, zmax), order='F')
        hgt = np.ma.masked_greater_equal( hgt, undef, copy=False)
        f.close()        
    else:
        print ("missing file " + prefix + "/Z_clim.grd")
        print (" exiting get_clima_in.py")
        sys.exit()

    if (os.path.exists(prefix+"/OMG_clim.grd")):
        f = open(prefix+'/OMG_clim.grd', 'rb')
        aa1 = np.fromfile(f, dtype='float32')
        vvel = np.reshape( aa1, (imax, jmax, zmax), order='F')
        vvel = np.ma.masked_greater_equal( vvel, undef, copy=False)
        f.close()            
    else:
        print ("missing file " + prefix + "/OMG_clim.grd")
        print (" exiting get_clima_in.py")
        sys.exit()    
    return hgt, uu, vv, temp, shum, vvel
 
