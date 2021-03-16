import numpy as np
import os.path
import sys

def get_flux_in(imax, jmax,  pr, ts, lhf, shf, sw, lw, prefix, undef):
    print("DRBDBG prefix ",prefix)
    if (os.path.exists(prefix+"/PR.grd")):
        f = open(prefix+'/PR.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        pr = np.reshape( data, (imax, jmax), order='F')
        pr =  pr * 24.*60.*60.
        pr = np.ma.masked_greater_equal( pr,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/PR.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()
##   convert to mm/day   from kg/m2/sec

    if (os.path.exists(prefix+"/TS.grd")):
        f = open(prefix+'/TS.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        ts = np.reshape( data, (imax, jmax), order='F')
        ts = np.ma.masked_greater_equal( ts,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/TS.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/SHF.grd")):
        f = open(prefix+'/SHF.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        shf = np.reshape( data, (imax, jmax), order='F')
        shf = np.ma.masked_greater_equal( shf,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/SHF.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/LHF.grd")):
        f = open(prefix+'/LHF.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        lhf = np.reshape( data, (imax, jmax), order='F')
        lhf = np.ma.masked_greater_equal( lhf,  undef, copy=False)
        f.close()        
    else:
        print ("missing file " + prefix+"/LHF.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()

    if (os.path.exists(prefix+"/SW.grd")):
        f = open(prefix+'/SW.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        sw = np.reshape( data, (imax, jmax), order='F')
        sw = np.ma.masked_greater_equal( sw,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/SW.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()    

    if (os.path.exists(prefix+"/LW.grd")):
        f = open(prefix+'/LW.grd', 'rb')
        data = np.fromfile(f, dtype='float32')
        lw = np.reshape( data, (imax, jmax), order='F')
        lw = np.ma.masked_greater_equal( lw,  undef, copy=False)
        f.close()
    else:
        print ("missing file " + prefix+"/LW.grd")
        print (" exiting get_flux_in.py ")
        sys.exit()
##################                                        
    return  pr, ts, lhf, shf, sw, lw
 
