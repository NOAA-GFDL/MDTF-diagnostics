#!/usr/bin/env python
import xarray as xr
import numpy as np 
import matplotlib.pyplot as plt 
import pdb, os
import datetime as dt

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
in_folder = '/mnt/drive6/LEOC96/Z/'
out_folder = '/localdrive/drive6/leo/converts/'

# read in model level, convert it to pressure level 
var = 'z'
var_map = {'z': 'zg'}
var_scale = {'z': 1./1000.}

# pressure levels of era-interim
# pres_level = [1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
pres_level = [100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]

pres_level = [2.16404256133345, 5.84530754043837, 10.7450801553507, 17.1065372595328, 25.1138051289766, 35.2211968195201, 48.1379036870309, 64.560183540236, 85.1144822187467, 110.419626793719, 141.092610422464, 177.729387604925, 220.89239709789, 271.066623628003, 328.516336882098, 392.785272564752, 461.94726249906, 532.465906646758, 600.430867020261, 663.107382784874, 719.307118080772, 768.814283964814, 811.846868750618, 848.836020639326, 880.346139043136, 906.995722281721, 929.394582518357, 948.128523228285, 963.732570169141, 976.687397176329, 987.39245780434, 996.109949282544]

# converting netcdf input time to time in datetime
year_list = [2008, 2012]

delta_t = 6

for year in range(2008, 2013):

  print(f'{year}...')
  out_ds = {}

  # year reset variables
  start_time_ind = 0

  time = []
  num_days = (dt.datetime(year, 12, 31) - dt.datetime(year, 1, 1)).days + 1
  time_len = int(num_days*24/delta_t)
  time_array = np.empty((time_len, )) *np.nan
  out_data = np.empty((time_len, len(pres_level), 180, 288))

  inFile = os.path.join(in_folder, f'zg_leo96mdtf_{year}.nc')
  ds = xr.open_dataset(os.path.join(inFile))
  lat = np.float32(ds.lat.values)
  lon = np.float32(ds.lon.values)

  # converting ds.level values into hPa, instead of Pa
  ds.lev.values = ds.lev.values/100.
  ds['lev'].attrs['units'] = 'hPa'

  ds_time = np.arange(0, len(ds.time)*delta_t, delta_t)
  if (len(time) == 0): 
    new_time = ds_time.tolist()
    time.extend(new_time)
    start_time_ind = 0
  else:
    new_time = (ds_time + max(time) + delta_t).tolist()
    start_time_ind = len(time) 
    time.extend(new_time)

  for tstep in range(len(ds_time)):
    print(f'\t{tstep+start_time_ind}')
    tmp = ds[var_map[var]].isel(time=tstep).interp(lev=pres_level, method='linear', assume_sorted=True, kwargs={'fill_value': 'extrapolate'})
    tmp = tmp * var_scale[var]
    out_data[tstep+start_time_ind, :, :, :] = tmp
    time_array[tstep+start_time_ind] = (tstep+start_time_ind)*6

  ds.close()

  # saving output
  out_data = xr.DataArray(out_data, coords={'time': time_array, 'lev': pres_level, 'lat': lat, 'lon': lon}, dims=['time', 'lev', 'lat', 'lon'])
  out_ds = xr.Dataset({var: out_data})

  for key in ds[var_map[var]].attrs.keys():
    out_ds[var].attrs[key] = ds[var_map[var]].attrs[key]

  out_ds[var].attrs['units'] = 'km'


  out_ds['time'].attrs['units'] = f'hours since {year}-01-01 00:00:00'
  out_ds['time'].attrs['calendar'] = 'standard'

  out_ds['lat'].attrs['units'] = 'degrees North'
  out_ds['lon'].attrs['units'] = 'degrees East'
  out_ds['lev'].attrs['units'] = 'hPa'

  out_file = os.path.join(out_folder, f'transect_{var}.{year}.nc')
  out_ds.to_netcdf(out_file)

