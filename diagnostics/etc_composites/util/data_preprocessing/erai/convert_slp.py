#!/usr/bin/env python

import numpy as np 
import xarray as xr
import os

folder = '/localdrive/drive6/erai/dl/' 
out_folder = '/localdrive/drive6/erai/converts/'

year_list = [1979, 1983]

for year in range(year_list[0], year_list[1]+1):

  year_folder = os.path.join(folder, f'{year}')

  # filename of the SLP file for the year
  fn = os.path.join(year_folder, f'slp_{year}.nc')
  out_fn = os.path.join(out_folder, f'slp.{year}.nc')
 
  # opening data for the given year
  ds = xr.open_dataset(fn)

  ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'})

  # TODO: if lon has negative values, I have to rotate the array
  # check if there are any negative values in the longitude array, if so, we have to rotate the arrays
  lon = ds['lon']
  if (np.any(lon < 0)): 
    roll_amount = int(np.sum(lon<0))
    ds['msl'] = ds.msl.roll(lon=roll_amount, roll_coords=True)
    ds['lon'] = ds.lon.roll(lon=roll_amount, roll_coords=True)
    tmp_lon = ds.lon.values
    tmp_lon[tmp_lon < 0] += 360
    attrs = ds.lon.attrs
    ds['lon'] = tmp_lon
    for key in attrs: 
      ds.lon.attrs[key] = attrs[key]

  # renaming variable from 'msl' to 'slp'
  ds = ds.rename({'msl': 'slp'})

  # converting the 'time' variable to hours since start of year
  len_time = len(ds.time)
  ds['time'] = np.asarray(np.arange(0, len_time*6, 6), dtype=np.int)
  ds.time.attrs['delta_t'] = '0000-00-00 06:00:00'
  ds.time.attrs['units'] = 'hours since %d-01-01 00:00:00'%(year)
  ds.time.attrs['calendar'] = 'proleptic_gregorian'

  # converting slp values to mb from Pa
  ds['slp'] = ds.slp/100.
  ds.slp.attrs['units'] = 'mb'

  # saving data to output file 
  ds.to_netcdf(out_fn)

  print('Done converting to %d.'%(year))
