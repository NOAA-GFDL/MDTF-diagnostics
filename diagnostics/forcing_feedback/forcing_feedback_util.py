# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcing_feedback_util.py
#
# Provide functions called by forcing_feedback.py
#
# This file is part of the Forcing Feedback Diagnostic Package and the
# MDTF code package. See LICENSE.txt for the license.
#
# Including:
#  (1) fluxanom_calc_4D
#  (2) fluxanom_calc_3D
#  (3) esat_coef
#  (4) latlonr3_3D4D
#  (5) globemean_3D
#  (6) fluxanom_nc_create
#  (7) feedback_regress
#
# ======================================================================
# Import standard Python packages 

import os
import sys
#import subprocess
import numpy as np
import numpy.ma as ma
import xarray as xr
#import requests
from scipy.interpolate import interp1d
from scipy.interpolate import griddata

# ======================================================================
#fluxanom_calc_4D
#  computes anomalies of radiatively-relevant 4D climate variable and multiplies
#  by radiative kernel to convert to radiative flux change. Clear- and all-sky calculations

def fluxanom_calc_4D(var_pert, var_base, tot_kern, clr_kern, dpsfc, levs):
    #Pressure of upper boundary of each vertical layer
    pt = (levs[1:]+levs[:-1])/2
    pt = np.append(pt,0)
    #Pressure of lower boundary of each vertical layer
    pb = pt[:-1]
    pb = np.insert(pb,0,1000)
    #Pressure thickness of each vertical level
    dp = pb - pt
     
    sp = var_pert.shape
    sb = var_base.shape
    skt = tot_kern.shape
    skc = clr_kern.shape

    dp_mat =  np.squeeze(np.repeat(np.repeat(np.repeat(\
                         dp[np.newaxis,1:],np.int(sp[0]/12),axis=0)[:,:,np.newaxis],sp[2],axis=2)[:,:,:,np.newaxis],sp[3],axis=3))

    if len(skt)!=4 or len(skc)!=4 or len(sp)!=4 or len(sb)!=4:
       print("An input variable is not 4D! Function will not execute")
    else:
       #Prep variable to analyze on a monthly-basis
       var_pert_re = np.reshape(var_pert, (np.int(sp[0]/12),12,sp[1],sp[2],sp[3]))
       var_base_re = np.reshape(var_base, (np.int(sb[0]/12),12,sb[1],sb[2],sb[3]))
 
       flux_tot = np.zeros((np.int(sp[0]/12),12,sp[1],sp[2],sp[3]))
       flux_clr = np.zeros((np.int(sp[0]/12),12,sp[1],sp[2],sp[3]))
       for m in range(0,12):
           
           #Conduct calculations by month, using m index to isolate data accordingly
           #Create climatology by average all timesteps in the var_base variable
           var_base_m_tmean = np.squeeze(np.nanmean(var_base_re[:,m,:,:,:],axis=0))
           var_pert_m = np.squeeze(var_pert_re[:,m,:,:,:])
           
           #Compute anomalies
           var_anom = var_pert_m - np.repeat(var_base_m_tmean[np.newaxis,:,:,:],np.int(sp[0]/12),axis=0)

           #Calculate flux anomaly for all levels except first level above surface - total-sky, troposphere
           flux_tot[:,m,1:,:,:] = np.squeeze(np.repeat(tot_kern[np.newaxis,m,1:,:,:],np.int(sp[0]/12),axis=0)) *\
                                        np.squeeze(np.repeat(np.repeat(np.repeat(\
                                        dp[np.newaxis,1:],np.int(sp[0]/12),axis=0)[:,:,np.newaxis],sp[2],axis=2)[:,:,:,np.newaxis],sp[3],axis=3))\
                                        *var_anom[:,1:,:,:]/100
           #Calculate flux anomaly for level above surface
           flux_tot[:,m,0,:,:] = np.squeeze(np.repeat(tot_kern[np.newaxis,m,0,:,:],np.int(sp[0]/12),axis=0))\
                                       *np.squeeze(dpsfc[:,m,:,:])*var_anom[:,0,:,:]/100

           #Calculate flux anomaly for all levels except first level above surface - clear-sky, troposphere
           flux_clr[:,m,1:,:,:] = np.squeeze(np.repeat(clr_kern[np.newaxis,m,1:,:,:],np.int(sp[0]/12),axis=0)) *\
                                        np.squeeze(np.repeat(np.repeat(np.repeat(\
                                        dp[np.newaxis,1:],np.int(sp[0]/12),axis=0)[:,:,np.newaxis],sp[2],axis=2)[:,:,:,np.newaxis],sp[3],axis=3))\
                                        *var_anom[:,1:,:,:]/100
           #Calculate flux anomaly for level above surface
           flux_clr[:,m,0,:,:] = np.squeeze(np.repeat(clr_kern[np.newaxis,m,0,:,:],np.int(sp[0]/12),axis=0))\
                                       *np.squeeze(dpsfc[:,m,:,:])*var_anom[:,0,:,:]/100

    #Reshape fluxanom variables and vertically integrate
    flux_tot = np.reshape(np.squeeze(np.nansum(flux_tot,axis=2)),(sp[0],sp[2],sp[3]))
    flux_clr = np.reshape(np.squeeze(np.nansum(flux_clr,axis=2)),(sp[0],sp[2],sp[3]))
   
    return flux_tot, flux_clr


