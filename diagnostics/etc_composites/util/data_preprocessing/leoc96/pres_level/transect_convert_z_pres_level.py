#!/usr/bin/env python
import xarray as xr
import numpy as np 
import matplotlib.pyplot as plt 
import pdb, os
import datetime as dt
from tqdm import tqdm

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

# pres_level = [1259.587, 1475.301, 1967.105, 2593.302, 3383.406, 4371.602, 5597.103, 7104.46, 8943.828, 11171.16, 13848.3, 17043.08, 20829.14, 25284.63, 30479.23, 36429.14, 43018.47, 49953.28, 56837.25, 63328.34, 69232.12, 74481.81, 79078.43, 83054.55, 86460.09, 89352.98, 91793.68, 93841.98, 95553.41, 96977.73, 98158.33, 99128.46, 100000]
# pres_level = [i/100. for i in pres_level]

pres_level = [0.0171052512649617, 0.0380102383882785, 0.0686551589322532, 0.11361803458164, 0.178752860685895, 0.274388498599214, 0.414767919596273, 0.618455975354221, 0.910066120368144, 1.32216980330045, 1.89729594414021, 2.6902576168577, 3.77081383122845, 5.2266642666333, 7.16675888193994, 9.72489105230714, 13.0635264807004, 17.3778029011962, 22.8996206774882, 29.9017286729427, 38.7016977185877, 49.6656638058622, 63.2117171006669, 79.8128107819713, 99.9990654267351, 124.359351881068, 153.542046894013, 188.254870627357, 229.263219871856, 277.364765336414, 333.155174318448, 396.36295331148, 464.941771304376, 535.059070791703, 602.621201211844, 664.880933508635, 720.696844719115, 769.874744124755, 812.629155924972, 849.397132370557, 880.739861311195, 907.254984317899, 929.55399628899, 948.220904866301, 963.782672356715, 976.707393399323, 987.394531409156, 996.109949282544]

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
  # out_data = np.empty((time_len, len(pres_level), 180, 288))
  out_data = np.empty((time_len, 32, 180, 288))

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

  for tstep in tqdm(range(len(ds_time)), total=len(ds_time)):
    pres_level = ds[var_map[var]].lev.values
    # tmp = ds[var_map[var]].isel(time=tstep).interp(lev=pres_level, method='linear', assume_sorted=True, kwargs={'fill_value': 'extrapolate'})
    tmp = ds[var_map[var]].isel(time=tstep)
    tmp = tmp * var_scale[var]

    # finding the mean between 2 levels
    tmp_out = np.zeros((tmp.shape[0]-1, tmp.shape[1], tmp.shape[2]))
    for ilev in range(tmp.shape[0]-1):
      tmp_out[ilev] = (tmp[ilev,:,:] + tmp[ilev,:,:])/2.

    out_data[tstep+start_time_ind, :, :, :] = tmp_out
    time_array[tstep+start_time_ind] = (tstep+start_time_ind)*6

  ds.close()

  # saving output
  out_data = xr.DataArray(out_data, coords={'time': time_array, 'lev': range(0, 32), 'lat': lat, 'lon': lon}, dims=['time', 'lev', 'lat', 'lon'])
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

