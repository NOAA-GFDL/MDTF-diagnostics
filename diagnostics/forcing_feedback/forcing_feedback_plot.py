# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcingfluxanom_plot_final.py
#
#  Called by forcingfluxanom_xr_final.py
#   Reads in observations and temporary model results of individual 2D feedbacks and IRF, produces maps of each and
#   a bar graph summarizing global-mean values
#
#  Forcing Feedback Diagnositic Package
#
#  This file is part of the Forcing and Feedback Diagnostic Package
#    and the MDTF code package. See LICENSE.txt for the license. 
#
#

import os
import sys
import numpy as np
import numpy.ma as ma
import xarray as xr
import cartopy as car
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as c
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
import cartopy.crs as ccrs

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
#from mpl_toolkits.basemap import Basemap, shiftgrid

def globemean_2D(var,w):
    var_mask = ma.masked_array(var,~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask,axis=1),weights=w))

    return var_mean

# Read in observational data
nc_obs = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
lat_obs = nc_obs.lat.values
lon_obs = nc_obs.lon.values
llons_obs, llats_obs = np.meshgrid(lon_obs,lat_obs)

#Read in model results

nc_pl = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_Planck.nc")
nc_lr = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_LapseRate.nc")
nc_lw_q = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_LW_WaterVapor.nc")
nc_sw_q = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_SW_WaterVapor.nc")
nc_alb = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_SfcAlbedo.nc")
nc_lw_c = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_LW_Cloud.nc")
nc_sw_c = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_SW_Cloud.nc")
nc_lw_irf = 12*xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_LW_IRF.nc")
nc_sw_irf = 12*xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_SW_IRF.nc")
nc_lw_netrad = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_LW_Rad.nc")
nc_sw_netrad = xr.open_dataset(os.environ["WK_DIR"]+"/model/fluxanom2D_SW_Rad.nc")

#nc_pl = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_lr = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_lw_q = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_sw_q = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_alb = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_lw_c = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_sw_c = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_lw_irf = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_sw_irf = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_lw_netrad = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")
#nc_sw_netrad = xr.open_dataset(os.environ["OBS_DATA"]+"/forcing_feedback_obs.nc")

lat_model = nc_sw_irf.lat.values
weights_model = np.cos(np.deg2rad(lat_model))
weights_obs = np.cos(np.deg2rad(lat_obs))


#Global-mean barplot comparison
barWidth = 0.125
#Figure 1: Total Radiation
LW_RA_Model = globemean_2D(nc_lw_netrad.LW_Rad.values,weights_model)
SW_RA_Model = globemean_2D(nc_sw_netrad.SW_Rad.values,weights_model)
bars1 = [LW_RA_Model,SW_RA_Model]
LW_RA_Obs = globemean_2D(nc_obs.LW_Rad.values,weights_obs)
SW_RA_Obs = globemean_2D(nc_obs.SW_Rad.values,weights_obs)
bars2 = [LW_RA_Obs,SW_RA_Obs]
r1 = np.arange(len(bars1))
r2 = [x + barWidth for x in r1]
plt.bar(r1,bars1,color='blue',width=barWidth,edgecolor='white',label='Model')
plt.bar(r2,bars2,color='red',width=barWidth,edgecolor='white',label='Observations')
plt.axhline(0,color='black',lw=1)
plt.ylabel('W/$m^2$/K')
plt.xticks([r + barWidth for r in range(len(bars1))], ['LW Rad', 'SW Rad'])
plt.legend(loc = "upper left")
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_globemean_Rad.eps')
plt.close()

#Figure 3: IRF
LW_IRF_Model = globemean_2D(nc_lw_irf.LW_IRF.values,weights_model)
SW_IRF_Model = globemean_2D(nc_sw_irf.SW_IRF.values,weights_model)
bars1 = [LW_IRF_Model,SW_IRF_Model]
LW_IRF_Obs = globemean_2D(nc_obs.LW_IRF.values,weights_obs)
SW_IRF_Obs = globemean_2D(nc_obs.SW_IRF.values,weights_obs)
bars2 = [LW_IRF_Obs,SW_IRF_Obs]
#print(bars1)
#print(bars2)
#quit()
r1 = np.arange(len(bars1))
r2 = [x + barWidth for x in r1]
plt.bar(r1,bars1,color='blue',width=barWidth,edgecolor='white',label='Model')
plt.bar(r2,bars2,color='red',width=barWidth,edgecolor='white',label='Observations')
plt.axhline(0,color='black',lw=1)
plt.ylabel('W/$m^2$')
plt.xticks([r + barWidth for r in range(len(bars1))], ['LW IRF', 'SW IRF'])
plt.legend(loc = "upper left")
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_globemean_IRF.eps')
plt.close()

