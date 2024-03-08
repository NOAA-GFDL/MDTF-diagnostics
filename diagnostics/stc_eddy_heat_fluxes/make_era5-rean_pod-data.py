# ==============================================================================
# MDTF Strat-Trop Coupling: Vertical Wave Propagation POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Vertical Wave Propagation POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# This script shows a simple recipe for creating the "pre-digested" reanalysis
# data used for making the reanalysis versions of the POD plots.
#
# Data for individual variables obtained from:
# https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels-monthly-means?tab=form
#
# Need the following variables:
# -----------------------------
# v-component of wind
# air temperature
# geopotential (this is post-processed to geopot height by dividing by 9.80665)

import os

import numpy as np
import xarray as xr

# BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
#
# On my system, the monthly-mean variables are contained in individual
# files that span all available years in the reanalysis from 1979 to
# the ~present. I set these as environment variables, but explicitly
# show the paths in comments as examples 

vwnd_fi = os.environ['ERA5_MONTHLY_V'] # '/Projects/era5/Monthlies/pressure/vwnd.mon.mean.nc'
air_fi = os.environ['ERA5_MONTHLY_T']  # '/Projects/era5/Monthlies/pressure/air.mon.mean.nc'
hgt_fi = os.environ['ERA5_MONTHLY_Z']  # '/Projects/era5/Monthlies/pressure/hgt.mon.mean.nc'

vwnd_ds = xr.open_dataset(vwnd_fi)
air_ds = xr.open_dataset(air_fi)
hgt_ds = xr.open_dataset(hgt_fi)

# By the end of this block of code, the vwnd, air, and hgt variables
# should each contain all available months of meridional wind,
# air temperature and geopotential height, respectively. They can be
# lazily loaded with xarray (e.g., after using open_mfdataset) 
# END: READ INPUT FIELDS ###


ehf = []
zg_zm = []
ta_zm_50 = []

# Not necessary to use a for loop here to perform the following computations;
# can simply use dask and its lazy execution/computation. However, on my system
# going through timestep by timestep ended up being quicker
for time in hgt.time:
    print(time.values)

    # May need to adjust variable names here to match those in your own files.
    # vwnd = v-component of wind
    # air = air temperature
    # hgt = geopotential height
    v100 = vwnd_ds.vwnd.sel(time=time,level=100).load()
    t100 = air_ds.air.sel(time=time, level=100).load()
    t50 = air_ds.air.sel(time=time, level=50).load()
    zg = hgt_ds.hgt.sel(time=time).load()

    # Compute zonal mean temperatures
    ta_zm_50_tmp = t50.mean('lon')
    ta_zm_100_tmp = t100.mean('lon')

    # Compute zonal mean eddy heat flux
    ehf_tmp = ((v100 - v100.mean('lon'))*(t100 - ta_zm_100_tmp)).mean('lon')

    # Compute zonal mean geopotential height
    zg_zm_tmp = zg.mean('lon')

    # Append the individual DataArrays into lists
    ehf.append(ehf_tmp)
    zg_zm.append(zg_zm_tmp)
    ta_zm_50.append(ta_zm_50_tmp)

# Make the zonal mean eddy heat flux DataArray and add metadata
ehf = xr.concat(ehf, dim='time')
ehf.name = 'ehf_100'
ehf.attrs['units'] = 'K m s-1'
ehf.attrs['long_name'] = "100 hPa Zonal Mean Eddy Heat Flux (v'T')"

# Make the zonal mean Z DataArray and add metadata
zg_zm = xr.concat(zg_zm, dim='time')
zg_zm.name = 'zg_zm'
zg_zm.attrs['units'] = 'm'
zg_zm.attrs['long_name'] = "Zonal Mean Geopotential Height"

# Make the zonal mean T DataArrays and add metadata
ta_zm_50 = xr.concat(ta_zm_50, dim='time')
ta_zm_50.name = 'ta_zm_50'
ta_zm_50.attrs['units'] = 'K'
ta_zm_50.attrs['long_name'] = "50 hPa Zonal Mean Temperature"

# Merge DataArrays into output dataset
out_ds = xr.merge([ta_zm_50, zg_zm, ehf])
out_ds.attrs['reanalysis'] = 'ERA5'
out_ds.attrs['notes'] = 'Fields derived from monthly-mean ERA5 data on pressure levels'

# To reduce size of output file without changing results much, will thin the
# available latitudes from 0.25 to 0.5 degrees. This is optional.
out_ds = out_ds.isel(lat=slice(0,None,2))

# To reduce size of output file even more, we will only keep latitudes poleward
# of 30 degrees (since we are primarily interested in the extratropics).
# This step is also optional.
out_ds = out_ds.where(np.abs(out_ds.lat) >= 30, drop=True)

# To reduce size of output file even more more, we will use zlib compression
# on each variable. This step is also optional.
encoding = {'ta_zm_50':  {'dtype':'float32', 'zlib':True, 'complevel':7},
            'zg_zm':     {'dtype':'float32', 'zlib':True, 'complevel':7},
            'ehf_100':   {'dtype':'float32', 'zlib':True, 'complevel':7}}

# Save the output file
filename = 'stc_eddy_heat_fluxes_obs-data.nc'
out_ds.rename({'level':'lev'}).to_netcdf(filename, encoding=encoding)
