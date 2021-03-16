import numpy as np

import sys
##import subprocess
##import commands


'''
  routine to calculate the variances and CO-variances 
    of vertically integrated MSE variables
    
  INPUT: 2 dimensional atmospheric variables: all vertical integrals 
   dimensions:  IMAX, JMAX
   variables : LHF :  latent heat flux  [W/m2]
               SHF :  sensible heat flux  [W/m2]
               SW  :  net  shortwave flux [W/m2]
               LW  :  net  longwave flux [W/m2]
               MSE :  vertical integral of Moist Static Energy [J/m2]
               MADV :  moisture advection [W/m2]
               OMSE  : MSE vertical advection [W/m2]
   1 dimensional INPUT:
         LON(IMAX) - longitude deg.
         LAT(JMAX) - latitude deg.
         PLEV(ZMAX) - pressure levels [mb]
         REARTH  - radius of earth in  [m]

     pamaters LON1, LON2, LAT1, LAT2   for spatial variances
OUTPUT:   variances of input variables (over selected area)
               LHF_VAR :  latent heat flux  [W/m2]
               SHF_VAR :  sensible heat flux  [W/m2]
               SW_VAR  :  net  shortwave flux [W/m2]
               LW_VAR  :  net  longwave flux [W/m2]
               MSE_VAR :  vertical integral of Moist Static Energy [J/m2]
               MADV_VAR :  moisture advection [W/m2]
               OMSE_VAR  : MSE vertical advection [W/m2]


  missing data are flaged by UNDEF which is a very large number
'''

def moisture_variance(imax, jmax, zmax, lon1, lon2, lat1, lat2, lon, lat, plev, ts, pr, shf, lhf, sw, lw, mse, madv, omse,  tadv, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var, undef):
    
#    shf_var = undef
#    lhf_var = undef
#    sw_var = undef
#    lw_var = undef
#    mse_var = undef
#    madv_var = undef
#    omse_var = undef
#    tadv_var = undef
   
##    
#     select the averaging indexes  over the respective boxes 
    for i in range(0, imax):
              if( lon[i] <= lon1 and lon[i+1] >= lon1):
                     ii1 = i+1
                     break
    for i in range(0, imax):
              if( lon[i] <= lon2 and lon[i+1] >= lon2):
                     ii2 = i
                     break
    for j in range(0, jmax):
              if( lat[j] <= lat1 and lat[j+1] >= lat1):
                     jj1 = j+1
                     break
    for j in range(0, jmax):
              if( lat[j] <= lat2 and lat[j+1] >= lat2):
                     jj2 = j
                     break
###
##      MSE  variance
    yy = mse[ii1:ii2, jj1:jj2]
    yy = yy.flatten('F')
    mse_var =  np.mean(yy * yy)

##   shf   covariance with MSE
    xx = shf[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    shf_var =  np.mean(xx * yy)

##   lhf
    xx = lhf[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    lhf_var =  np.mean(xx * yy)

##    SW
    xx = sw[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    sw_var =  np.mean(xx * yy)

##    LW
    xx = lw[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    lw_var =  np.mean(xx * yy)

##       Madv
    xx = madv[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    madv_var =  np.mean(xx * yy)
 
###  Tadv 
    xx = tadv[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    tadv_var =  np.mean(xx * yy)
   
### OMSE 
    xx = omse[ii1:ii2, jj1:jj2]
    xx = xx.flatten('F')
    omse_var =  np.mean(xx * yy)

    return shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var