# ======================================================================
#fluxanom_calc_3D
#  computes anomalies of radiatively-relevant 3D climate variable and multiplies
#  by radiative kernel to convert to radiative flux change. Clear- and all-sky calculations
#  Note var_*_clr not always used. Specifically an option for clear-sky albedo calculations

def fluxanom_calc_3D(var_pert_tot, var_base_tot, tot_kern, clr_kern, var_pert_clr=None, var_base_clr=None):

    sp = var_pert_tot.shape
    sb = var_base_tot.shape
    skt = tot_kern.shape
    skc = clr_kern.shape

    flux_sfc_tot = np.zeros((np.int(sp[0]/12),12,sp[1],sp[2]))
    flux_sfc_clr = np.zeros((np.int(sp[0]/12),12,sp[1],sp[2]))
    if len(skt)!=3 or len(skc)!=3 or len(sp)!=3 or len(sb)!=3:
       print("An input variable is not 3D! Function will not execute")
    else:

       #Prep variable to analyze on a monthly-basis
       var_pert_tot_re = np.reshape(var_pert_tot, (np.int(sp[0]/12),12,sp[1],sp[2]))
       var_base_tot_re = np.reshape(var_base_tot, (np.int(sb[0]/12),12,sb[1],sb[2]))
     
       if var_pert_clr is not None:
          var_pert_clr_re = np.reshape(var_pert_clr, (np.int(sp[0]/12),12,sp[1],sp[2]))
       if var_base_clr is not None:
          var_base_clr_re = np.reshape(var_base_clr, (np.int(sb[0]/12),12,sb[1],sb[2]))

       for m in range(0,12):

           #Conduct calculations by month, using m index to isolate data accordingly
           #Create climatology by average all timesteps in the var_base variable
           var_base_tot_m_tmean = np.squeeze(np.nanmean(var_base_tot_re[:,m,:,:],axis=0))
           var_pert_tot_m = np.squeeze(var_pert_tot_re[:,m,:,:])

           if var_base_clr is not None:
              var_base_clr_m_tmean = np.squeeze(np.mean(var_base_clr_re[:,m,:,:],axis=0)) 
              var_pert_clr_m = np.squeeze(var_pert_clr_re[:,m,:,:])

           #Compute anomalies
           var_tot_anom = var_pert_tot_m - np.repeat(var_base_tot_m_tmean[np.newaxis,:,:],np.int(sp[0]/12),axis=0)

           if var_base_clr is not None:
              var_clr_anom = var_pert_clr_m - np.repeat(var_base_clr_m_tmean[np.newaxis,:,:],np.int(sp[0]/12),axis=0)

           #Compute flux anomaly - total-sky
           flux_sfc_tot[:,m,:,:] = np.squeeze(np.repeat(tot_kern[np.newaxis,m,:,:],np.int(sp[0]/12),axis=0)) * var_tot_anom

           #Compute flux anomaly - clear-sky
           if var_base_clr is not None:
              flux_sfc_clr[:,m,:,:] = np.squeeze(np.repeat(clr_kern[np.newaxis,m,:,:],np.int(sp[0]/12),axis=0)) * var_clr_anom
           else:
              flux_sfc_clr[:,m,:,:] = np.squeeze(np.repeat(clr_kern[np.newaxis,m,:,:],np.int(sp[0]/12),axis=0)) * var_tot_anom
    
    #Reshape flux anomalies
    flux_sfc_tot = np.reshape(flux_sfc_tot,(sp[0],sp[1],sp[2]))
    flux_sfc_clr = np.reshape(flux_sfc_clr,(sp[0],sp[1],sp[2]))
          
    return flux_sfc_tot, flux_sfc_clr

