import xarray as xr
import numpy as np 

import os, pdb

years = [1979, 1979]
var_list = ['pr']

in_folder = '/mnt/drive5/ERAINTERIM/'
out_folder = '/localdrive/drive6/erai/converts/'

var_map = {'pr': 'tp'}

for year in range(years[0], years[1]+1):
  for var in var_list:
    in_file = os.path.join(in_folder, f'{var.upper()}/{var.upper()}_{year}.nc')
    out_file = os.path.join(out_folder, f'{var}.{year}.nc')
    ds = xr.open_dataset(in_file)
    in_lat = ds.lat.values
    in_lon = ds.lon.values
    ds.close()

    ds = ds.rename({var_map[var]: var})
    
    roll_amount = np.sum(in_lon < 0)

    tmp_val = ds.lon.values
    tmp_val[tmp_val < 0] += 360
    ds['lon'] = tmp_val
    ds.lon.attrs['units'] = 'degrees_east'
    ds.lon.attrs['axis'] = 'X'
    if (roll_amount > 0): 
      ds['lon'] = ds.lon.roll(lon=roll_amount, roll_coords=True)
      ds[var] = ds[var].roll(lon=roll_amount, roll_coords=True)

    ds.to_netcdf(out_file)
    print(f'Completed {var} for {year}') 

