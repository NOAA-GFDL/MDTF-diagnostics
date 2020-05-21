import numpy as np
import os.path
import sys

def get_flux_in(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    print("DRBDBG prefix ",prefix)
    if (os.path.exists(prefix+"/PR.grd")):
        f = open(prefix+'/PR.grd', 'rb')
        pr = np.fromfile(f, dtype='float32')
        pr =  pr * 24.*60.*60.
        f.close()
    else:
        print "missing file " + prefix+"/PR.grd"
        print " exiting get_flux_in.py "
        sys.exit()
##   convert to mm/day   from kg/m2/sec

    if (os.path.exists(prefix+"/TS.grd")):
        f = open(prefix+'/TS.grd', 'rb')
        ts = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print  "missing file " + prefix+"/TS.grd"
        print " exiting get_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/SHF.grd")):
        f = open(prefix+'/SHF.grd', 'rb')
        shf = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print "missing file " + prefix+"/SHF.grd"
        print " exiting get_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/LHF.grd")):
        f = open(prefix+'/LHF.grd', 'rb')
        lhf = np.fromfile(f, dtype='float32')
        f.close()        
    else:
        print "missing file " + prefix+"/LHF.grd"
        print " exiting get_flux_in.py "
        sys.exit()

    if (os.path.exists(prefix+"/SW.grd")):
        f = open(prefix+'/SW.grd', 'rb')
        sw = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print "missing file " + prefix+"/SW.grd"
        print " exiting get_flux_in.py "
        sys.exit()    

    if (os.path.exists(prefix+"/LW.grd")):
        f = open(prefix+'/LW.grd', 'rb')
        lw = np.fromfile(f, dtype='float32')
        f.close()
    else:
        print  "missing file " + prefix+"/LW.grd"
        print " exiting get_flux_in.py "
        sys.exit()
##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
