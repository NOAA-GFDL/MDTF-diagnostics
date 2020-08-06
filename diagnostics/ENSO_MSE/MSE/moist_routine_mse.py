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

OUTPUT: MSE3  3 dimensional MSE [J/kg]
        MSE1  2 dimensional vertical integral of MSE [J/m2]

missing data are flaged by UNDEF which is a very large number
'''

def moisture_energy(imax, jmax, zmax, lon, lat, plev, hgt, ta, hus, ua, va, rearth, mse1, mse3, undef):
    #work on process
    #print("moisture_energy processing...")
    # various constants
    pi = 4.0 * np.arctan(1.0)
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82

    undef2 = 0.5 * undef 
    # fill with undef first 
    mse3 = np.zeros( (imax,jmax, zmax),dtype='float32', order='F')
    mse3[:,:,:] = undef
    mse1 = np.zeros( (imax,jmax),dtype='float32', order='F')
    # calculate  the advection  loop over all domain points
    # except the top and bottom J = 1, J= JMAX
    # calculations are based on center differences
    for j in range(1, jmax-1):
        for i in range(0, imax):            
            # vertical integral  of MSE 
            mse1[i,j] = 0.0
            ss  = 0.0
            for k in range(0, zmax):
                k1 = max(0, k-1)
                k2 = min(zmax-1, k+1)
                # to simplify the coding the various input variables for differentiation are selected here
                
                za1  = hgt[i,j,k1]
                za2  = hgt[i,j,k]
                za3  = hgt[i,j,k2]
                
                ta2  = ta[i,j,k]
                za2  = hgt[i,j,k]
                qq2  = hus[i,j,k]
      
                # perform the calculation only if all input variables
                # are defined (not missing).
                if ((ta2 < undef2) and (za2 < undef2) and (za1 < undef2) and (za3 < undef2) and (qq2 < undef2)):
                    # density of air needed, for conversio to J/m2 
                    rho = plev[k] * 100./(rd*ta2) 
                    # vertical differential, needed for integration
                    dz = 0.5 *(za3-za1) 
                    # the MSE  is defined as cp*T + g*Hgt  + Lh*specific_humidity 
                    xx2 = cp*( ta2) + gg*(za2) + lh*( qq2)                    
                    # vertical integration multiply by density to get [J/m2]
                    mse1[i,j] = mse1[i,j] +  rho * xx2 * dz 
                    # just MSE alone
                    mse3[i,j, k] = xx2 
                    ss = ss + 1.0

            # just in a case all vertical levels are missing
            # set the output to missing
            if(ss <= 0.0):
                mse1[i,j] = undef
    return mse1, mse3
