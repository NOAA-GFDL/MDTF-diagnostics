# In[1]:


# This file is part of the Sea Ice Suite Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
# 
#   Last update: 1/25/2021
# 
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point Lettie Roach and Cecilia Bitz
#   - Lettie Roach, University of Washington, lroach@uw.edu
# 
#   Open source copyright agreement
# 
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
# 
#   Functionality
# 
#   Code to input many years of monthly sea ice concentration and compute spatial maps of
#     monthly climatology, monthly standard deviation of all years
#     linear trend of each month for all years
#     monthly detrended standard deviation for all years
#     lagged correlation by month of monthly detrended data (hence also deseasonalized)
#       where lag is an arbitrary number of months
# 
#   Required programming language and libraries
# 
#      Python3 
# 
#   Required model output variables
# 
#      Sea ice concentration either as fraciton or percent 
#      it is assumed to be in the sea ice realm, and normally is named siconce
#      minor edits can alter to the settings.jsconc file can change these assumptions
# 
#   References
# 
#      Roach, L.R. and Co-authors, 2021: Process-oriented evaluation of Sea Ice 
#         and Mixed Layer Depth in MDTF Special Issue
#

#from __future__ import print_function
import os

# undo these for the framework version
import matplotlib
matplotlib.use('Agg') # non-X windows backend

print("********I am here")

# Commands to load third-party libraries. Any code you don't include that's 
# not part of your language's standard library should be listed in the 
# settings.jsonc file.
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
#from matplotlib import cm
import xesmf as xe
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
#import glob

# homegrown this code also imports pandas and scipy
from seaice_MLD_stats import (
    xr_reshape,
    _lrm,
    _lagcorr,
)

print("*******Now I am here")

# In[2]:


# this part will be done by the framework for us
os.environ['DATADIR']='/glade/work/bitz/mdtf/inputdata/model/SAM0-UNICON_r1i1p1f1_gn/'
os.environ['WK_DIR']='/glade/work/bitz/mdtf/wkdir/'

os.environ['CASENAME']='SAM0-UNICON_r1i1p1f1_gn'
os.environ['model']='SAM0-UNICON'
os.environ['conventions']='SAM0-UNICON'
os.environ['FIRSTYR']='1979'
os.environ['LASTYR']='2014'
os.environ['siconc_var']='siconc'


# In[3]:


def readindata(file, varname='siconc',firstyr='1979',lastyr='2014'):
    ds = xr.open_dataset(file)
    ds = ds.sel(time=slice(firstyr+'-01-01',lastyr+'-12-31')) # limit to yrs of interest, maybe model dep
    print('Limit domain to Arctic to match obs') # script would work fine if data were global
    ds = ds.where(ds.latitude>30.,drop=True) # limit to arctic for now, remove later
    field = ds[varname]
    field.name = varname

    if field.isel(time=0).max().values > 50.0:  # ensure we are [0,1] not [0,100]
        field=field*0.01

    ds.close()
    return field


# In[4]:


### 1) Loading model data files: ###############################################

input_file = "{DATADIR}/mon/{CASENAME}.{siconc_var}.mon.nc".format(**os.environ)
output_dir = "{WK_DIR}/{model}/seaice_suite/processed_data/".format(**os.environ)
figures_dir = "{WK_DIR}/{model}/seaice_suite/figures/".format(**os.environ)
obs_file = '/glade/work/bitz/mdtf/inputdata/obs_data/seaice_suite/HadISST_ice_1979-2016_grid_nh.nc'

proc_obs_file = '/glade/work/bitz/mdtf/inputdata/obs_data/seaice_suite/HadISST_stats_1979-2014.nc'

proc_mod_file=output_dir+'seaice_fullfield_stats.nc'

modelname = "{model}".format(**os.environ)
siconc_var = "{siconc_var}".format(**os.environ)
firstyr = "{FIRSTYR}".format(**os.environ)
lastyr = "{LASTYR}".format(**os.environ)

processmod= not(os.path.isfile(proc_mod_file)) # check if obs proc file exists
if processmod:
    field = readindata(input_file, 'siconc',firstyr,lastyr)

processobs= not(os.path.isfile(proc_obs_file)) # check if obs proc file exists
if processobs: # if no proc file then must get obs and process
    obs = readindata(obs_file, 'sic',firstyr,lastyr)


# In[5]:


