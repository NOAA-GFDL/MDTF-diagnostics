#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This file is part of the Surface Albedo Feedback Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
#   Last update: 1/25/2021
# 
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point of contact Aaron Donohoe, U. Washington adonohoe@u.washington.edu
#   - Other contributors Ed Blanchardd, Lettie Roach, Wei Cheng
# 
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
# 
#   Functionality
# 
#   Code to input many years of monthly TOA and Surface shortwave radiative fluxes
#     and compute spatial maps of the surface albedo kernel from an isotropic model 
#     and surface albedo 
# 
#   Required programming language and libraries
# 
#      Python3 
# 
#   Required model output variables
# 
#      TOA and Surface shortwave radiative fluxes and surface temperature
#      ideally for 1996-2014 and 50 yrs of piControl and abrupt-4XCO2
# 
#   References
# 
#      Donohoe, A., E. Blanchard-Wrigglesworth, A. Schweiger, and P.J. Rasch, 2020:
#          The Effect of Atmospheric Transmissivity on Model and Observational Estimates 
#          of the Sea Ice Albedo Feedback, J. Climate, https://doi.org/10.1175/JCLI-D-19-0674.1
#

#from __future__ import print_function
import os

# undo these for the framework version
import matplotlib
matplotlib.use('Agg') # non-X windows backend

# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
import xesmf as xe
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import surface_albedo_feedback_calcs


podname='surface_albedo_feedback'

surface_albedo_feedback_calcs.process_data()

wk_dir="{WK_DIR}".format(**os.environ)
model="{model}".format(**os.environ)
modelname = "{model}".format(**os.environ)
# these yrs only refer to the hist period for comparing kernel of mod to CERES
# this pod also uses piControl and 4XCO2 output, the years will differ with model
firstyr = "{FIRSTYR}".format(**os.environ)
lastyr = "{LASTYR}".format(**os.environ)

obsdir="{OBS_DATA}/".format(**os.environ)
output_dir = wk_dir+'/model/'
figures_dir = wk_dir+'/model/'


# In[4]:


### model and obs data files and varnames: ###############################################

# procesed output file names
kernel_obs_file = obsdir+'CERES40_surface_albedo_kernel_2000-2018_MJJA.nc'
sensitivity_obs_file = obsdir+'CERES40_ice_sensitivity_MJJA.nc'
kernel_histmod_file=output_dir+'surface_albedo_kernel_'+firstyr+'-'+lastyr+'.nc'
kernel_pimod_file=output_dir+'surface_albedo_kernel_piControl.nc'
albedo_abmod_file=output_dir+'surface_albedo_abrupt-4xCO2.nc'


# In[5]:


obs = xr.open_dataset(kernel_obs_file)
obskernel = obs.kernel
obsalbedo = obs.albedo

obs = xr.open_dataset(sensitivity_obs_file)
obssensitivity=100.*obs.OBS_ice_sensitivity  # convert to percent per K

mod = xr.open_dataset(kernel_histmod_file)
histmodkernel = mod.kernel
histmodalbedo = mod.albedo

# regrid model data to obs grid
method = 'nearest_s2d'       #method = 'nearest_d2s'  # this was bad do not use
regridder = xe.Regridder(mod, obs, method, periodic=False, reuse_weights=False)
modregrid=regridder(mod)

histmodregridkernel = modregrid.kernel
histmodregridalbedo = modregrid.albedo

mod = xr.open_dataset(albedo_abmod_file)
abmodTglob = mod.Tglob
abmodalbedo = mod.albedo

mod = xr.open_dataset(kernel_pimod_file)
pimodTglob = mod.Tglob
pimodalbedo = mod.albedo
pimodkernel = mod.kernel

mod=None
obs=None
modregrid=None


# In[1]:


# info about the 3 panel figs
figsize=(12,4.5)
leftcbarposition=[0.18, 0.15, 0.4, 0.04] #[left, bottom, width, height]
rightcbarposition=[0.69, 0.15, 0.18, 0.04]

# info about the 2 panel figs
figsize2=(9,4.5)
cbarposition=[0.31, 0.15, 0.4, 0.04]

def pltpanel(field,title=None,subs=(1,3,1),cmap_c='plasma'):
    ax = plt.subplot(subs,projection = ccrs.NorthPolarStereo())
    ax.add_feature(cfeature.COASTLINE,zorder=100,edgecolor='k')
    ax.set_extent([0.005, 360, 50, 90], crs=ccrs.PlateCarree())
    pl = field.plot(x='lon', y='lat', transform=ccrs.PlateCarree(),cmap=cmap_c,add_colorbar=False)
    ax.set_title(title,fontsize=14)
    return pl


# In[7]:


fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo Kernel from Isotropic Model MJJA', fontsize=18)

cmap_c = 'plasma'
pl=pltpanel(histmodkernel.sel(month=slice(4,7)).mean(dim='month'),modelname+' 1996-2014',subs=131,cmap_c = cmap_c)
pl.set_clim([0,3.1])
pl=pltpanel(obskernel.sel(month=slice(4,7)).mean(dim='month'),'CERES EBAF 2000-2018',subs=132,cmap_c = cmap_c)
pl.set_clim([0,3.1])

