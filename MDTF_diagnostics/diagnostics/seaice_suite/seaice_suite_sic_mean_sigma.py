#!/usr/bin/env python
# coding: utf-8
# This file is part of the Sea Ice Suite Diagnostic POD of the MDTF code package
# (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# This POD calculates maps of the sea ice concentration mean, trend,
# standard deviation, and one-lag correlation by month. Sea ice
# concentration from passive microwave satellite from HadISSTv1.1 is
# included to compare with model. The observed ice edge is shown for
# reference.
#
# All correlations are computed after detrending.  For a one-month lag, 
# the map for January shows the correlation of January and February. The 
# map for February shows the correlation of February and March. And so forth. 
# For a one-year lag, the map for January shows the correlation of January
# and January a year later. And so forth.
#
# The results from this POD are to be appear in a paper being prepared
# for the MAPP team special issue.
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
#   Unless you've distributed your script elsewhere, you don't need to change this.
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
import os
import matplotlib
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
import xesmf as xe
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# homegrown this code also imports pandas and scipy
from seaice_MLD_stats import (
    xr_reshape,
    _lrm,
    _lagcorr,
)
matplotlib.use('Agg')  # non-X windows backend


def readindata(file, varname='siconc', firstyr='1979', lastyr='2014'):
    print("file ", file)
    ds = xr.open_dataset(file)
    ds = ds.sel(time=slice(firstyr.zfill(4)+'-01-01', lastyr.zfill(4)+'-12-31'))  # limit to yrs of interest, maybe model dep
    print('Limit domain to Arctic to match obs')  # script would work fine if data were global
    if "latitude" in list(ds.keys()):
        ds = ds.where(ds.latitude > 30., drop=True)  # limit to arctic for now, remove later
    elif "lat" in list(ds.keys()):
        ds = ds.where(ds.lat > 30., drop=True)
    field = ds[varname]
    if field.values[:, :, 3].max() > 1.5:  # ensure we are [0,1] not [0,100]#
        field.values = field.values*0.01
    field.name = varname
    print("varname ", varname)
    ds.close()
    return field


# 1) Loading model data files:
input_file = os.environ['SICONC_FILE']
obsoutput_dir = "{WORK_DIR}/obs/".format(**os.environ)
modoutput_dir = "{WORK_DIR}/model/".format(**os.environ)
figures_dir = "{WORK_DIR}/model/".format(**os.environ)
obs_file = '{OBS_DATA}/HadISST_ice_1979-2016_grid_nh.nc'.format(**os.environ)
proc_obs_file = obsoutput_dir+'HadISST_stats_1979-2014.nc'.format(**os.environ)
proc_mod_file = modoutput_dir+'seaice_fullfield_stats.nc'

modelname = "{CASENAME}".format(**os.environ)
siconc_var = "{siconc_var}".format(**os.environ)
firstyr = "{startdate}".format(**os.environ)
lastyr = "{enddate}".format(**os.environ)
# obsfirstyr and obslastyr may be changed in the POD settings.jsonc file
obsfirstyr = "{obsfirstyr}".format(**os.environ)
obslastyr = "{obslastyr}".format(**os.environ)

processmod = not os.path.isfile(proc_mod_file)  # check if obs proc file exists
if processmod:
    field = readindata(input_file, siconc_var, firstyr, lastyr)

processobs = not(os.path.isfile(proc_obs_file))  # check if obs proc file exists
if processobs:  # if no proc file then must get obs and process
    obs = readindata(obs_file, 'sic', firstyr=obsfirstyr, lastyr=obslastyr)


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
    firstyr = int(firstyr)
    lastyr = int(lastyr)
    
    field = xr_reshape(field,'time',['year','month'],[np.arange(firstyr,lastyr+1),np.arange(12)])
    print('computing trend, this may take a few minutes')
    trend, intercept = xr.apply_ufunc(_lrm, field.year, field,
                                      input_core_dims=[['year'], ['year']],
                                      output_core_dims=[[],[]],
                                      output_dtypes=[float, float],
                                      vectorize=True)
                           #dask='parallelized')

    print('computing the rest')
    residuals = field - (field.year*trend+ intercept)

    themean = field.mean(dim='year')
    thestd = field.std(dim='year')
    detrendedstd = residuals.std(dim='year')
    
    themean.name = 'themean'
    thestd.name = 'thestd'
    trend.name = 'trend'
    detrendedstd.name = 'detrended_std'
    residuals.name = 'residuals'

    return themean, thestd, trend, detrendedstd, residuals