def mainmonthlystats(field=None, firstyr=1979, lastyr=2014):
    """Compute mean, std, trend, std of detrended, residuals

    Parameters
    ----------
    field : xarray.DataArray, dims must be time, space (space can be multidim)
    
    Returns
    -------
    themean, thestd, trend, detrendedstd: xarray.DataArray, dims of month, space
    residuals: xarray.DataArray, dims of year, month, space
    """
    firstyr=int(firstyr)
    lastyr=int(lastyr)
    
    field=xr_reshape(field,'time',['year','month'],[np.arange(firstyr,lastyr+1),np.arange(12)])
    print('computing trend, this may take a few minutes')
    trend, intercept = xr.apply_ufunc(_lrm, field.year, field,
                           input_core_dims=[['year'], ['year']],
                           output_core_dims=[[],[]],
                           output_dtypes=[np.float, np.float],
                           vectorize=True)
                           #dask='parallelized')

    print('computing the rest')
    residuals = field - (field.year*trend+ intercept)

    themean = field.mean(dim='year')
    thestd = field.std(dim='year')
    detrendedstd = residuals.std(dim='year')
    
    themean.name='themean'
    thestd.name='thestd'
    trend.name='trend'
    detrendedstd.name='detrended_std'
    residuals.name='residuals'

    return themean, thestd, trend, detrendedstd, residuals


# In[6]:


def lagcorr(residuals,lag=1):
    """Pearson's correlation coefficient for lagged detrended field computed by month.
    .. math::
        a = residuals
        b = residuals shifted by lag 
        r_{ab} = \\frac{ \\sum_{i=i}^{n} (a_{i} - \\bar{a}) (b_{i} - \\bar{b}) }
                 {\\sqrt{ \\sum_{i=1}^{n} (a_{i} - \\bar{a})^{2} }
                  \\sqrt{ \\sum_{i=1}^{n} (b_{i} - \\bar{b})^{2} }}
    Parameters
    ----------
    residual : xarray.DataArray detrending by month, which also deseasonalizes

    Returns
    -------
    rlag : xarray.DataArray    Pearson's correlation coefficient at lag by month
    """

    rlag = xr.apply_ufunc(
        _lagcorr,
        residuals,
        input_core_dims=[['year','month']],
        kwargs={'lag': lag},
        output_core_dims=[['month']],
        output_dtypes=[np.float],
        vectorize=True)
        #dask='parallelized')

    rlag.name = 'lagcorr'
    rlag=rlag.transpose('month',...)
        
    return rlag


# In[7]:


def processandsave(field,file_out,firstyr=1979,lastyr=2014):
    ### 2) Doing computations on model or obs: #####################################
    # this takes about a few min on data that is already limited to the Arctic
    # recommend using DASK if you decide to compute global metrics
    # residuals are detrended field for each month, effectively making them detrended and deseasonalized
    themean, thestd, trend, detrendedstd, residuals = mainmonthlystats(field,firstyr,lastyr)
    print('main stats done')
    onemolagcorr=lagcorr(residuals,1) 
    oneyrlagcorr=lagcorr(residuals,12)
    onemolagcorr.name='onemolagcorr'
    oneyrlagcorr.name='oneyrlagcorr'

    ### 3) Saving output data: #####################################################

    allstats=xr.merge([themean, thestd, trend, detrendedstd, onemolagcorr, oneyrlagcorr])

    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    allstats.coords['monthabbrev'] = xr.DataArray(months, dims='month')
    allstats

    allstats.to_netcdf(file_out)


# In[8]:


if processmod:
    processandsave(field,proc_mod_file,firstyr,lastyr)

if processobs:
    processandsave(obs,proc_obs_file,firstyr,lastyr)


# In[10]:


### 4) Read processed data, regrid model to obs grid, plot, saving figures: #######################################

obsstats = xr.open_dataset(proc_obs_file)
obsstats=obsstats.rename({'latitude':'lat'})
obsstats=obsstats.rename({'longitude':'lon'})

obsmean=obsstats.themean 
obsstd=obsstats.thestd
obstrend=obsstats.trend 
obsdetrendedstd=obsstats.detrended_std 
obsonemolagcorr=obsstats.onemolagcorr
obsoneyrlagcorr=obsstats.oneyrlagcorr

modstats = xr.open_dataset(proc_mod_file)

coords = [a for a in modstats.coords]
if 'longitude' in coords:
    modstats=modstats.rename({'latitude':'lat'})
    modstats=modstats.rename({'longitude':'lon'})

# regrid model data to obs grid
method = 'nearest_s2d'       #method = 'nearest_d2s'  # this was bad do not use
regridder = xe.Regridder(modstats, obsstats, method, periodic=False, reuse_weights=False)
modstats=regridder(modstats)

modmean=modstats.themean 
modstd=modstats.thestd
modtrend=modstats.trend 
moddetrendedstd=modstats.detrended_std 
modonemolagcorr=modstats.onemolagcorr
modoneyrlagcorr=modstats.oneyrlagcorr

month=modstats.month.values
monthabbrev=modstats.monthabbrev.values

obsstats.close()
modstats.close()


# In[11]:


#import copy