#Figure 3: Longwave Radiative Feedbacks
PL_Model = globemean_2D(nc_pl.Planck.values,weights_model)
LR_Model = globemean_2D(nc_lr.LapseRate.values,weights_model)
LWWV_Model = globemean_2D(nc_lw_q.LW_WaterVapor.values,weights_model)
LWC_Model = globemean_2D(nc_lw_c.LW_Cloud.values,weights_model)
bars1 = [PL_Model,LR_Model,LWWV_Model,LWC_Model]
PL_Obs = globemean_2D(nc_obs.Planck.values,weights_obs)
LR_Obs = globemean_2D(nc_obs.LapseRate.values,weights_obs)
LWWV_Obs = globemean_2D(nc_obs.LW_WaterVapor.values,weights_obs)
LWC_Obs = globemean_2D(nc_obs.LW_Cloud.values,weights_obs)
bars2 = [PL_Obs,LR_Obs,LWWV_Obs,LWC_Obs]
r1 = np.arange(len(bars1))
r2 = [x + barWidth for x in r1]
plt.bar(r1,bars1,color='blue',width=barWidth,edgecolor='white',label='Model')
plt.bar(r2,bars2,color='red',width=barWidth,edgecolor='white',label='Observations')
plt.axhline(0,color='black',lw=1)
plt.ylabel('W/$m^2$/K')
plt.xticks([r + barWidth for r in range(len(bars1))], ['Planck', 'Lapse Rate', 'LW Water Vapor',' LW Cloud'])
plt.legend(loc = "upper left")
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_globemean_LWFB.eps')
plt.close()

#Figure 4: Shortwave Radiative Feedbacks
Alb_Model = globemean_2D(nc_alb.SfcAlbedo.values,weights_model)
SWWV_Model = globemean_2D(nc_sw_q.SW_WaterVapor.values,weights_model)
SWC_Model = globemean_2D(nc_sw_c.SW_Cloud.values,weights_model)
bars1 = [Alb_Model,SWWV_Model,SWC_Model]
Alb_Obs = globemean_2D(nc_obs.SfcAlbedo.values,weights_obs)
SWWV_Obs = globemean_2D(nc_obs.SW_WaterVapor.values,weights_obs)
SWC_Obs = globemean_2D(nc_obs.SW_Cloud.values,weights_obs)
bars2 = [Alb_Obs,SWWV_Obs,SWC_Obs]
r1 = np.arange(len(bars1))
r2 = [x + barWidth for x in r1]
plt.bar(r1,bars1,color='blue',width=barWidth,edgecolor='white',label='Model')
plt.bar(r2,bars2,color='red',width=barWidth,edgecolor='white',label='Observations')
plt.axhline(0,color='black',lw=1)
plt.ylabel('W/$m^2$/K')
plt.xticks([r + barWidth for r in range(len(bars1))], ['Sfc. Albedo', 'SW Water Vapor',' SW Cloud'])
plt.legend(loc = "upper left")
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_globemean_SWFB.eps')
plt.close()


if ((np.max(nc_sw_irf.lon.values)>=300)):   #convert 0-360 lon to -180-180 lon for plotting
   lon1 = np.mod((nc_sw_irf.lon.values+180),360)-180
   lon1a = lon1[0:np.int(len(lon1)/2)]
   lon1b = lon1[np.int(len(lon1)/2):]
   lon_model = np.concatenate((lon1b,lon1a))
else:
   lon_model = nc_sw_irf.lon.values
llons_model, llats_model = np.meshgrid(lon_model,lat_model)


#Produce maps of the radiative feedbacks and IRF tends, comparing model results to observations

