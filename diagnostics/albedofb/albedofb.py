#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This file is part of the Surface Albedo Feedback Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
#   Last update: 9/8/2022
# 
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point of contact Aaron Donohoe, U. Washington adonohoe@uw.edu
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
#      ideally for 1996-2014
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
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import albedofb_calcs

# In[3]:

podname = 'albedofb'

# these yrs only refer to the hist period for comparing kernel of mod to CERES
firstyr = "{STARTDATE}".format(**os.environ)
lastyr = "{ENDDATE}".format(**os.environ)

wk_dir = "{WORK_DIR}".format(**os.environ)
obs_dir = "{OBS_DATA}/".format(**os.environ)
output_dir = wk_dir+'/model/'
figures_dir = wk_dir+'/model/'
modelname = "{CASENAME}".format(**os.environ)


# In[4]:


# model and obs data files and varnames: ###############################################

# obs processed files, provided
kernel_obs_file = obs_dir+'CERES40_surface_albedo_kernel_2000-2018_MJJA.nc' 
sensitivity_obs_file = obs_dir+'CERES40_surface_sensitivity_MJJA.nc'

# model output file names, to compute next
kernel_histmod_file = output_dir+'surface_albedo_kernel_'+firstyr+'-'+lastyr+'.nc'
sensitivity_histmod_file = output_dir+'surface_albedo_sensitivity_'+firstyr+'-'+lastyr+'.nc'


# In[5]:


# the albedo feedback modeling is done here, used same code to process CERES40 that is provided 
albedofb_calcs.process_data(kernel_histmod_file, sensitivity_histmod_file)


# In[6]:


# read in kernel and albedo
obs_dataset = xr.open_dataset(kernel_obs_file)
obskernel = obs_dataset.kernel
obsalbedo = obs_dataset.albedo

mod_dataset = xr.open_dataset(kernel_histmod_file)
histmodkernel = mod_dataset.kernel
histmodalbedo = mod_dataset.albedo

# set up regrid model to obs grid
method = 'nearest_s2d'
regridder = xe.Regridder(mod_dataset, obs_dataset, method, periodic=False, reuse_weights=False)

modregrid = regridder(mod_dataset)                      # regrid model to obs grid
histmodregridkernel = modregrid.kernel
histmodregridalbedo = modregrid.albedo

# read in sensitivity, which is albedo trend per global mean temperature trend 
obs_dataset2 = xr.open_dataset(sensitivity_obs_file)
obssensitivity = 100.*obs_dataset2.OBS_ice_sensitivity   # convert to percent per K

mod_dataset2 = xr.open_dataset(sensitivity_histmod_file)
modregrid2 = regridder(mod_dataset2)                     # regrid model to obs grid
histmodregridsensitivity = 100.*modregrid2.sensitivity   # convert to percent per K


# In[7]:


# info about the 3 panel figs
figsize = (12, 4.5)
leftcbarposition = [0.18, 0.15, 0.4, 0.04]  # [left, bottom, width, height]
rightcbarposition = [0.69, 0.15, 0.18, 0.04]

# info about the 2 panel figs
figsize2 = (9, 4.5)
cbarposition = [0.31, 0.15, 0.4, 0.04]


def pltpanel(field, title=None, subs=(1, 3, 1), cmap_c='plasma'):
    ax = plt.subplot(subs, projection=ccrs.NorthPolarStereo())
    ax.add_feature(cfeature.COASTLINE, zorder=100, edgecolor='k')
    ax.set_extent([0.005, 360, 50, 90], crs=ccrs.PlateCarree())
    pl = field.plot(x='lon', y='lat', transform=ccrs.PlateCarree(), cmap=cmap_c, add_colorbar=False)
    ax.set_title(title, fontsize=14)
    return pl


# In[8]:


# surface albedo kernel
fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo Kernel from Isotropic Model MJJA', fontsize=18)

cmap_c = 'plasma'
pl = pltpanel(histmodkernel.sel(month=slice(4, 7)).mean(dim='month'), modelname +' 1996-2014',subs=131,cmap_c = cmap_c)
pl.set_clim([0, 3.1])
pl = pltpanel(obskernel.sel(month=slice(4, 7)).mean(dim='month'),'CERES EBAF 2000-2018',subs=132,cmap_c = cmap_c)
pl.set_clim([0, 3.1])

