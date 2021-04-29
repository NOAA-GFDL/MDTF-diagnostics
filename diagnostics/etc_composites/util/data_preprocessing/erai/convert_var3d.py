#!/usr/bin/env python

import numpy as np 
import xarray as xr
import os

folder = '/localdrive/drive6/erai/dl/' 
out_folder = '/localdrive/drive6/erai/converts/'

year_list = [1979, 1979]
var_list = {\
    # 'u850': {'fn': 'u850', 'varname': 'u'}, \
    # 'v850': {'fn': 'v850', 'varname': 'v'}, \
    # 'z850': {'fn': 'hgt850', 'varname': 'z'}, \
    # 'ps':   {'fn': 'ps', 'varname': 'sp'}, \
    # 't':    {'fn': 't', 'varname': 't'}, \
    # 'z':    {'fn': 'hgt3d', 'varname': 'z'}, \
    # 'u':    {'fn': 'u3d', 'varname': 'u'}, \
    # 'v':    {'fn': 'v3d', 'varname': 'v'}, \
    'w':    {'fn': 'w3d', 'varname': 'w'}, \
    }

for year in range(year_list[0], year_list[1]+1):

  print(f'Converting to {year}...')
  year_folder = os.path.join(folder, f'{year}')

  for var in var_list.keys():
    print(f'\t{var.upper()}')

    # filename of the SLP file for the year
    fn = os.path.join(year_folder, f'{var_list[var]["fn"]}_{year}.nc')
    out_fn = os.path.join(out_folder, f'{var}.{year}.nc')
   
    # opening data for the given year
    ds = xr.open_dataset(fn)
    ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'})

    if ('level' in ds.coords.keys()):
      ds = ds.rename({'level': 'lev'})

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
    ds = ds.rename({var_list[var]['varname'] : var})


    # converting the 'time' variable to hours since start of year
    len_time = len(ds.time)
    ds['time'] = np.asarray(np.arange(0, len_time*6, 6), dtype=np.int)
    ds.time.attrs['delta_t'] = '0000-00-00 06:00:00'
    ds.time.attrs['units'] = 'hours since %d-01-01 00:00:00'%(year)
    ds.time.attrs['calendar'] = 'proleptic_gregorian'

    # converting slp values to mb from Pa
    if (var == 'z') | (var == 'z850'): 
      ds[var] = ds[var]/9.8/1000
      ds[var].attrs['units'] = 'km'

    # saving data to output file 
    ds.to_netcdf(out_fn)

  break