def lagcorr(residuals, lag=1):
    """Pearson's correlation coefficient for lagged detrended field computed by month.
    .. math::
        a = residuals
        b = residuals shifted by lag 
        r_{ab} = \\frac{ \\sum_{i=i}^{n} (a_{i} - \\bar{a}) (b_{i} - \\bar{b}) }
                 {\\sqrt{ \\sum_{i=1}^{n} (a_{i} - \\bar{a})^{2} }
                  \\sqrt{ \\sum_{i=1}^{n} (b_{i} - \\bar{b})^{2} }}
    Parameters
    ----------
    residuals : xarray.DataArray detrending by month, which also deseasonalizes

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
        output_dtypes=[float],
        vectorize=True)  # dask='parallelized')

    rlag.name = 'lagcorr'
    rlag=rlag.transpose('month',...)
        
    return rlag


def processandsave(field, file_out, firstyr=1979, lastyr=2014):
    # 2) Doing computations on model or obs:
    # this takes about a few min on data that is already limited to the Arctic
    # recommend using DASK if you decide to compute global metrics
    # residuals are detrended field for each month, effectively making them detrended and deseasonalized
    themean, thestd, trend, detrendedstd, residuals = mainmonthlystats(field, firstyr, lastyr)
    print('main stats done')
    onemolagcorr = lagcorr(residuals,1)
    oneyrlagcorr = lagcorr(residuals,12)
    onemolagcorr.name = 'onemolagcorr'
    oneyrlagcorr.name = 'oneyrlagcorr'

    # 3) Save output data:

    allstats=xr.merge([themean, thestd, trend, detrendedstd, onemolagcorr, oneyrlagcorr])

    months = ['Jan',
              'Feb',
              'Mar',
              'Apr',
              'May',
              'Jun',
              'Jul',
              'Aug',
              'Sep',
              'Oct',
              'Nov',
              'Dec'
              ]

    allstats.coords['monthabbrev'] = xr.DataArray(months, dims='month')
    allstats.to_netcdf(file_out)


if processmod:
    processandsave(field, proc_mod_file, firstyr, lastyr)

if processobs:
    processandsave(obs, proc_obs_file, obsfirstyr, obslastyr)

# 4) Read processed data, regrid model to obs grid, plot, saving figures:

obsstats = xr.open_dataset(proc_obs_file)
obsstats = obsstats.rename({'latitude':'lat'})
obsstats = obsstats.rename({'longitude':'lon'})

obsmean = obsstats.themean
obsstd = obsstats.thestd
obstrend = obsstats.trend
obsdetrendedstd = obsstats.detrended_std
obsonemolagcorr = obsstats.onemolagcorr
obsoneyrlagcorr = obsstats.oneyrlagcorr

modstats = xr.open_dataset(proc_mod_file)

coords = [a for a in modstats.coords]
if 'longitude' in coords:
    modstats = modstats.rename({'latitude':'lat'})
    modstats = modstats.rename({'longitude':'lon'})

# regrid model data to obs grid
method = 'nearest_s2d'
regridder = xe.Regridder(modstats, obsstats, method, periodic=False, reuse_weights=False)
modstats = regridder(modstats)

modmean = modstats.themean
modstd = modstats.thestd
modtrend = modstats.trend
moddetrendedstd = modstats.detrended_std
modonemolagcorr = modstats.onemolagcorr
modoneyrlagcorr = modstats.oneyrlagcorr

month = modstats.month.values
monthabbrev = modstats.monthabbrev.values

obsstats.close()
modstats.close()


def monthlyplot(field, obs=None, edgec=None, figfile='./figure.png',
                cmapname='PuBu_r', statname='Mean', unitname='Fraction', vmin=0., vmax=1.):
    fig = plt.figure(figsize=(12,10))
    cmap_c = cmapname

    if obs is None:
        edge = False
    else:
        edge = True
        if edgec is None:
            edgec = 'yellow'
            
    for m, themonth in enumerate(monthabbrev):
        ax = plt.subplot(3, 4, m+1, projection=ccrs.NorthPolarStereo())
        ax.add_feature(cfeature.LAND, zorder=100, edgecolor='k', facecolor='darkgrey')

        ax.set_extent([0.005, 360, 50, 90], crs=ccrs.PlateCarree())
        pl = field.sel(month=m).plot(x='lon', y='lat', vmin=vmin, vmax=vmax,
                                     transform=ccrs.PlateCarree(), cmap=cmap_c, add_colorbar=False)
        if edge:
            obs.sel(month=m).plot.contour(levels=[.15], x='lon', y='lat', linewidths=2,
                                          transform=ccrs.PlateCarree(), colors=[edgec])
  
        ax.set_title(themonth, fontsize=14)

    fig.suptitle(f"{modelname} {statname} Sea Ice Concentration {firstyr}-{lastyr}", fontsize=18)

    cbar_ax = fig.add_axes([0.315, 0.08, 0.4, 0.02])  # [left, bottom, width, height]
    cbar = fig.colorbar(pl, cax=cbar_ax,  orientation='horizontal')
    cbar.ax.set_title(unitname,fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(figfile, format='png', dpi=300)
    plt.show()
    plt.close()
    return


figfile = f"{figures_dir}themean_{firstyr}-{lastyr}.png"
monthlyplot(modmean, obs=obsmean, figfile=figfile, cmapname='Blues_r',
            statname='Mean', unitname='Fraction', vmin=0., vmax =1.)

figfile = f"{figures_dir}themean_anomalies_{firstyr}-{lastyr}.png"
monthlyplot(modmean-obsmean, obsmean, figfile=figfile, edgec='gray',
            cmapname='RdBu_r', statname='Minus Obs Mean',
            unitname='Fraction', vmin=-0.8, vmax=0.8)

figfile = f"{figures_dir}trend_{firstyr}-{lastyr}.png"
monthlyplot(modtrend, obs=obsmean, figfile=figfile,
            cmapname='RdBu_r', edgec='silver', statname='Trend in',
            unitname='Fraction per year',vmin=-0.03,vmax=0.03)

figfile = f"{figures_dir}trend_anomalies_{firstyr}-{lastyr}.png"
monthlyplot(modtrend-obstrend, obs=obsmean, figfile=figfile,
            cmapname='RdBu_r', edgec='silver', statname='Minus Obs Trend in',
            unitname='Fraction per year',vmin=-0.03,vmax=0.03)

figfile = f"{figures_dir}detrendedstd_{firstyr}-{lastyr}.png"
monthlyplot(moddetrendedstd, obs=modmean, edgec='silver', figfile=figfile,
            cmapname='hot_r', statname='Detrended Std Dev',
            unitname='Fraction',vmin=0.,vmax=0.3)

figfile = f"{figures_dir}detrendedstd_anomalies_{firstyr}-{lastyr}.png"
monthlyplot(moddetrendedstd-obsdetrendedstd, obsmean, edgec='gray',
            figfile=figfile, cmapname='RdBu_r',
            statname='Minus Obs Detrended Std Dev',
            unitname='Fraction', vmin=-0.3, vmax=0.3)

figfile = f"{figures_dir}onemolagcorr_{firstyr}-{lastyr}.png"
monthlyplot(modonemolagcorr, obs=modmean, edgec='silver',
            figfile=figfile, cmapname='hot_r',
            statname='One-Month Lag Correlation',
            unitname='Correlation', vmin=0., vmax=1.)

figfile = f"{figures_dir}onemolagcorr_anomalies_{firstyr}-{lastyr}.png"
monthlyplot(modonemolagcorr-obsonemolagcorr, obs=obsmean, edgec='silver',
            figfile=figfile, cmapname='RdBu_r',
            statname='Minus Obs One-Mon. Lag Corr.',
            unitname='Correlation', vmin=-1., vmax=1.)

figfile = f"{figures_dir}oneyrlagcorr_{firstyr}-{lastyr}.png"
monthlyplot(modoneyrlagcorr, obs=modmean, edgec='silver',
            figfile=figfile, cmapname='hot_r', statname='One-Yr. Lag Corr.',
            unitname='Correlation', vmin=-0., vmax=0.5)

figfile = f"{figures_dir}oneyrlagcorr_anomalies_{firstyr}-{lastyr}.png"
monthlyplot(modoneyrlagcorr-obsoneyrlagcorr, obs=obsmean, edgec='silver',
            figfile=figfile, cmapname='RdBu_r', statname='Minus Obs One-Yr. Lag Corr.',
            unitname='Correlation', vmin=-0.5, vmax=0.5)
