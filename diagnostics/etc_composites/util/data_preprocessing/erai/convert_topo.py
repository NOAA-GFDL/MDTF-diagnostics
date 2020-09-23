import xarray as xr
import numpy as np 

# read in the invariants file, which has lsm and topo in my case
in_file = '/localdrive/drive6/erai/invariants.nc'
out_file = '/localdrive/drive6/erai/converts/invariants.nc'

# open the file 
ds = xr.open_dataset(in_file)

# renaming the height variable 
ds = ds.rename({'z': 'hgt', 'lsm': 'lsm'})

# making sure the units are correct for lsm
ds['hgt'] = ds['hgt']/9.8
ds.hgt.attrs['units'] = 'm'
ds.hgt.attrs['long_name'] = 'surface_height_from_geopotential'
ds.hgt.attrs['standard_name'] = 'surface_height'

# writing the output file 
ds.to_netcdf(out_file)

# closing the file
ds.close()
  