levels = np.arange(-6,6.0001,1)
#Temperature Feedback
fig,axs = plt.subplots(2, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0, 0].set_title('Planck - Model')
varhold = nc_pl.Planck.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0, 0].set_extent([-180,180,-80,80])
cs = axs[0, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[0,0].coastlines()
g1 = axs[0,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None


axs[0, 1].set_title('Planck - Obs.')
varhold = nc_obs.Planck.values
axs[0, 1].set_extent([-180,180,-80,80])
cs = axs[0, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[0,1].coastlines()
g1 = axs[0,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

axs[1, 0].set_title('Lapse Rate - Model')
varhold = nc_lr.LapseRate.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[1, 0].set_extent([-180,180,-80,80])
cs = axs[1, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[1,0].coastlines()
g1 = axs[1,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[1, 1].set_title('Lapse Rate - Obs.')
varhold = nc_obs.LapseRate.values
axs[1, 1].set_extent([-180,180,-80,80])
cs = axs[1, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[1,1].coastlines()
g1 = axs[1,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None


cbar = plt.colorbar(cs,ax=axs.flat,orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_Temperature.eps',bbox_inches='tight')
plt.close()

levels = np.arange(-6,6.0001,1)
#Water Vapor Feedback
fig,axs = plt.subplots(2, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0, 0].set_title('LW Water Vapor - Model')
varhold = nc_lw_q.LW_WaterVapor.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0, 0].set_extent([-180,180,-80,80])
cs = axs[0, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[0,0].coastlines()
g1 = axs[0,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None
cbar = plt.colorbar(cs,ax=axs[0,0],orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')

axs[0, 1].set_title('LW Water Vapor - Obs.')
varhold = nc_obs.LW_WaterVapor.values
axs[0, 1].set_extent([-180,180,-80,80])
cs = axs[0, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[0,1].coastlines()
g1 = axs[0,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None
cbar = plt.colorbar(cs,ax=axs[0,1],orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')

levels = np.arange(-1,1.0001,0.125)
axs[1, 0].set_title('SW Water Vapor - Model')
varhold = nc_sw_q.SW_WaterVapor.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[1, 0].set_extent([-180,180,-80,80])
cs = axs[1, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-1,vmax=1,levels=levels,extend='both')
axs[1,0].coastlines()
g1 = axs[1,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None
cbar = plt.colorbar(cs,ax=axs[1,0],orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')

axs[1, 1].set_title('SW Water Vapor - Obs.')
varhold = nc_obs.SW_WaterVapor.values
axs[1, 1].set_extent([-180,180,-80,80])
cs = axs[1, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-1,vmax=1,levels=levels,extend='both')
axs[1,1].coastlines()
g1 = axs[1,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None
cbar = plt.colorbar(cs,ax=axs[1,1],orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')

plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_WaterVapor.eps',bbox_inches='tight')
plt.close()


levels = np.arange(-6,6.0001,1)
#Surface Albedo Feedback
fig,axs = plt.subplots(1, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0].set_title('Sfc. Albedo - Model')
varhold = nc_alb.SfcAlbedo.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0].set_extent([-180,180,-80,80])
cs = axs[0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[0].coastlines()
g1 = axs[0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[1].set_title('Sfc. Albedo - Obs.')
varhold = nc_obs.SfcAlbedo.values
axs[1].set_extent([-180,180,-80,80])
cs = axs[1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-6,vmax=6,levels=levels,extend='both')
axs[1].coastlines()
g1 = axs[1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

cbar = plt.colorbar(cs,ax=axs.flat,orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_SfcAlbedo.eps',bbox_inches='tight')
plt.close()

levels = np.arange(-16,16.0001,2)
#Cloud Feedback
fig,axs = plt.subplots(2, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0, 0].set_title('LW Cloud - Model')
varhold = nc_lw_c.LW_Cloud.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-3160 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0, 0].set_extent([-180,180,-80,80])
cs = axs[0, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-16,vmax=16,levels=levels,extend='both')
axs[0,0].coastlines()
g1 = axs[0,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[0, 1].set_title('LW_Cloud - Obs.')
varhold = nc_obs.LW_Cloud.values
axs[0, 1].set_extent([-180,180,-80,80])
cs = axs[0, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-16,vmax=16,levels=levels,extend='both')
axs[0,1].coastlines()
g1 = axs[0,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

axs[1, 0].set_title('SW Cloud - Model')
varhold = nc_sw_c.SW_Cloud.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-3160 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[1, 0].set_extent([-180,180,-80,80])
cs = axs[1, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-16,vmax=16,levels=levels,extend='both')
axs[1,0].coastlines()
g1 = axs[1,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[1, 1].set_title('SW Cloud - Obs.')
varhold = nc_obs.SW_Cloud.values
axs[1, 1].set_extent([-180,180,-80,80])
cs = axs[1, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-16,vmax=16,levels=levels,extend='both')
axs[1,1].coastlines()
g1 = axs[1,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

cbar = plt.colorbar(cs,ax=axs.flat,orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_Cloud.eps',bbox_inches='tight')
plt.close()

levels = np.arange(-24,24.0001,4)
#Rad Feedback
fig,axs = plt.subplots(2, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0, 0].set_title('LW Total Rad. - Model')
varhold = nc_lw_netrad.LW_Rad.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-3240 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0, 0].set_extent([-180,180,-80,80])
cs = axs[0, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-24,vmax=24,levels=levels,extend='both')
axs[0,0].coastlines()
g1 = axs[0,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[0, 1].set_title('LW_Total Rad. - Obs.')
varhold = nc_obs.LW_Rad.values
axs[0, 1].set_extent([-180,180,-80,80])
cs = axs[0, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-24,vmax=24,levels=levels,extend='both')
axs[0,1].coastlines()
g1 = axs[0,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

axs[1, 0].set_title('SW Total Rad. - Model')
varhold = nc_sw_netrad.SW_Rad.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-3240 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[1, 0].set_extent([-180,180,-80,80])
cs = axs[1, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-24,vmax=24,levels=levels,extend='both')
axs[1,0].coastlines()
g1 = axs[1,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[1, 1].set_title('SW Total Rad. - Obs.')
varhold = nc_obs.SW_Rad.values
axs[1, 1].set_extent([-180,180,-80,80])
cs = axs[1, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-24,vmax=24,levels=levels,extend='both')
axs[1,1].coastlines()
g1 = axs[1,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

cbar = plt.colorbar(cs,ax=axs.flat,orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$/K')
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_Rad.eps',bbox_inches='tight')
plt.close()

levels = np.arange(-0.15,0.150001,0.015)
#IRF Feedback
fig,axs = plt.subplots(2, 2,subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0)))

axs[0, 0].set_title('LW IRF - Model')
varhold = nc_lw_irf.LW_IRF.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[0, 0].set_extent([-180,180,-80,80])
cs = axs[0, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-0.15,vmax=0.15,levels=levels,extend='both')
axs[0,0].coastlines()
g1 = axs[0,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[0, 1].set_title('LW_IRF - Obs.')
varhold = nc_obs.LW_IRF.values
axs[0, 1].set_extent([-180,180,-80,80])
cs = axs[0, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-0.15,vmax=0.15,levels=levels,extend='both')
axs[0,1].coastlines()
g1 = axs[0,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

axs[1, 0].set_title('SW IRF - Model')
varhold = nc_sw_irf.SW_IRF.values
if ((np.max(nc_sw_irf.lon.values)>=300)): #convert 0-360 lon to -180-180 lon for plotting
   start1a = varhold[...,0:np.int(len(lon1)/2)]
   start1b = varhold[...,np.int(len(lon1)/2):]
   varhold = np.concatenate((start1b,start1a),axis=1)
   start1a,start1b = None,None
axs[1, 0].set_extent([-180,180,-80,80])
cs = axs[1, 0].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-0.15,vmax=0.15,levels=levels,extend='both')
axs[1,0].coastlines()
g1 = axs[1,0].gridlines(linestyle=':')
g1.xlines = False
g1.ylabels_left = True
g1.ylocator = mticker.FixedLocator(np.arange(-60,61,30))
g1.yformatter = LATITUDE_FORMATTER
varhold = None

axs[1, 1].set_title('SW IRF - Obs.')
varhold = nc_obs.SW_IRF.values
axs[1, 1].set_extent([-180,180,-80,80])
cs = axs[1, 1].contourf(lon_model,lat_model,varhold,cmap=plt.cm.RdBu_r,transform=ccrs.PlateCarree(),vmin=-0.15,vmax=0.15,levels=levels,extend='both')
axs[1,1].coastlines()
g1 = axs[1,1].gridlines(linestyle=':')
g1.xlines = False
varhold = None

cbar = plt.colorbar(cs,ax=axs.flat,orientation='horizontal',aspect=25)
cbar.set_label('W/$m^2$')
plt.savefig(os.environ['WK_DIR']+'/model/PS/forcing_feedback_maps_IRF.eps',bbox_inches='tight')
plt.close()
