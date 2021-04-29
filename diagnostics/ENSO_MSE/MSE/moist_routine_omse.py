import numpy as np

'''
  routine to calculate the vertical MSE advection and its vertical integral
    
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

def moisture_o_energy(imax, jmax, zmax, lon, lat, plev, hgt, ta, hus, omega, rearth):
    #work on process
    #print("moisture_o_energy processing...")
    # various constants
    pi = 4.0 * np.arctan(1.0)
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82

    plev = plev.reshape((1,1,zmax), order='F')
    rho = plev * 100./(rd * ta)
##     vertical differentiation
    kk = np.arange(0, zmax)
    k1 = np.fmax(0, kk-1)
    k2 = np.fmin(zmax-1, kk+1)
    dz = 0.5 * (hgt[:, :, k2] - hgt[:, :, k1])
##   here need also difference in pressure:
    dplev =  100 * (plev[:,:,k2] - plev[:,:,k1])

##   vertical integral  of :   -omega * dMSE/dp] 
##    MSE = cp*T + g*Hgt + Lh*specific_humidity
    mse =  cp *ta + gg * hgt + lh * hus  
    dmse = ( mse[:,:,k2] - mse[:,:,k1])  
    omse3 =  - ( omega * dmse/dplev)   
    omse1 = np.sum(  rho * omse3 * dz, axis = 2)   
                    
    return omse1, omse3
