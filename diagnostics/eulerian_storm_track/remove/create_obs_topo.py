import numpy as np 
import matplotlib.pyplot as plt
import xarray as xr
import os

''' ERA-Interim topography file '''
erai_file = '/localdrive/drive6/erai/invariants.nc'
out_file  = './erai_topo.nc'

ds = xr.open_dataset(erai_file)
z = ds.variables['z'][0, :, :].values/9.8
lat = ds.variables['latitude'][:].values
lon = ds.variables['longitude'][:].values
ds.close()

o_ds = xr.Dataset({"topo": (('lat', 'lon'), z)}, coords={"lat": lat, "lon": lon})
o_ds.to_netcdf(out_file)

''' ERA5 topography file '''
era5_file = '/localdrive/drive6/era5/invariants_025.nc'
out_file  = './era5_topo.nc'

ds = xr.open_dataset(era5_file)
z = ds.variables['z'][0, :, :].values/9.8
lat = ds.variables['latitude'][:].values
lon = ds.variables['longitude'][:].values
ds.close()

o_ds = xr.Dataset({"topo": (('lat', 'lon'), z)}, coords={"lat": lat, "lon": lon})
o_ds.to_netcdf(out_file)

