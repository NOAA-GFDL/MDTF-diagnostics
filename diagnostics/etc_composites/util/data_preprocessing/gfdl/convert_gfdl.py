import xarray as xr
import numpy as np
import datetime as dt

import os, pdb

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
slp_file = '/mnt/drive3/gfdl/6HRLY/SURF/atmos.2008010100-2012123123.slp.nc'
start_year = 2008

ds = xr.open_dataset(slp_file)

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
  out_file = os.path.join(out_folder, f'slp.{year}.nc')

  # setting the output values
  lon = in_lon
  lat = in_lat

  # # converting lon/lat mid values to lon/lat left edges
  lon = np.float32(lon)
  lat = np.float32(lat)

  # getting the time index
  time_ind = (in_years == year)
  time = in_hours[time_ind]
  slp = ds.slp.isel(time=time_ind)
  
  out_slp = xr.DataArray(slp.values, coords={'time': time, 'lat': lat, 'lon': lon}, dims=['time', 'lat', 'lon'])
  out_ds = xr.Dataset({'slp': out_slp})

  # setting the units
  out_ds.time.attrs['calendar'] = 'standard'
  out_ds.time.attrs['units'] = f'hours since {year}-01-01 00:00:00'
  out_ds.time.attrs['delta_t'] = '0000-00-00 06:00:00'

  # cdt atrributes
  out_ds.lat.attrs['units'] = 'degrees North'
  out_ds.lon.attrs['units'] = 'degrees East'

  # slp attributes
  out_ds.slp.attrs['units'] = 'mb'
  out_ds.slp.attrs['long_name'] = 'sea_level_pressure'

  print(f'Completed {year}')
  out_ds.to_netcdf(out_file)
  out_ds.close()

