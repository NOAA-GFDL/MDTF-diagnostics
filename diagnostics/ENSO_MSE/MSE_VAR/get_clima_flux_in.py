import numpy as np
import os.path
import sys

def get_clima_flux_in(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    if (os.path.exists(prefix+"/PR_clim.grd")):
        f = open(prefix+'/PR_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        pr =  np.reshape( data, (imax, jmax), order='F')
        pr =  pr * 24.*60.*60.
        pr = np.ma.masked_greater_equal( pr,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/PR_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()

##   convert to mm/day   from kg/m2/sec

    if (os.path.exists(prefix+"/TS_clim.grd")):
        f = open(prefix+'/TS_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        ts = np.reshape( data, (imax, jmax), order='F')
        ts = np.ma.masked_greater_equal( ts,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/TS_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/SHF_clim.grd")):
        f = open(prefix+'/SHF_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32') 
        shf =  np.reshape( data, (imax, jmax), order='F')
        shf =  np.ma.masked_greater_equal( shf,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/SHF_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/LHF_clim.grd")):
        f = open(prefix+'/LHF_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        lhf = np.reshape( data, (imax, jmax), order='F')
        lhf = np.ma.masked_greater_equal( lhf, undef, copy=False)
        f.close()        
    else:
        print ("missing file " + prefix+"/LHF_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/SW_clim.grd")):
        f = open(prefix+'/SW_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        sw = np.reshape( data, (imax, jmax), order='F')
        sw = np.ma.masked_greater_equal( sw, undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/SW_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/LW_clim.grd")):
        f = open(prefix+'/LW_clim.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        lw = np.reshape( data, (imax, jmax), order='F')
        lw = np.ma.masked_greater_equal( lw, undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/LW_clim.grd")
        print (" exiting get_clima_flux_in.py ")
        sys.exit()
##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
