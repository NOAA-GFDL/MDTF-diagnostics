#!/usr/bin/env python
import xarray as xr
import numpy as np
import datetime as dt

import os, pdb

# var_list = ['pr']
# var_map = {'pr': 'pr'}
# var_units = {'pr': 'mm/day'}
# var_convert = {'pr': 84600}
# var_longname = {'pr': 'Total precipitation rate'}

# var_list = ['ps']
# var_map = {'ps': 'ps'}
# var_units = {'ps': 'Pa'}
# var_convert = {'ps': 1.}
# var_longname = {'ps': 'Surface Pressure'}

# var_list = ['prw']
# var_map = {'prw': 'PRW'}
# var_units = {'prw': 'mm/day'}
# var_convert = {'prw': 1.}
# var_longname = {'prw': 'Water Vapor Path'}

# var_list = ['clt']
# var_map = {'clt': 'clt'}
# var_units = {'clt': '%'}
# var_convert = {'clt': 1.}
# var_longname = {'clt': 'Total Cloud Fraction'}

var_list = ['pr', 'ps', 'prw', 'clt']
var_map = {'pr': 'pr', 'ps': 'ps', 'prw': 'PRW', 'clt': 'clt'}
var_units = {'pr': 'mm/day', 'ps': 'Pa', 'prw': 'mm/day', 'clt': '%'}
var_convert = {'pr': 86400, 'ps': 1., 'prw': 1., 'clt': 1.}
var_longname = {'pr': 'Total Precipitation Rate', 'ps': 'Surface Pressure', 'prw': 'Water Vapor Path', 'clt': 'Total Cloud Fraction'}

def get_days_in_month(year, month):
  leap_year = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]
  non_leap_year = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
  if (np.mod(year, 4) == 0): 
    return leap_year[month-1]
  else:
    return non_leap_year[month-1]

def get_hours_since_year(time):
  hours = (get_days_in_month(time.year, time.month))*24 + (time.day-1)*(24) + time.hour
  return hours

def get_time_julian(start_year, len_time):
  time = np.array([dt.datetime(start_year, 1, 1) + dt.timedelta(hours=i*6) for i in range(len_time)])
  return time

out_folder = '/localdrive/drive6/gfdl/converts'
for var in var_list: 
  print(f'Variable {var.upper()}')
  var_file = f'/mnt/drive3/gfdl/6HRLY/SURF/atmos.2008010100-2012123123.{var_map[var]}.nc'
  start_year = 2008

  ds = xr.open_dataset(var_file)

  # getting the values from the netcdf value
  in_lat = ds.lat.values
  in_lon = ds.lon.values
  in_actual_time = ds.time.values
  in_time = get_time_julian(start_year, len(in_actual_time))

  # in_time picks the later part of the time bounds, so we have to shift the time by 6 hours back to get the start time
  in_years = np.array([i.year for i in in_time])
  in_hours = np.array([get_hours_since_year(i) for i in in_time])

  if np.any(in_lon < 0):
    print('Have to shift the lon!')
    sys.exit(0)

  for year in range(np.min(in_years), np.max(in_years)+1):

    # output file name
    out_file = os.path.join(out_folder, f'{var}.{year}.nc')

    # setting the output values
    lon = in_lon
    lat = in_lat

    # converting lon/lat mid values to lon/lat left edges
    # lon = lon - (lon[1]-lon[0])/2.
    # lat = lat - (lat[1]-lat[0])/2.
    lon = np.float32(lon)
    lat = np.float32(lat)

    # getting the time index
    time_ind = (in_years == year)
    time = in_hours[time_ind]
    var_val = ds[var_map[var]].isel(time=time_ind)
    
    out_var = xr.DataArray(var_val.values*var_convert[var], coords={'time': time, 'lat': lat, 'lon': lon}, dims=['time', 'lat', 'lon'])
    out_ds = xr.Dataset({var: out_var})

    # setting the units
    out_ds.time.attrs['calendar'] = 'standard'
    out_ds.time.attrs['units'] = f'hours since {year}-01-01 00:00:00'
    out_ds.time.attrs['delta_t'] = '0000-00-00 06:00:00'

    # cdt atrributes
    out_ds.lat.attrs['units'] = 'degrees North'
    out_ds.lon.attrs['units'] = 'degrees East'

    # slp attributes
    out_ds[var].attrs['units'] = var_units[var]
    out_ds[var].attrs['long_name'] = var_longname[var] 

    print(f'Completed {year}')
    out_ds.to_netcdf(out_file)
    out_ds.close()

  ds.close()
