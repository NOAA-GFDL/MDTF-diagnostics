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

OUTPUT: MADV3  3 dimensional vertical MSE advection  [W/kg]
        MADV1  2 dimensional vertical integral of
                      of vertical advection of MSE  [W/m2]
  missing data are flaged by UNDEF which is a very large number
'''

def moisture_o_energy(imax, jmax, zmax, lon, lat, plev, hgt, ta, hus, omega, rearth, omse1, omse3, undef):
    #work on process
    #print("moisture_o_energy processing...")
    # various constants
    pi = 4.0 * np.arctan(1.0)
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82

    undef2 = 0.5 * undef 
    # fill with undef first 
    for j in range(0, jmax):
        for i in range (0, imax):
            omse1[i,j] = undef
            for k in range(0, zmax):
                omse3[i,j,k] = undef

    # calculate  the advection  loop over all domain points
    # except the top and bottom J = 1, J= JMAX
    # calculations are based on center differences
    for j in range(1, jmax-1):
        for i in range(0, imax):
            
            # vertical integral of MSE is defined as :integral[omega* dMSE/dp] * dz 
            omse1[i,j] = 0.0
            ss  = 0.0
            for k in range(0, zmax):
                k1 = max(0, k-1)
                k2 = min(zmax-1, k+1)

                # pressure differential  needed for advection calculations 
                dplev = 100.* (plev[k2] - plev[k1]) 
                hhgt  = hgt[i,j,k]
                
                # vertical differential needed for integration 
                if((hgt[i,j,k2] < undef2) and (hgt[i,j,k1] < undef2)):
                    dz = (hgt[i,j,k2]-hgt[i,j,k1]) *0.5
                else:
                    dz = undef
                # to simplify the coding the various 
                #  input variables for differentiation are selected here
                omg  = omega[i,j,k]
                ta1  = ta[i,j,k1]
                ta2  = ta[i,j,k]
                ta3  = ta[i,j,k2]
                za1  = hgt[i,j,k1]
                za2  = hgt[i,j,k]
                za3  = hgt[i,j,k2]
                qq1  = hus[i,j,k1]
                qq2  = hus[i,j,k]
                qq3  = hus[i,j,k2]     
          
                # perform the calculation only if all input variables
                # are defined (not missing).
                if ((ta1 < undef2) and (ta3 < undef2) and (za1 < undef2) and (za3 < undef2) and 
                    (qq1 < undef2) and (qq3 < undef2) and (omg < undef2) and (ta2 < undef2) and (dz < undef2)):
                    # density needed for W/m2 conversion
                    rho = plev[k] * 100./(rd*ta2)
                    # vertical differential
                    dz = (za3 - za1) * 0.5  
                    # vertical pressure differential of MSE
                    # MSE = cp*T + g*Hgt + Lh*specific_humidity
                    # here XX1 is the vertical differential d(MSE) 
                    xx1 = cp*( ta3 - ta1) + gg*(za3 - za1) + lh*( qq3 - qq1)
                    # muliply by -1 to get advection,  -omega*dMSE/dp       
                    xx1 = -1. *  omg* xx1/dplev
                    
                    # integration in vertical  - multiply by density RHO to convert to W/m2
                    omse1[i,j] = omse1[i,j] + rho *  dz *  xx1
                    omse3[i,j,k] = xx1

                    ss = ss + 1.0

            # just in a case all vertical levels are missing
            # set the output to missing
            if(ss <= 0.0):
                omse1[i,j] = undef
    return omse1, omse3
