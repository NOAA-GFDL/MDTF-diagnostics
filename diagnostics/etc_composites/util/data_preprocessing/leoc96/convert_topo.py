import xarray as xr
import numpy as np
import os
import matplotlib.pyplot as plt

import pdb

in_file = '/mnt/drive6/LEOC96/atmos/atmos.static.nc'
out_file = '/localdrive/drive6/leo/convert_invariants.nc'

ds = xr.open_dataset(in_file)

lat = ds.lat.values
lon = ds.lon.values 

# converting lon mid values to lon left edges
lon = np.float32(lon)
lat = np.float32(lat)

# land-sea mask
lsm = xr.DataArray(ds.land_mask.values, coords={'lat': lat, 'lon': lon}, dims=['lat', 'lon'])
lsm.attrs['units'] = 'none'
lsm.attrs['long_name'] = 'fraction amount of land'

# surface height
hgt = xr.DataArray(ds.zsurf.values, coords={'lat': lat, 'lon': lon}, dims=['lat', 'lon'])
hgt.attrs['units'] = 'm'
hgt.attrs['long_name'] = 'surface_height'

out_ds = xr.Dataset({'lsm': lsm, 'hgt': hgt})
out_ds.to_netcdf(out_file)

print('Completed Creating Invariants File.')