cbar_ax = fig.add_axes(leftcbarposition) 
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = histmodregridkernel-obskernel
df=pltpanel(diff.sel(month=slice(4,7)).mean(dim='month'),'Difference',subs=133,cmap_c = cmap_c)
df.set_clim([-1,1])

cbar_ax = fig.add_axes(rightcbarposition) 
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'historical_albedo_kernel_'+modelname+'.png', format='png',dpi=300)


# In[8]:


fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo Kernel from Isotropic Model MJJA', fontsize=18)

cmap_c = 'plasma'
pl = pltpanel(histmodkernel.sel(month=slice(4,7)).mean(dim='month'),modelname+' 1996-2014',subs=131,cmap_c = cmap_c)
pl.set_clim([0,3.1])
pl = pltpanel(pimodkernel.sel(month=slice(4,7)).mean(dim='month'),modelname+' piControl',subs=132,cmap_c = cmap_c)
pl.set_clim([0,3.1])

cbar_ax = fig.add_axes(leftcbarposition)
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = histmodkernel-pimodkernel
df = pltpanel(diff.sel(month=slice(4,7)).mean(dim='month'),'Difference',subs=133,cmap_c = cmap_c)

cbar_ax = fig.add_axes(rightcbarposition)
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'piControl_and_historical_albedo_kernel_'+modelname+'.png', format='png',dpi=300)


# In[9]:


fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo MJJA', fontsize=18)

cmap_c = 'PuBu_r'
pl = pltpanel(100.*abmodalbedo.sel(month=slice(4,7)).mean(dim='month'),modelname+' abrupt-4xCO2',subs=131,cmap_c = cmap_c)
pl.set_clim([5,85])
pl = pltpanel(100.*pimodalbedo.sel(month=slice(4,7)).mean(dim='month'),modelname+' piControl',subs=132,cmap_c = cmap_c)
pl.set_clim([5,85])

cbar_ax = fig.add_axes(leftcbarposition)
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = (abmodalbedo-pimodalbedo)
df = pltpanel(100.*diff.sel(month=slice(4,7)).mean(dim='month'),'Difference', subs=133,cmap_c = cmap_c)
df.set_clim([-50,50])

cbar_ax = fig.add_axes(rightcbarposition) 
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'piControl_and_abrupt4xCO2_albedo_'+modelname+'.png', format='png',dpi=300)


# In[10]:


# ice sensitivity
fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo MJJA', fontsize=18)

cmap_c = 'PuBu_r'
pl = pltpanel(100.*obsalbedo.sel(month=slice(4,7)).mean(dim='month'),'Observed 2000-2018',subs=131,cmap_c = cmap_c)
pl.set_clim([5,85])
pl = pltpanel(100.*histmodalbedo.sel(month=slice(4,7)).mean(dim='month'),modelname+' 1996-2014',subs=132,cmap_c = cmap_c)
pl.set_clim([5,85])

cbar_ax = fig.add_axes(leftcbarposition)
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = (histmodregridalbedo-obsalbedo)*100.
df = pltpanel(diff.sel(month=slice(4,7)).mean(dim='month'),'Difference',subs=133,cmap_c = cmap_c)
df.set_clim([-30,30])

cbar_ax = fig.add_axes(rightcbarposition)
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'historical_surface_albedo_'+modelname+'.png', format='png',dpi=300)


# In[11]:


# ice sensitivity
fig = plt.figure(figsize=figsize2)

fig.suptitle('Ice Sensitivity MJJA', fontsize=18)

cmap_c = 'PiYG'
df = pltpanel(obssensitivity,'Observed',subs=121,cmap_c = cmap_c)
df.set_clim([-15,15])

warming=(abmodTglob-pimodTglob) 
modelsensitivity = (abmodalbedo-pimodalbedo)*100./warming
df = pltpanel(modelsensitivity.sel(month=slice(4,7)).mean(dim='month'),modelname,subs=122,cmap_c = cmap_c)
df.set_clim([-15,15])

cbar_ax = fig.add_axes(cbarposition) #[left, bottom, width, height]
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo Change (%) per K', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'Ice_Sensitivity_'+modelname+'.png', format='png',dpi=300)


# In[12]:


# Surface Albedo Feedback
fig = plt.figure(figsize=figsize2)

fig.suptitle('Surface Albedo Feedback MJJA', fontsize=18)

cmap_c = 'PiYG'

# this data is not available yet
fb = obskernel.sel(month=slice(4,7)).mean(dim='month')*obssensitivity
df = pltpanel(fb, 'Observed', subs=121,cmap_c = cmap_c)
df.set_clim([-30,30])

fb = pimodkernel.sel(month=slice(4,7)).mean(dim='month')*modelsensitivity.sel(month=slice(4,7)).mean(dim='month')
df = pltpanel(fb, modelname, subs=122,cmap_c = cmap_c)
df.set_clim([-30,30])


cbar_ax = fig.add_axes(cbarposition)
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Ice Sensitivity (W m$^{-2}$ per K)', fontsize=14)

plt.subplots_adjust(bottom=0.21,top=0.85)

plt.savefig(figures_dir+'Surface_albedo_FB_'+modelname+'.png', format='png',dpi=300)


