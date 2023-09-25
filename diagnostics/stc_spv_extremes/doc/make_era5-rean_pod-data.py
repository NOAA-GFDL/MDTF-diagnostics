# ==============================================================================
# MDTF Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# This script shows a simple recipe for creating the "pre-digested" reanalysis
# data used for making the reanalysis versions of the POD plots.
#
# Data for individual variables obtained from:
# https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels?tab=form
#
# Note that the raw reanalysis files must be averaged into daily-means for this code
# to work properly.
#
# Need the following daily-mean variables:
# -----------------------------
# U-component of wind
# Geopotential heights
# 2m air temperatures

import os

import numpy as np
import xarray as xr

### BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
#
# On my system, the daily-mean 3D variables are contained in individual
# files that span each year in the reanalysis. Note that my files have also been
# spatially degraded by selecting every nth latitude (typically n=4 or 8). 
# I set the location of these files as environment variables, but explicitly
# show the paths in comments as examples 

uwnd_fi = os.environ['ERA5_DAILY_U']  # '/Volumes/ECMWF/ERA5/press/dailymean/u/era5_uwnd_pres_????.nc'
zg_fi = os.environ['ERA5_DAILY_Z']  # '/Volumes/ECMWF/ERA5/press/dailymean/zg/era5_hgt_????.nc'
tas_fi = os.environ['ERA5_DAILY_TS'] # '/Volumes/ECMWF/ERA5/sfc/daily/era5_air2m_????.nc'

def preprocess_zm(ds):
    '''Take zonal-mean of each file before concatenating along time'''
    return ds.mean('lon')

uwnd_ds = xr.open_mfdataset(uwnd_fi,decode_cf=True, combine='by_coords',preprocess=preprocess_zm)
zg_ds = xr.open_mfdataset(zg_fi,decode_cf=True, combine='by_coords')
tas_ds = xr.open_mfdataset(tas_fi,decode_cf=True, combine='by_coords')

# By the end of this block of code, the uwnd, zg, and tas variables
# should each contain all available days of zonal-mean zonal winds,  
# geopotential heights, and 2m air temperatures respectively. They can be
# lazily loaded with xarray (e.g., after using open_mfdataset) 
### END: READ INPUT FIELDS ###

# Determine which years will be used from reanalysis to compare to models
# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
#FIRSTYR = int(os.environ['FIRSTYR'])
#LASTYR = int(os.environ['LASTYR'])

FIRSTYR = 1979
LASTYR = 2014

uwnd_ds = uwnd_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))
zg_ds = zg_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))
tas_ds = tas_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))

#load the files- this part can take a little while since the files are 
# daily-means. Note that the variable names here may vary depending on
# your files and may need to be adjusted.

# Compute zonal mean geopotential heights
zg_zm = zg_ds.hgt.mean('lon').load()
    
# Separately, pull the 500 mb gridded geopotential heights
# Note, need to verify that pressure levels are in hPa or mb and not Pa
zg_500 = zg_ds.hgt.sel(level=500).load()

# load zonal-mean zonal winds
uwnd_zm = uwnd_ds.uwnd.load()

# load 2m air temperatures
tas = tas_ds.air.load()
# Note, my tas files were gridded at 1x1 while the pressure level vars
# were 2x2. to degrade the grid to be the same size, here I select every
# other grid point
tas = tas.isel(lat=slice(0,None,2),lon=slice(0,None,2))

#print(tas, zg_500,uwnd_zm,zg_zm)

# Make the zonal mean uwnd DataArray and add metadata
uwnd_zm = xr.concat(uwnd_zm, dim='time')
uwnd_zm.name = 'uwnd_zm'
uwnd_zm.attrs['units'] = 'm s**-1'
uwnd_zm.attrs['long_name'] = "Zonal-mean U component of wind"

# Make the zonal mean temp DataArray and add metadata
zg_zm = xr.concat(zg_zm, dim='time')
zg_zm.name = 'zg_zm'
zg_zm.attrs['units'] = 'm'
zg_zm.attrs['long_name'] = "Zonal-mean geopotential height"

# Make the zonal mean temp DataArray and add metadata
zg_500 = xr.concat(zg_500, dim='time')
zg_500.name = 'zg_500'
zg_500.attrs['units'] = 'm'
zg_500.attrs['long_name'] = "500 mb gridded geopotential height"

# Make the surface temperature DataArray and add metadata
tas = xr.concat(tas, dim='time')
tas.name = 'tas'
tas.attrs['units'] = 'K'
tas.attrs['long_name'] = "2m air temperature"

# Merge DataArrays into output dataset
out_ds = xr.merge([uwnd_zm, zg_zm, zg_500, tas])
out_ds.attrs['reanalysis'] = 'ERA5'
out_ds.attrs['notes'] = 'Fields derived from daily-mean ERA5 data on pressure and near-surface levels'

#print(out_ds.lon.values)

# To reduce size of output file even more, we will only keep latitudes poleward
# of 30 degrees (since we are primarily interested in the extratropics).
# This step is also optional.
out_ds = out_ds.where(np.abs(out_ds.lat) >= 30, drop=True)

# To reduce size of output file even more, we will use a scale_factor
# on each variable. This step is also optional.
encoding = {'uwnd_zm':    {'dtype':'float32', 'scale_factor':0.1},
            'zg_zm':      {'dtype':'float32', 'scale_factor':0.1},
            'zg_500':     {'dtype':'float32', 'scale_factor':0.1},
            'tas':        {'dtype':'float32', 'scale_factor':0.1} }

# Save the output file
#OBS_DATA = os.environ['OBS_DATA'] 
OBS_DATA = '/Users/abutler/earth-analytics/mdtf/MDTF-diagnostics/diagnostics/stc_spv_extremes/'
filename = OBS_DATA+'stc_spv_extremes_obs-data.nc'
out_ds.rename({'level':'plev'}).to_netcdf(filename, encoding=encoding)

