#!/usr/bin/env python

import numpy as np 
import xarray as xr
import os


folder = '/localdrive/drive6/era5/data/MSL'
out_folder = '/localdrive/drive6/era5/data/slp_rename/'

# # Standard sample output that is used by the tracker
# tmp = '/localdrive/drive10/mcms_tracker/RUNDIR/DATA365/slp.1902.nc'
# ds_tmp = xr.open_dataset(tmp)
# print('STANDARD')
# print('\n ================================== \n')
# print(ds_tmp.slp)
# print('\n ================================== \n')
# print('\n ================================== \n')


year_list = [2018, 2020]

for year in range(year_list[0], year_list[1]+1):

  # filename of the SLP file for the year
  fn = os.path.join(folder, 'msl_%d.nc'%(year))
  out_fn = os.path.join(out_folder, 'slp.%d.nc'%(year))
 
  # opening data for the given year
  ds = xr.open_dataset(fn)


  # renaming variable from 'msl' to 'slp'
  ds = ds.rename({'msl': 'slp', 'latitude': 'lat', 'longitude': 'lon'})

  # converting the 'time' variable to hours since start of year
  len_time = len(ds.time)
  ds['time'] = np.asarray(np.arange(0, len_time), dtype=np.int)
  ds.time.attrs['delta_t'] = '0000-00-00 01:00:00'
  ds.time.attrs['units'] = 'hours since %d-01-01 00:00:00'%(year)

  # converting slp values to mb from Pa
  ds['slp'] = ds.slp/100.
  ds.slp.attrs['units'] = 'mb'

  # saving data to output file 
  ds.to_netcdf(out_fn)

  print('Done converting to %d.'%(year))