def monthlyplot(field, obs=None, edgec=None, figfile='./figure.png',
                cmapname='PuBu_r', statname='Mean', unitname='Fraction',vmin=0.,vmax=1.):
    fig = plt.figure(figsize=(12,10))
    cmap_c = cmapname
    #cmap = plt.get_cmap(cmapname)
    #cmap_c = copy.copy(cmap)
    #cmap_c.set_bad(color = 'lightgrey')

    try: 
        obs.any()
        edge=True
        if edgec==None:
            edgec='yellow'
    except:
        edge=False
            
    for m, themonth in enumerate(monthabbrev):
        ax = plt.subplot(3,4,m+1,projection = ccrs.NorthPolarStereo())
        ax.add_feature(cfeature.LAND,zorder=100,edgecolor='k',facecolor='darkgrey')

        ax.set_extent([0.005, 360, 50, 90], crs=ccrs.PlateCarree())
        pl = field.sel(month=m).plot(x='lon', y='lat', vmin=vmin, vmax=vmax, 
                        transform=ccrs.PlateCarree(),cmap=cmap_c,add_colorbar=False)
        if edge:
            ed = obs.sel(month=m).plot.contour(levels=[.15],x='lon', y='lat', linewidths=2, 
                        transform=ccrs.PlateCarree(),colors=[edgec])
  
        ax.set_title(themonth,fontsize=14)


    fig.suptitle(modelname+' '+statname+' Sea Ice Concentration '+str(firstyr)+'-'+str(lastyr), fontsize=18)

    cbar_ax = fig.add_axes([0.315, 0.08, 0.4, 0.02]) #[left, bottom, width, height]
    cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
    
  
    cbar.ax.set_title(unitname,fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(figfile, format='png',dpi=300)
    plt.show()
    plt.close()
    return


# In[12]:


figfile=figures_dir+'themean_'+firstyr+'-'+lastyr+'.png'
monthlyplot(modmean, obs=obsmean, figfile=figfile, cmapname='Blues_r', statname='Mean', unitname='Fraction',vmin=0.,vmax=1.)


# In[13]:


monthlyplot(obsmean, cmapname='Blues_r', statname='Mean', unitname='Fraction',vmin=0.,vmax=1.)


# In[14]:


figfile=figures_dir+'themean_anomalies'+firstyr+'-'+lastyr+'.png'
monthlyplot(modmean-obsmean, obsmean, edgec='gray', cmapname='RdBu_r', statname='Minus Obs Mean', unitname='Fraction',vmin=-0.8,vmax=0.8)


# In[15]:


figfile=figures_dir+'detrendedstd_'+firstyr+'-'+lastyr+'.png'
monthlyplot(moddetrendedstd, obs=modmean, edgec='silver', figfile=figfile, cmapname='hot_r', statname='Detrended Std Dev', unitname='Fraction',vmin=0.,vmax=0.3)


# In[16]:


figfile=figures_dir+'detrendedstd_anomalies'+firstyr+'-'+lastyr+'.png'
monthlyplot(moddetrendedstd-obsdetrendedstd, obsmean, edgec='gray', figfile=figfile, cmapname='RdBu_r', statname='Minus Obs Detrended Std Dev', unitname='Fraction',vmin=-0.3,vmax=0.3)


# In[17]:


figfile=figures_dir+'onemolagcorr_'+firstyr+'-'+lastyr+'.png'
monthlyplot(modonemolagcorr, obs=modmean, edgec='silver', figfile=figfile, cmapname='hot_r', statname='One-Month Lag Correlation', unitname='Correlation',vmin=0.,vmax=1.)


# In[18]:


figfile=figures_dir+'onemolagcorr_anomalies_'+firstyr+'-'+lastyr+'.png'
monthlyplot(modonemolagcorr-obsonemolagcorr, obs=obsmean, edgec='silver', figfile=figfile, cmapname='RdBu_r', statname='Minus Obs One-Mon. Lag Corr.', unitname='Correlation',vmin=-1.,vmax=1.)


# In[19]:


figfile=figures_dir+'oneyrlagcorr_'+firstyr+'-'+lastyr+'.png'
monthlyplot(modoneyrlagcorr, obs=modmean, edgec='silver', figfile=figfile, cmapname='hot_r', statname='One-Yr. Lag Corr.', unitname='Correlation',vmin=-0.,vmax=0.5)


# In[20]:


figfile=figures_dir+'oneyrlagcorr_anomalies_'+firstyr+'-'+lastyr+'.png'
monthlyplot(modoneyrlagcorr-obsoneyrlagcorr, obs=obsmean, edgec='silver', figfile=figfile, cmapname='RdBu_r', statname='Minus Obs One-Yr. Lag Corr.', unitname='Correlation',vmin=-0.5,vmax=0.5)


# In[ ]:





