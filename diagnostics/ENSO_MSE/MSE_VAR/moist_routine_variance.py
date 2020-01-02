import numpy as np

'''
  routine to calculate the variances and CO-variances 
    of vertically integrated MSE variables
    
  INPUT: 2 dimensional atmospheric variables: all vertical integrals 
   dimensions:  IMAX, JMAX
   variables : TS  :  skin surface  temperature [K]
               PR  :  precipitation rate [kg/m2/sec]
               LHF :  latent heat flux  [W/m2]
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
               TS_VAR:  skin surface  temperature [K]
               PR_VAR :  precipitation rate [kg/m2/sec]
               LHF_VAR :  latent heat flux  [W/m2]
               SHF_VAR :  sensible heat flux  [W/m2]
               SW_VAR  :  net  shortwave flux [W/m2]
               LW_VAR  :  net  longwave flux [W/m2]
               MSE_VAR :  vertical integral of Moist Static Energy [J/m2]
               MADV_VAR :  moisture advection [W/m2]
               OMSE_VAR  : MSE vertical advection [W/m2]


  missing data are flaged by UNDEF which is a very large number
'''

def moisture_variance(imax, jmax, zmax, lon1, lon2, lat1, lat2, lon, lat, plev, ts, pr, shf, lhf, sw, lw, mse, madv, omse,  tadv, ts_var, pr_var, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var, undef,  undef2):
    
    ts_var = undef2
    pr_var = undef2
    shf_var = undef2
    lhf_var = undef2
    sw_var = undef2
    lw_var = undef2
    mse_var = undef2
    madv_var = undef2
    omse_var = undef2
    tadv_var = undef2
   
    factor  =  1./(30.*24.*60.*60.)
##    convert mm/day to W/m2
    prfactor =  2.5E+06  ##28.9 ###  (2.5E+06)/(24.*60.*60.)
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
##  ts  variance !!  rest  CO-variances  except mse !!
    ss = 0.
    cc = 0. 
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(ts[i,j] < undef):  
                cc = cc + ts[i,j]*ts[i,j]   
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        ts_var = cc/ss
##   pr
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(pr[i,j] < undef):  
                cc = cc + prfactor*pr[i,j]*prfactor*pr[i,j]  
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        pr_var = cc/ss
##   shf
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(shf[i,j] < undef and mse[i,j] < undef):
                cc = cc + shf[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        shf_var = cc/ss
##   lhf
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(lhf[i,j] < undef):
                cc = cc + lhf[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        lhf_var = cc/ss
##    SW
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(sw[i,j] < undef and  mse[i,j] < undef):
                cc = cc + sw[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        sw_var = cc/ss
##    LW
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(lw[i,j] < undef  and  mse[i,j] < undef):
                cc = cc + lw[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        lw_var = cc/ss

##      MSE  variance 
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(mse[i,j] < undef):
                cc = cc + factor*mse[i,j]* factor*mse[i,j]
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        mse_var =  (cc/ss)
##       Madv
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(madv[i,j] < undef  and  mse[i,j] < undef):
                cc = cc + madv[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo 
    if( ss > 0.):
        madv_var = (cc/ss)

###  Tadv 
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(tadv[i,j] < undef  and  mse[i,j] < undef):
                cc = cc + tadv[i,j]*mse[i,j]*factor
                ss = ss + 1.
##    endif enddo
    if( ss > 0.):
        tadv_var = (cc/ss)


### OMSE 
    ss = 0.
    cc = 0.
    for j in range(jj1, jj2):
        for i in range (ii1, ii2):
            if(omse[i,j] < undef  and  mse[i,j] < undef):
                cc = cc + omse[i,j]*mse[i,j]*factor
                ss = ss + 1.
##           end if  end do 
    if( ss > 0.):
        omse_var = (cc/ss)

    return ts_var, pr_var, shf_var, lhf_var, sw_var, lw_var, mse_var, madv_var, omse_var, tadv_var
