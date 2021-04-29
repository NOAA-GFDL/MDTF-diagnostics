#!/usr/bin/env python

import numpy as np 
import xarray as xr
import os


folder = '/localdrive/drive6/era5/data/six_hrly'
out_folder = '/localdrive/drive6/era5/data/six_hrly/converts'

# # Standard sample output that is used by the tracker
# tmp = '/localdrive/drive10/mcms_tracker/RUNDIR/DATA365/slp.1902.nc'
# ds_tmp = xr.open_dataset(tmp)
# print('STANDARD')
# print('\n ================================== \n')
# print(ds_tmp.slp)
# print('\n ================================== \n')
# print('\n ================================== \n')


year_list = [2019, 2020]
var_list = ['tp', 'u10', 'v10', 'msl']
# var_list = ['msl']

var_map = {'msl': 'slp', 'tp': 'pr', 'u10': 'u10', 'v10': 'v10'}

for var in var_list:
  print(f'{var.upper()}')
  for year in range(year_list[0], year_list[1]+1):

    # filename of the SLP file for the year
    fn = os.path.join(folder, f'{var}/{var}_{year}_6hrly.nc')
    out_fn = os.path.join(out_folder, f'{var_map[var]}.{year}.nc')
   
    # opening data for the given year
    ds = xr.open_dataset(fn)

    # # renaming variable from 'msl' to 'slp'
    # ds = ds.rename({'msl': 'slp', 'latitude': 'lat', 'longitude': 'lon'})
    ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})

    # if (year == 2019):
    #   ds = ds.rename({f'{var}_0001' : var})

    if (var == 'msl'):
      ds = ds.rename({'msl': 'slp'})
      # converting slp values to mb from Pa
      ds['slp'] = ds.slp/100.
      ds.slp.attrs['units'] = 'mb'
    else:
      ds = ds.rename({var: var_map[var]})

    # converting the 'time' variable to hours since start of year
    len_time = len(ds.time)
    ds['time'] = np.asarray(np.arange(0, len_time*6, 6), dtype=np.int64)
    ds.time.attrs['delta_t'] = '0000-00-00 06:00:00'
    ds.time.attrs['units'] = 'hours since %d-01-01 00:00:00'%(year)

    # saving data to output file 
    ds.to_netcdf(out_fn)

    print('\tDone converting to %d.'%(year))
