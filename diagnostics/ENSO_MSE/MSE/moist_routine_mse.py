import numpy as np

'''
    routine to calculate the MSE and its vertical integral
    
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

def moisture_energy(imax, jmax, zmax, plev, hgt, ta, hus):
    #print("moisture_energy processing...")
    # various constants
    lh = 2.5e+6
    cp = 1004.0
    
    rd = 287.0
    gg = 9.82

    # fill with undef first 
    mse3 = cp * ta + gg * hgt + lh * hus
 
    plev = plev.reshape((1,1,zmax), order='F')
    rho = plev * 100./(rd * ta)

    kk = np.arange(0, zmax)
    k1 = np.fmax(0, kk-1)
    k2 = np.fmin(zmax-1, kk+1)

    dz = 0.5 * (hgt[:, :, k2] - hgt[:, :, k1])

    mse1 = np.sum(rho * mse3 * dz, axis=2)
 
##    print("moisture_energy processing end")
    return mse1, mse3
