import numpy as np
import os.path
import math
import sys

from scipy.io import netcdf


import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from read_netcdf_3D import read_netcdf_3D
from read_netcdf_2D import read_netcdf_2D

def get_nino_index(imax, jmax, lon, lat,  itmax, iy1, iy2, im1, im2, llon1, llon2, llat1, llat2, ii1, ii2, jj1, jj2,  sigma, tmax1, tmax2, years1,  years2, prefix, undef):

    tmax1 = 0
    tmax2 = 0
####   need to select the indexes  ii1, ii2,   jj1, jj2  of the area to calculate the sigmas etc
    for i in range(0, imax):
        if( lon[i] <= llon1 and lon[i+1] >= llon1):
            ii1 = i + 1
            break
    for i in range(0, imax):
        if( lon[i] <= llon2 and lon[i+1] >= llon2):
            ii2 = i
            break
    for j in range(0, jmax):
        if( lat[j] <= llat1 and lat[j+1] >= llat1):
            jj1 = j + 1
            break
    for j in range(0, jmax):
        if( lat[j] <= llat2 and lat[j+1] >= llat2):
            jj2 = j
            break
###    define  full 12 month climatology

    im12 = 12

    clima = np.ma.zeros( (imax,jmax, im12),dtype='float32',  order='F')
    sst = np.ma.zeros( (imax,jmax, im12),dtype='float32',  order='F')

###    read in TS from NetCDF
    nameclima = os.path.join(prefix,"../CLIMA","ts_clim.nc")
    if ( os.path.exists(nameclima)):
        print("get_nino_index.py reading "+nameclima)
        clima = read_netcdf_2D(imax, jmax, im12,  "ts",  nameclima, clima, undef)
        clima = np.ma.masked_greater_equal(clima, undef, copy=False)
    else:
        print (" missing file " + nameclima)
        print (" exiting get_nino_index.py ")
        sys.exit()
    ssigma = 0.
    ss = 0.
###   read full TS for select months
    for iy in range(iy1, iy2+1):

        for im in range (im1, im2+1):
            iyy = iy
            imm = im
            if( im > im12 ):
                iyy = iyy + 1
                imm = im - 12
            if( iyy <= iy2 ):

                yy = "%04d" % iyy
                year = str(yy)
                namein = os.path.join(prefix,year,"ts_"+year+".nc")

                if ( os.path.exists(namein) ):
                   sst = read_netcdf_2D(imax, jmax, im12,  "ts",  namein, sst, undef)
                   sst = np.ma.masked_greater_equal(sst, undef, copy=False)
                #    do the calculation of SST sigma
                   for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                          ssigma = ssigma +  (sst[i,j,imm-1]-clima[i, j, imm-1])*(sst[i,j, imm-1]-clima[i, j, imm-1])
                          ss = ss + 1.
                #      get corresponding climatology for anomaly calculations
                #   make the average and swrt to have just SIGMA

                else:
                    print( " missing file " + namein )
                    print( " exiting get_nino_index.py ")
                    sys.exit()
    if( ss > 0.):
        ssigma = ssigma/ss
        ssigma = math.sqrt(ssigma)
    else:
        ssigma = undef

    print ("In reference area the calculated SST r.m.s  = ",  ssigma , " deg. C")
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
                yy = "%04d" % iyy
                year = str(yy)
                namein = os.path.join(prefix,year,"ts_"+year+".nc")
                if ( os.path.exists(namein)):
                    sst = read_netcdf_2D(imax, jmax, im12,  "ts",  namein, sst, undef)
                    sst = np.ma.masked_greater_equal(sst, undef, copy=False)
#     loop over NINO3.4  and  make anomaly
                    for j in range (jj1, jj2):
                        for i in range (ii1, ii2):
                          anom = anom +  (sst[i,j, imm-1] - clima[i, j, imm-1])
                          ss = ss + 1.
                else:
                    print( " missing file " + namein )
                    print( " exiting get_nino_index.py " )
                    sys.exit()

######   average and select
        if( ss > 0.):
            anom = anom/ss
            threshold1 =  sigma * ssigma
            threshold2 = -sigma * ssigma
            if( anom >= threshold1):
                years1[it1] = iy
                it1 = it1 + 1
            if( anom <=  threshold2):
                years2[it2] = iy
                it2 = it2 + 1
            else:
                anom = undef

    tmax1 = it1
    tmax2 = it2
#####
    return ii1, ii2, jj1, jj2,  tmax1, years1, tmax2, years2

