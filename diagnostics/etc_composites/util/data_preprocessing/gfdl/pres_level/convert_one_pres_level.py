#!/usr/bin/env python
import xarray as xr
import numpy as np 
import matplotlib.pyplot as plt 
import pdb, os
import datetime as dt
import tqdm 

# ------------------- Functions
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

# ------------------ Main Code  
inFolder = '/mnt/drive3/gfdl/6HRLY/KLEV/'
out_folder = '/localdrive/drive6/gfdl/converts/'

# read in model level, convert it to pressure level 

# var = 'v'
# var_map = {'v': 'va'}

# var = 'u'
# var_map = {'u': 'ua'}

var = 'cls'
var_map = {'cls': 'cls'}

inFile = os.path.join(inFolder, f'atmos.2008010100-2012123123.{var_map[var]}.nc')
ds = xr.open_dataset(os.path.join(inFile))

# getting the necessary values
lat = np.float32(ds.lat.values)
lon = np.float32(ds.lon.values)
in_actual_time = ds.time.values
pfull = ds.pfull.values
phalf = ds.phalf.values

# pressure levels of era-interim
# pres_level = [1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
# pres_level = [100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
pres_level = [850]

# converting netcdf input time to time in datetime
start_year = 2008
in_time = get_time_julian(start_year, len(in_actual_time))
  
# in_time picks the later part of the time bounds, so we have to shift the time by 6 hours back to get the start time
in_years = np.array([i.year for i in in_time])
in_hours = np.array([get_hours_since_year(i) for i in in_time])

for year in range(np.nanmin(in_years), np.nanmax(in_years)+1):

  print(f'{year}...')
  # getting the time index
  time_ind = (in_years == year)
  time = in_hours[time_ind]
  in_data = ds[var_map[var]].isel(time=time_ind)

  out_data = np.empty((in_data.shape[0], len(pres_level), in_data.shape[2], in_data.shape[3]))

  print('Time Step:')
  for tstep in tqdm(range(len(time)), total=len(time)):
    # print(f'\t{tstep}')
    tmp = in_data.isel(time=tstep).interp(pfull=pres_level, method='linear', assume_sorted=True, kwargs={'fill_value': 'extrapolate'})
    out_data[tstep, :, :, :] = tmp

  # if only one pressure_level we have to name it accordingly
  if (len(pres_level) == 1): 
    out_var = f'{var}{pres_level[0]}'
  else: 
    out_var = var

  out_data = xr.DataArray(out_data, coords={'time': time, 'lev': pres_level, 'lat': lat, 'lon': lon}, dims=['time', 'lev', 'lat', 'lon'])
  out_ds = xr.Dataset({out_var: out_data})

  for key in ds[var_map[var]].attrs.keys():
    out_ds[out_var].attrs[key] = ds[var_map[var]].attrs[key]


  out_ds['time'].attrs['units'] = f'hours since {year}-01-01 00:00:00'
  out_ds['time'].attrs['calendar'] = 'standard'
  
  out_ds['lat'].attrs['units'] = 'degrees North'
  out_ds['lon'].attrs['units'] = 'degrees East'

  if (len(pres_level) == 1): 
    out_ds = out_ds.isel(lev=0)

  out_file = os.path.join(out_folder, f'{out_var}.{year}.nc')
  out_ds.to_netcdf(out_file)

