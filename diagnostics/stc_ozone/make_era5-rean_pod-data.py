# ==============================================================================
# MDTF Strat-Trop Coupling: Stratospheric Ozone and Circulation POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Stratospheric Ozone and Circulation POD
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
# Ozone mass mixing ratio
# U-component of wind
# Air temperature

import os

import numpy as np
import xarray as xr

### BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
#
# On my system, the monthly-mean 3D variables are contained in individual
# files that span each year in the reanalysis from 1979 to
# the ~present. I set these as environment variables, but explicitly
# show the paths in comments as examples 

o3_fi = os.environ['ERA5_MONTHLY_O3'] # '/Volumes/ECMWF/ERA5/press/monmean/o3/era5.moda.an.pl.o3.????.nc'
uwnd_fi = os.environ['ERA5_MONTHLY_U']  # '/Volumes/ECMWF/ERA5/press/monmean/u/era5.moda.an.pl.u.????.nc'
temp_fi = os.environ['ERA5_MONTHLY_T']  # '/Volumes/ECMWF/ERA5/press/monmean/t/era5.moda.an.pl.t.????.nc'

o3_ds = xr.open_mfdataset(o3_fi,decode_cf=True, combine='by_coords')
uwnd_ds = xr.open_mfdataset(uwnd_fi,decode_cf=True, combine='by_coords')
temp_ds = xr.open_mfdataset(temp_fi,decode_cf=True, combine='by_coords')

# By the end of this block of code, the o3, uwnd and temp variables
# should each contain all available months of ozone mixing ratio, 
# zonal winds, and temperatures, respectively. They can be
# lazily loaded with xarray (e.g., after using open_mfdataset) 
### END: READ INPUT FIELDS ###

# Determine which years will be used from reanalysis to compare to models
# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
FIRSTYR = int(os.environ['FIRSTYR'])
LASTYR = int(os.environ['LASTYR'])

o3_ds = o3_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))
uwnd_ds = uwnd_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))
temp_ds = temp_ds.sel(time=slice(str(FIRSTYR), str(LASTYR)))

# Not necessary to use a for loop here to perform the following computations;
# can simply use dask and its lazy execution/computation. However, on my system
# going through timestep by timestep ended up being quicker

o3_zm = []
uwnd_zm = []
temp_zm = []

for time in uwnd_ds.time:
    print(time.values)
    
    #load files
    # May need to adjust variable names here to match those in your own files.
    # u = u-component of wind
    # o3 = Ozone mass mixing ratio
    # t = Air temperature
    o3 = o3_ds.o3.sel(time=time).load()
    uwnd = uwnd_ds.u.sel(time=time).load()
    temp = temp_ds.t.sel(time=time).load()
    
    #CMIP6 standard output for ozone is in mole fraction of O3. 
    #ERA5 is in kg/kg (mass mixing ratio) - need to convert to mol/mol
    #See: https://confluence.ecmwf.int/pages/viewpage.action?pageId=153391710
    mol_mass_dry_air = 28.9644 #units g/mol
    mol_mass_o3 = 47.9982 #units g/mol
    o3_new = o3 * (mol_mass_dry_air/mol_mass_o3)

    # Compute zonal mean ozone
    o3_zm_tmp = o3_new.mean('longitude')

    # Compute zonal mean uwnd
    uwnd_zm_tmp = uwnd.mean('longitude')
    
    # Compute zonal mean temp
    temp_zm_tmp = temp.mean('longitude')
    
    # Append the individual DataArrays into lists
    uwnd_zm.append(uwnd_zm_tmp)
    o3_zm.append(o3_zm_tmp)
    temp_zm.append(temp_zm_tmp)

# Make the zonal mean uwnd DataArray and add metadata
uwnd_zm = xr.concat(uwnd_zm, dim='time')
uwnd_zm.name = 'uwnd_zm'
uwnd_zm.attrs['units'] = 'm s**-1'
uwnd_zm.attrs['long_name'] = "Zonal-mean U component of wind"

# Make the zonal mean O3 DataArray and add metadata
o3_zm = xr.concat(o3_zm, dim='time')
o3_zm.name = 'o3_zm'
o3_zm.attrs['units'] = 'mol mol-1'
o3_zm.attrs['long_name'] = "Mole Fraction of O3"

# Make the zonal mean temp DataArray and add metadata
temp_zm = xr.concat(temp_zm, dim='time')
temp_zm.name = 'temp_zm'
temp_zm.attrs['units'] = 'K'
temp_zm.attrs['long_name'] = "Zonal-mean Air Temperature"

# Merge DataArrays into output dataset
out_ds = xr.merge([o3_zm, uwnd_zm, temp_zm])
out_ds.attrs['reanalysis'] = 'ERA5'
out_ds.attrs['notes'] = 'Fields derived from monthly-mean ERA5 data on pressure levels'

# To reduce size of output file without changing results much, will thin the
# available latitudes from 0.25 to 0.5 degrees. This is optional.
out_ds = out_ds.isel(latitude=slice(0,None,2))

# To reduce size of output file even more, we will only keep latitudes poleward
# of 30 degrees (since we are primarily interested in the extratropics).
# This step is also optional.
out_ds = out_ds.where(np.abs(out_ds.latitude) >= 30, drop=True)

# To reduce size of output file even more more, we will use zlib compression
# on each variable. This step is also optional.
encoding = {'o3_zm':       {'dtype':'float32', 'zlib':True, 'complevel':7},
            'uwnd_zm':     {'dtype':'float32', 'zlib':True, 'complevel':7},
            'temp_zm':     {'dtype':'float32', 'zlib':True, 'complevel':7}}

# Save the output file
OBS_DATA = os.environ['OBS_DATA'] 
filename = OBS_DATA+'stc_ozone_obs-data.nc'
out_ds.rename({'level':'lev'}).rename({'latitude':'lat'}).to_netcdf(filename, encoding=encoding)