# ======================================================================
# esat_coef
#
#Computes the saturation vapor pressure coefficient necessary for water vapor radiative flux calculations
def esat_coef(temp):
    tc = temp - 273
    aw = np.array([6.11583699, 0.444606896, 0.143177157e-01,
                 0.264224321e-03, 0.299291081e-05, 0.203154182e-07,
                 0.702620698e-10, 0.379534310e-13, -0.321582393e-15])
    ai = np.array([6.11239921, 0.443987641, 0.142986287e-01,
                 0.264847430e-03, 0.302950461e-05, 0.206739458e-07,
                 0.640689451e-10, -0.952447341e-13, -0.976195544e-15])
    esat_water = aw[0]
    esat_ice = ai[0]

    for z in range(1, 9):
        esat_water = esat_water + aw[z]*(tc**(z))
        esat_ice = esat_ice + ai[z]*(tc**(z))


    esat = esat_ice
    b = np.where(tc > 0)
    esat[b] = esat_water[b]

    return esat


# ======================================================================
# latlonr3_3D4D
#
# Reformats, reorders and regrids lat,lon so model data matches kernel data grid
def latlonr3_3D4D(variable, lat_start, lon_start, lat_end, lon_end,kern):

    #Check of start and end lat is in similar order. If not, flip.
    if ((lat_start[0]>lat_start[-1]) and (lat_end[0]<lat_end[-1])) or \
       ((lat_start[0]<lat_start[-1]) and (lat_end[0]>lat_end[-1])):

       lat_start = np.flipud(lat_start)
       variable = variable[...,::-1,:]

    #Check if start and end lon both are 0-360 or both -180-180.  If not, make them the same
    if ((np.max(lon_start)>=300) and (np.max(lon_end)>100 and np.max(lon_end)<300)):

         lon1 = np.mod((lon_start+180),360)-180

         lon1a = lon1[0:len(lon1)/2]
         lon1b = lon1[len(lon1)/2:]
         start1a = variable[...,0:len(lon1)/2]
         start1b = variable[...,len(lon1)/2:]
         lon_start = np.concatenate((lon1b,lon1a))
         variable = np.concatenate((start1b,start1a),axis=-1)
    elif ((np.max(lon_start)>100 and np.max(lon_start)<300) and (np.max(lon_end)>=300)):
         lon1 = np.mod(lon_start,360)

         lon1a = lon1[0:len(lon1)/2]
         lon1b = lon1[len(lon1)/2:]
         start1a = variable[...,0:len(lon1)/2]
         start1b = variable[...,len(lon1)/2:]
         lon_start = np.concatenate((lon1b,lon1a))
         variable = np.concatenate((start1b,start1a),axis=-1)

    #If, after above change (or after skipping that step), start and lat are in different order, flip.
    if ((lon_start[0]>lon_start[-1]) and (lon_end[0]<lon_end[-1])) or \
       ((lon_start[0]<lon_start[-1]) and (lon_end[0]>lon_end[-1])):

       lon_start = np.flipud(lon_start)
       variable = variable[...,::-1]

    #Now that latitudes and longitudes have similar order and format, regrid.
    Y_start, X_start = np.meshgrid(lat_start,lon_start)
    Y_kern, X_kern = np.meshgrid(lat_end,lon_end)

    if len(variable.shape) == 3: #For 3D data
         shp_start = variable.shape
         shp_kern = kern.shape
         variable_new = np.empty((shp_start[0],shp_kern[1],shp_kern[2]))*np.nan
         for kk in range(shp_start[0]):
             variable_new[kk,:,:] = griddata((Y_start.flatten(), \
             X_start.flatten()),np.squeeze(variable[kk,:,:]).T.flatten(), \
             (Y_kern.flatten(),X_kern.flatten()),fill_value=np.nan).reshape(shp_kern[2],shp_kern[1]).T
    elif len(variable.shape) == 4: #For 4D data
         shp_start = variable.shape
         shp_kern = kern.shape
         variable_new = np.empty((shp_start[0],shp_start[1],shp_kern[2],shp_kern[3]))*np.nan
         for ll in range(shp_start[1]):
             for kk in range(shp_start[0]):
                 #print(ll)
                 #print(kk)
                 #print(np.squeeze(variable[kk,ll,:,:]).T.flatten())
                 variable_new[kk,ll,:,:] = griddata((Y_start.flatten(), \
                 X_start.flatten()),np.squeeze(variable[kk,ll,:,:]).T.flatten(), \
                 (Y_kern.flatten(),X_kern.flatten()),fill_value=np.nan).reshape(shp_kern[3],shp_kern[2]).T
                 
         shp_start = None
         shp_kern = None

    return variable_new