cbar_ax = fig.add_axes(leftcbarposition) 
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = histmodregridkernel-obskernel
df = pltpanel(diff.sel(month=slice(4, 7)).mean(dim='month'), 'Difference', subs=133, cmap_c=cmap_c)
df.set_clim([-1, 1])

cbar_ax = fig.add_axes(rightcbarposition) 
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Radiative Sensitivity (W m$^{-2}$ per 1%)', fontsize=14)

plt.subplots_adjust(bottom=0.21, top=0.85)

plt.savefig(figures_dir+'historical_albedo_kernel_'+modelname+'.png', format='png', dpi=300)


# In[9]:


# surface albedo
fig = plt.figure(figsize=figsize)

fig.suptitle('Surface Albedo MJJA', fontsize=18)

cmap_c = 'PuBu_r'
pl = pltpanel(100.*obsalbedo.sel(month=slice(4, 7)).mean(dim='month'), 'Observed 2000-2018', subs=131, cmap_c=cmap_c)
pl.set_clim([5, 85])
pl = pltpanel(100.*histmodalbedo.sel(month=slice(4, 7)).mean(dim='month'),
              modelname + ' ' + firstyr + '-' + lastyr, subs=132, cmap_c=cmap_c)
pl.set_clim([5, 85])

cbar_ax = fig.add_axes(leftcbarposition)
cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

# their difference
cmap_c = 'PiYG'
diff = (histmodregridalbedo-obsalbedo)*100.
df = pltpanel(diff.sel(month=slice(4, 7)).mean(dim='month'), 'Difference', subs=133,cmap_c=cmap_c)
df.set_clim([-30, 30])

cbar_ax = fig.add_axes(rightcbarposition)
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo (%)', fontsize=14)

plt.subplots_adjust(bottom=0.21, top=0.85)

plt.savefig(figures_dir+'historical_surface_albedo_'+modelname+'.png', format='png',dpi=300)


# In[10]:


# Albedo sensitivity
fig = plt.figure(figsize=figsize2)

fig.suptitle('Albedo Sensitivity MJJA', fontsize=18)

cmap_c = 'PiYG'
df = pltpanel(obssensitivity, 'Observed 2000-2018', subs=121, cmap_c=cmap_c)
df.set_clim([-15, 15])

df = pltpanel(histmodregridsensitivity.sel(month=slice(4, 7)).mean(dim='month'), modelname + ' '
              + firstyr + '-' + lastyr, subs=122, cmap_c=cmap_c)
df.set_clim([-15, 15])

cbar_ax = fig.add_axes(cbarposition)  # [left, bottom, width, height]
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo Change (%) per K', fontsize=14)

plt.subplots_adjust(bottom=0.21, top=0.85)

plt.savefig(figures_dir+'historical_albedo_sensitivity_'+modelname+'.png', format='png',dpi=300)


# In[11]:


# Surface Albedo Feedback
fig = plt.figure(figsize=figsize2)

fig.suptitle('Surface Albedo Feedback MJJA', fontsize=18)

cmap_c = 'PiYG'

fb = obskernel.sel(month=slice(4, 7)).mean(dim='month')*obssensitivity
df = pltpanel(fb, 'Observed 2000-2018', subs=121, cmap_c=cmap_c)
df.set_clim([-30, 30])

fb = histmodregridkernel.sel(month=slice(4, 7)).mean(dim='month')*histmodregridsensitivity.sel(month=slice(4, 7)).mean(dim='month')
df = pltpanel(fb, modelname + '' + firstyr + '' + lastyr, subs=122, cmap_c=cmap_c)
df.set_clim([-30, 30])


cbar_ax = fig.add_axes(cbarposition)
cbar = fig.colorbar(df, cax=cbar_ax,  orientation='horizontal')
cbar.set_label('Albedo Sensitivity (W m$^{-2}$ per K)', fontsize=14)

plt.subplots_adjust(bottom=0.21, top=0.85)

plt.savefig(figures_dir+'historical_surface_albedo_FB_'+modelname+'.png', format='png',dpi=300)


# In[12]:


# remove the file pointers 
del mod_dataset
del obs_dataset
del mod_dataset2
del obs_dataset2


