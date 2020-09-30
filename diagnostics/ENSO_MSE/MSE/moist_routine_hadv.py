import numpy as np
import sys

'''
    routine to calculate the horizontal moisture advection and its
    vertical integral
    
    INPUT: 3 dimensional atmospheric variables:
    dimensions:  IMAX, JMAX, ZMAX
    variables : HGT: geopotential height [m]
               TA : temperature [K]
               HUS:  specific humidity [kg/kg]
               UA:  U wind compoment [m/s]
               VA:  V wind component [m/s]
    1 dimensional INPUT:
         LON(IMAX) - longitude deg.
         LAT(JMAX) - latitude deg.
         PLEV(ZMAX) - pressure levels [mb]
         REARTH  - radius of earth in  [m]

OUTPUT: MSE_ADV3  3 dimensional horizontal moisture advection  [W/kg]
        MSE_ADV1  2 dimensional vertical integral of horizontal moisture advection  [W/m2]
missing data are flaged by UNDEF which is a very large number
'''

def mse_adv(imax, jmax, zmax, lon, lat, plev, hgt, ta, hus, ua, va, rearth, mse_adv1, mse_adv3, undef):
    #work on process
    #print("mse_adv processing...")
    # various constants
    pi = 4.0 * np.arctan(1.0)
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82
    undef2 =0.5 * undef
    # fill with undef first 
    mse_adv3 = np.zeros( (imax,jmax, zmax),dtype='float32', order='F')
    mse_adv3[:,:,:] = undef 
    mse_adv1 = np.zeros( (imax,jmax),dtype='float32', order='F') 

    # calculate  the advection  loop over all domain points
    # except the top and bottom J = 1, J= JMAX
    # calculations are based on center differences
    for j in range(1, jmax-1):
        for i in range(0, imax):
            # selected indexes for differentiation scheme
            j1 = max(0, j-1)
            j2 = min(jmax-1, j+1)
            i1 = max(0, i-1)
            i2 = min(imax-1, i+1)

            # calculate the distance differences along x, and y axis
            # between grid poins i-1, i+1,  j-1, j+1
            dxx = rearth * np.cos(lat[j]*pi/180.0) * (lon[i2]-lon[i1]) * pi/180.0
            dyy = rearth * (lat[j2] - lat[j1]) * pi/180.0
            ## print( i1, i2, j1, j2,  lon[i1], lon[i2], lat[j1], lat[j2], dxx , " " , dyy )

            # loop in vertical  - calculation of advection
            # and integration
            mse_adv1[i,j] = 0.0
            ss  = 0.0
            for k in range(0, zmax):
                k1 = max(0, k-1)
                k2 = min(zmax-1, k+1)

                # calculate the air density - needed for conversion to W/m2
                if(ta[i,j,k] < undef2): 
                    rho = plev[k]*100.0/(rd*ta[i,j,k]) 
                else:
                    rho = undef
                # height differential - dz - needed for vertical integration
                if((hgt[i,j,k2] < undef2) and (hgt[i,j,k1] < undef2)):
                    dz = (hgt[i,j,k2]-hgt[i,j,k1]) *0.5
                else:
                    dz = undef
                    
                # to simplify the coding the various
                # input variables for differentiation are selected here
                qq   = hus[i,j,k]
                qq11 = hus[i1,j,k]
                qq21 = hus[i2,j,k]
                qq12 = hus[i,j1,k]
                qq22 = hus[i,j2,k]
                
                zz   = hgt[i,j,k]
                zz11 = hgt[i1,j,k]
                zz21 = hgt[i2,j,k]
                zz12 = hgt[i,j1,k]
                zz22 = hgt[i,j2,k]
                
                tt   = ta[i, j,k]
                tt11 = ta[i1,j,k]
                tt21 = ta[i2,j,k]
                tt12 = ta[i,j1,k]
                tt22 = ta[i,j2,k]
                
                uu =   ua[i,j,k]
                vv  =  va[i,j,k]
                u11  = ua[i1,j,k]
                u21  = ua[i2,j,k]
                v12  = va[i,j1,k]
                v22  = va[i,j2,k]
                          
                # perform the calculation only if all input variables
                # are defined (not missing).
                if ((dz < undef2) and 
                    (qq11 < undef2) and (qq21 < undef2) and (qq12 < undef2) and (qq22  < undef2) and 
                    (tt11 < undef2) and (tt21 < undef2) and (tt12 < undef2) and (tt22  < undef2) and 
                    (zz11 < undef2) and (zz21 < undef2) and (zz12 < undef2) and (zz22  < undef2) and 
                    (uu < undef2) and (vv < undef2) and (rho < undef2)):
                    # the MSE is defined as cp*T + g*Hgt + Lh*specific_humidity
                    #      XX1 is differentiation of MSE along x i.e. d(MSE)/dx
                    #      XX2 is diff. of MSE along y . i.e. d(MSE)/dy
                    xx1 = cp*(tt21 - tt11) + lh*(qq21 - qq11) + gg*(zz21 - zz11)
                    xx2 = cp*(tt22 - tt12) + lh*(qq22 - qq12) + gg*(zz22 - zz12)
                    xx =  uu * xx1/(dxx) +  vv * xx2/(dyy) 
                    
                    # evaluation of U*d(MSE)/dx + V*d(MSE)/dy 
                                              
                    # vertical integration:   muliply by density of air to get w/m2
                    # also minus sign to make it advection as defined
                    mse_adv1[i,j] = mse_adv1[i,j] - xx * dz * cp * rho
                    mse_adv3[i,j,k] = -xx
                    ss = ss + 1.0

            # just in a case all vertial levels are missing
            # set the output to missing
            if(ss <= 0.0):
                mse_adv1[i,j] = undef
    return mse_adv1, mse_adv3