# ======================================================================
# globemean_3D
#
# Compute cosine weighted global-mean
def globemean_3D(var,w):
    var_mask = ma.masked_array(var,~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask,axis=2),axis=1,weights=w))

    return var_mean

# ======================================================================
# fluxanom_nc_create
#
# Saves 2D feedbacks or forcing

def fluxanom_nc_create(variable,lat,lon,fbname):

    var = xr.DataArray(variable,coords=[lat,lon],dims=['lat','lon'],name=fbname)
    var.to_netcdf(os.environ['WK_DIR']+'/model/fluxanom2D_'+fbname+'.nc')

    return None

# ======================================================================
# feedback_regress
#
# Regeresses radiative flux anomalies with global-mean dTs to compute 2D feedback
def feedback_regress(fluxanom,tspert,tsclimo,lat,lon,fbname):

    sp = tspert.shape
    sc = tsclimo.shape

    tsclimo_re = np.squeeze(np.nanmean(np.reshape(tsclimo, \
                (np.int(sc[0]/12),12,sc[1],sc[2])),axis=0))

    tsanom = tspert - np.reshape(np.repeat(tsclimo_re[np.newaxis,...],np.int(sp[0]/12), \
               axis=0),(sp[0],sp[1],sp[2]))
    
    weights = np.repeat(np.cos(np.deg2rad(lat))[np.newaxis,:],sp[0],axis=0)
    tsanom_globemean = globemean_3D(tsanom,weights)
    tsanom_re = np.repeat(np.repeat(tsanom_globemean[:,np.newaxis], \
                          sp[1],axis=1)[...,np.newaxis],sp[2],axis=2)
    
    tsanom_re_timemean = np.nanmean(tsanom_re,axis=0)
    tsanom_re_std = np.nanstd(tsanom_re,axis=0)
    fluxanom_timemean = np.nanmean(fluxanom,axis=0)
    fluxanom_std = np.nanstd(fluxanom,axis=0)

    n=np.sum(~np.isnan(tsanom_re),axis=0)
    cov = np.nansum((tsanom_re-tsanom_re_timemean)*\
             (fluxanom-fluxanom_timemean),axis=0)/n
    slopes = cov/(tsanom_re_std**2)

    fluxanom_nc_create(slopes,lat,lon,fbname)

    return slopes

