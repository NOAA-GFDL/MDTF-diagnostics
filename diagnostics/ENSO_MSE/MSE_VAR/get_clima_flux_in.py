import numpy as np
import os.path
import sys

def get_clima_flux_in(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    if (os.path.exists(prefix+"/PR_clim.grd")):
        f = open(prefix+'/PR_clim.grd', 'rb')
        pr = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        pr = pr.reshape(jmax, imax)
        pr = np.swapaxes(pr, 0, 1)
        pr =  pr * 24.*60.*60.
        f.close()
    else:
        print "missing file " + prefix+"/PR_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()

##   convert to mm/day   from kg/m2/sec

    if (os.path.exists(prefix+"/TS_clim.grd")):
        f = open(prefix+'/TS_clim.grd', 'rb')
        ts = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        ts = ts.reshape(jmax, imax)
        ts = np.swapaxes(ts, 0, 1)
        f.close()
    else:
        print "missing file " + prefix+"/TS_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/SHF_clim.grd")):
        f = open(prefix+'/SHF_clim.grd', 'rb')
        shf = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        shf = shf.reshape(jmax, imax)
        shf = np.swapaxes(shf, 0, 1)
        f.close()
    else:
        print "missing file " + prefix+"/SHF_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/LHF_clim.grd")):
        f = open(prefix+'/LHF_clim.grd', 'rb')
        lhf = np.fromfile(f, dtype='float32')
        # reshape to t, y, x
        lhf = lhf.reshape(jmax, imax)
        lhf = np.swapaxes(lhf, 0, 1)
        f.close()        
    else:
        print "missing file " + prefix+"/LHF_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/SW_clim.grd")):
        f = open(prefix+'/SW_clim.grd', 'rb')
        sw = np.fromfile(f, dtype='float32')
              # reshape to t, y, x    
        sw = sw.reshape(jmax, imax)
        sw = np.swapaxes(sw, 0, 1)
        f.close()
    else:
        print "missing file " + prefix+"/SW_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/LW_clim.grd")):
        f = open(prefix+'/LW_clim.grd', 'rb')
        lw = np.fromfile(f, dtype='float32')
        lw = lw.reshape(jmax, imax)
        lw = np.swapaxes(lw, 0, 1)
        f.close()
    else:
        print "missing file " + prefix+"/LW_clim.grd"
        print " exiting get_clima_flux_in.py "
        sys.exit()
##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
