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

import numpy as np
import xarray as xr
import xesmf as xe


# BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
#
# On my system, the monthly-mean variables are contained in individual
# files that span all available years in the reanalysis from 1979 to
# the ~present. I set these as environment variables, but explicitly
# show the paths in comments as examples 

# Some needed functions #


def field_regridding(ds, latname, lonname):
    r""" Regrid input data so that there are 73 latitude points. This grid
    includes 5S and 5N, which are needed for the QBO analysis. This grid
    includes 60N, which is needed for the SSW analysis. """

    # Check to see if the latitudes are organized north to south or south to north
    lat_first = ds[latname].values[0]
    lat_end = ds[latname].values[-1]

    if lat_first >= lat_end:
        lats = np.linspace(90, -90, num=73)
    if lat_end > lat_first:
        lats = np.linspace(-90, 90, num=73)

    # Check to see if the longitudes are organized -180/180 or 0 to 360
    lon_first = ds[lonname].values[0]
    print(lon_first, 'lon_first')

    if lon_first < 0:
        lons = np.linspace(-180, 177.5, num=144)
    if lon_first >= 0:
        lons = np.linspace(0, 357.5, num=144)

    ds_out = xr.Dataset({'lat': (['lat'], lats), 'lon': (['lon'], lons), })
    regridder = xe.Regridder(ds, ds_out, 'bilinear')
    regridded = regridder(ds)
    print(regridded, 'regridded')

    return regridded


def compute_total_eddy_heat_flux(varray, tarray, vname, tname):
    r""" Compute the total (all zonal wavenumbers) eddy heat flux
    using monthly data. Output field has new variable, 'ehf.' """

    # Take the zonal means of v and T
    dummy = varray.mean('lon')

    eddyv = (varray - varray.mean('lon'))[vname]
    eddyt = (tarray - tarray.mean('lon'))[tname]

    ehf = np.nanmean(eddyv.values * eddyt.values, axis=-1)
    dummy[vname].values[:] = ehf
    dummy = dummy.rename({vname: 'ehf'})
    print(dummy)

    return dummy


# Load the observational data #

sfi = '/Volumes/Personal-Folders/CCP-Dillon/ERA5/stationary/POD/HadISST_sst.nc'
pfi = '/Volumes/Personal-Folders/CCP-Dillon/ERA5/stationary/POD/cat-era5-prmsl-monmean-91-180.nc'
ufi = '/Volumes/Personal-Folders/CCP-Dillon/ERA5/stationary/POD/cat-era5-uwnd-monmean-91-180.nc'
vfi = '/Volumes/Personal-Folders/CCP-Dillon/ERA5/stationary/POD/cat-era5-vwnd-monmean-91-180.nc'
tfi = '/Volumes/Personal-Folders/CCP-Dillon/ERA5/stationary/POD/cat-era5-air-monmean-91-180.nc'

# Open datasets #

sst_ds = xr.open_dataset(sfi)
psl_ds = xr.open_dataset(pfi)
uwnd_ds = xr.open_dataset(ufi)
vwnd_ds = xr.open_dataset(vfi)
air_ds = xr.open_dataset(tfi)

# Regrid #

sst_regridded = field_regridding(sst_ds, 'latitude', 'longitude')
psl_regridded = field_regridding(psl_ds, 'lat', 'lon')
uwnd_regridded = field_regridding(uwnd_ds, 'lat', 'lon')
vwnd_regridded = field_regridding(vwnd_ds, 'lat', 'lon')
air_regridded = field_regridding(air_ds, 'lat', 'lon')

# By the end of this block of code, the vwnd, air, and hgt variables
# should each contain all available months of meridional wind,
# air temperature and geopotential height, respectively. They can be
# lazily loaded with xarray (e.g., after using open_mfdataset) 
# END: READ INPUT FIELDS ###

r""" Compute the total (all zonal wavenumbers) eddy heat flux
using monthly data. Output field has new variable, 'ehf.' """

# Take the zonal means of v and T
dummy = vwnd_regridded.mean('lon')

eddyv = (vwnd_regridded - vwnd_regridded.mean('lon'))['vwnd']
eddyt = (air_regridded - air_regridded.mean('lon'))['air']

ehf = np.nanmean(eddyv.values * eddyt.values, axis=-1)
dummy['vwnd'].values[:] = ehf
ehf = dummy.rename({'vwnd': 'ehf'})
ehf.attrs['long_name'] = "Zonal Mean Eddy Heat Flux (v'T')"

r""" Zonally average the zonal wind """
uzm = uwnd_regridded.mean('lon')
uzm = uzm.rename({'uwnd': 'ua'})

r""" Change name in psl file """
psl_out = psl_regridded.rename({'prmsl': 'psl'})

print('######### BREAK ##########')

print(sst_regridded)
print('sst_regridded')
print(' ')
print(ehf)
print('ehf')
print(' ')
print(uzm)
print('uzm')
print(' ')
print(psl_ds)
print('psl_ds')
print(' ')

# Merge DataArrays into output dataset
out_ds = xr.merge([ehf, uzm, psl_out])
print(out_ds)
out_ds = out_ds.rename({'level': 'lev'})
out_ds.attrs['reanalysis'] = 'ERA5'
out_ds.attrs['notes'] = 'Fields derived from monthly-mean ERA5 data on pressure levels'

out_ds.psl.attrs['units'] = 'Pa'
out_ds.ua.lev.attrs['units'] = 'hPa'
out_ds.ehf.lev.attrs['units'] = 'hPa'

sst_out_ds = sst_regridded
sst_out_ds.attrs['reanalysis'] = 'HadiSST'
sst_out_ds.attrs['notes'] = 'Fields derived from monthly-mean HadiSST sea surface temperature'
sst_out_ds = sst_out_ds.rename({'sst': 'tos'})

'''
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
'''

filename = 'stc-qbo-enso-obs-atm.nc'
out_ds.to_netcdf(filename)
filename = 'stc-qbo-enso-obs-ocn.nc'
sst_out_ds.to_netcdf(filename)
