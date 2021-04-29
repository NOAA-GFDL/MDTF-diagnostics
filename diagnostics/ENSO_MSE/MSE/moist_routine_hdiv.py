import numpy as np

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

OUTPUT: MSE_DIV3   3 dimensional horizontal divergence of MSE [W/kg]
        MSE_DIV1   2 dimensional vertical integral of
                      horizontal divergence of MSE  [W/m2]
missing data are flaged by UNDEF which is a very large number
'''

def mse_div(imax, jmax, zmax, lon, lat, plev, hgt, ta, hus, ua, va, rearth, mse_div1, mse_div3, undef):
    #work on process
    #print("mse_div processing...")
    # various constants
    pi = 4.0 * np.arctan(1.0)
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82
    
    undef2 = 0.5 * undef 
    # fill with undef first 
    mse_div3 = np.zeros( (imax,jmax, zmax),dtype='float32', order='F')
    mse_div3[:,:,:] = undef
    mse_div1 = np.zeros( (imax,jmax),dtype='float32', order='F')

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
            
            # loop in vertical  - calculation of advection
            # and integration
            mse_div1[i,j] = 0.0
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
                hh   = hgt[i, j, k]
                hh10 = hgt[ i1, j, k]
                hh20 = hgt[ i2, j, k]
                hh01 = hgt[ i, j1, k]
                hh02 = hgt[ i, j2, k] 
                               
                qq   = hus[i,j,k]
                qq10 = hus[i1,j,k]
                qq20 = hus[i2,j,k]
                qq01 = hus[i,j1,k]
                qq02 = hus[i,j2,k]
                
                tt   = ta[i, j,k]
                tt10 = ta[i1,j,k]
                tt20 = ta[i2,j,k]
                tt01 = ta[i,j1,k]
                tt02 = ta[i,j2,k]
                
                uu =   ua[i,j,k]
                vv  =  va[i,j,k]
                u10  = ua[i1,j,k]
                u20  = ua[i2,j,k]
                v01  = va[i,j1,k]
                v02  = va[i,j2,k]
          
                # perform the calculation only if all input variables
                # are defined (not missing).
                if ((hh < undef2) and (qq < undef2) and (u10 < undef2) and (u20 < undef2) and 
                    (v01  < undef2) and  (v02 < undef2) and (rho < undef2)  and  (tt < undef2) and (dz < undef2)):
                    # the MSE divergence is defined as: MSE * (dU/dx + dV/dy)
                    mse = (cp*tt + gg*hh + lh*qq) * ((u20-u10)/dxx + (v02-v01)/dyy)
                    
                    # vertical integration:
                    # multiplied by density of air to get the W/m2 units
                    mse_div1[i,j] = mse_div1[i,j]  + dz * rho * mse
                    mse_div3[i,j,k] = mse
                    ss = ss + 1.0

            # just in a case all vertial levels are missing
            # set the output to missing
            if(ss <= 0.0):
                mse_div1[i,j] = undef
    return mse_div1, mse_div3
