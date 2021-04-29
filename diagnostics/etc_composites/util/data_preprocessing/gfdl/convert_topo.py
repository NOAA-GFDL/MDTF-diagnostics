import xarray as xr
import numpy as np
import os
import matplotlib.pyplot as plt

import pdb


in_file = '/mnt/drive3/atmos.static.nc'
out_file = '/localdrive/drive6/gfdl/convert_invariants.nc'

ds = xr.open_dataset(in_file)

lat = np.float32(ds.lat.values)
lon = np.float32(ds.lon.values)

# # converting lon mid values to lon left edges
# lon = lon - (lon[1] - lon[0])/2.
# lat = lat - (lat[1] - lat[0])/2.

# land-sea mask
lsm = xr.DataArray(ds.landsea.values, coords={'lat': lat, 'lon': lon}, dims=['lat', 'lon'])
lsm.attrs['units'] = 'none'
lsm.attrs['long_name'] = 'fraction amount of land'

# surface height
hgt = xr.DataArray(ds.oro.values, coords={'lat': lat, 'lon': lon}, dims=['lat', 'lon'])
hgt.attrs['units'] = 'm'
hgt.attrs['long_name'] = 'surface_height'

out_ds = xr.Dataset({'lsm': lsm, 'hgt': hgt})
out_ds.to_netcdf(out_file)

print('Completed Creating Invariants File.')
