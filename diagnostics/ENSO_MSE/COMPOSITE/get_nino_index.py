import numpy as np
import os.path
import math
import sys

def get_nino_index(imax, jmax, lon, lat,  itmax, iy1, iy2, im1, im2, llon1, llon2, llat1, llat2, ii1, ii2, jj1, jj2,  sigma, tmax1, tmax2, years1,  years2, prefix, undef):
####   need to select the indexes  ii1, ii2,   jj1, jj2  of the area to calculate the sigmas etc
    for i in range(0, imax):
        if( lon[i] <= llon1 and lon[i+1] >= llon1):
            ii1 = i+1
            break
    for i in range(0, imax):
        if( lon[i] <= llon2 and lon[i+1] >= llon2):    
            ii2 = i
            break
    for j in range(0, jmax):
        if( lat[j] <= llat1 and lat[j+1] >= llat1):
            jj1 = j+1
            break
    for j in range(0, jmax):
        if( lat[j] <= llat2 and lat[j+1] >= llat2):
            jj2 = j
            break
###    define  full 12 month climatology 
    im12 = 12

    clima = np.zeros((imax,jmax, im12),dtype='float32')

    nameclima = prefix+"/../CLIMA/TS_clim.grd"
    if ( os.path.exists(nameclima)):
        print("get_nino_index.py reading "+nameclima)
        f = open(nameclima)
        clima1 = np.fromfile(f, dtype='float32')
        #reshape to t, y, x
        clima1 = clima1.reshape(im12,  jmax,imax)
        clima = np.swapaxes(clima1, 0, 2)
        f.close()
    else:
        print " missing file " + nameclima
        print " exiting get_nino_index.py "
        sys.exit()
    ssigma = 0.
    ss = 0.
    for iy in range(iy1, iy2+1):    
        for im in range (im1, im2+1):
            iyy = iy
            imm = im
            if( im > im12 ):
                iyy = iyy + 1
                imm = im - 12
            if( iyy <= iy2 ):
                mm = "%02d" % imm
                month = str(mm)
                yy = "%04d" % iyy
                year = str(yy)
                namein = prefix+"/"+year+"/TS_"+year+"-"+month+".grd"

                if ( os.path.exists(namein) ):
                    f = open(namein)
                    sst1 = np.fromfile(f, dtype='float32')
                # reshape to t, y, x
                    sst1 = sst1.reshape(jmax,imax)
                    sst = np.swapaxes(sst1, 0, 1)
                #     do the calculation of SST sigma 
                    for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                            if( (sst[i,j] < undef) & (clima[i, j, imm-1] < undef) ):
                                ssigma = ssigma +  (sst[i,j]-clima[i, j, imm-1])*(sst[i,j]-clima[i, j, imm-1])
                                ss = ss + 1.
                #      get corresponding climatology for anomaly calculations
                #   make the average and swrt to have just SIGMA
            
                    f.close()
                else:    
                    print " missing file " + namein 
                    print " exiting get_nino_index.py " 
                    sys.exit()
    if( ss > 0.):
        ssigma = ssigma/ss
        ssigma = math.sqrt(ssigma)
    else:
        ssigma = undef 

    print "In reference area the calculated SST r.m.s  = ",  ssigma , " deg. C"
####   
##       loop over years and select years with SST anomaly  over +1. sigma 
##     the  selected year refers to  first month in the season (e.g. Dec in DJF)
    it1 = 0
    it2 = 0
    for iy in range(iy1, iy2+1):
        anom = 0.
        ss = 0.
        for im in range (im1, im2+1):
            iyy = iy
            imm = im
            if( im > im12 ):
                iyy = iyy + 1
                imm = im - 12
            if( iyy <= iy2 ):
                mm = "%02d" % imm
                month = str(mm)
                yy = "%04d" % iyy
                year = str(yy)
                namein = prefix+"/"+year+"/TS_"+year+"-"+month+".grd"
                if ( os.path.exists(namein)):
                    f = open(namein)        
                    sst1 = np.fromfile(f, dtype='float32')
                     # reshape to t, y, x
                    sst1 = sst1.reshape(jmax,imax)
                    sst = np.swapaxes(sst1, 0, 1)
                    f.close()
#     loop over NINO3.4  and  make anomaly 
                    for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                            if( (sst[i,j] < undef) & (clima[i, j, imm-1] < undef) ):
                                anom = anom +  (sst[i,j] - clima[i, j, imm-1])
                                ss = ss + 1.
                else: 
                    print " missing file " + namein
                    print " exiting get_nino_index.py " 
                    sys.exit()

######   average and select      
        if( ss > 0.):
            anom = anom/ss
            threshold1 = sigma* ssigma
            threshold2 = -sigma* ssigma
            if( anom >= threshold1):    
                years1[it1] = iy
                it1 = it1 + 1
            if( anom <=  threshold2):
                years2[it2] = iy
                it2 = it2 + 1
            else:
                anom = undef    

    tmax1 = it1 - 1
    tmax2 = it2 -1
#####
    
    return ii1, ii2, jj1, jj2,  tmax1, years1, tmax2, years2
 
