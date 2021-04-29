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
inFolder = '/mnt/drive6/LEOC96/level/atmos_level/ts/6hr/1yr/'
out_folder = '/localdrive/drive6/leo/converts/'

# Years 
year_list = [2008, 2012]

# # variables to convert in 3d format
# var_list = ['rh', 'clc', 'cls', 'w', 't']
# var_map = {'rh':'hur', 'clc':'clc', 'cls':'cls', 'w':'wap', 'clw':'clw', 'clws':'clws', 't':'ta'}

var_list = ['u', 'v']
var_map = {'u':'ua', 'v': 'va'}

for var in var_list:
  print(f'{var.upper()}')

  for year in range(year_list[0], year_list[1]+1):
    
    print(f'\t... {year}')

    # reading in var file
    inFile = os.path.join(inFolder, f'atmos_level.{year}010100-{year}123123.{var_map[var]}.nc')
    ds = xr.open_dataset(os.path.join(inFile))

    # getting the necessary values
    lat = np.float32(ds.lat.values)
    lon = np.float32(ds.lon.values)
    in_actual_time = ds.time.values
    pfull = ds.pfull.values

    # pressure levels of era-interim
    # pres_level = [1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]
    pres_level = [100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 775, 800, 825, 850, 875, 900, 925, 950, 975, 1000]

    pres_level = [0.0171052512649617, 0.0380102383882785, 0.0686551589322532, 0.11361803458164, 0.178752860685895, 0.274388498599214, 0.414767919596273, 0.618455975354221, 0.910066120368144, 1.32216980330045, 1.89729594414021, 2.6902576168577, 3.77081383122845, 5.2266642666333, 7.16675888193994, 9.72489105230714, 13.0635264807004, 17.3778029011962, 22.8996206774882, 29.9017286729427, 38.7016977185877, 49.6656638058622, 63.2117171006669, 79.8128107819713, 99.9990654267351, 124.359351881068, 153.542046894013, 188.254870627357, 229.263219871856, 277.364765336414, 333.155174318448, 396.36295331148, 464.941771304376, 535.059070791703, 602.621201211844, 664.880933508635, 720.696844719115, 769.874744124755, 812.629155924972, 849.397132370557, 880.739861311195, 907.254984317899, 929.55399628899, 948.220904866301, 963.782672356715, 976.707393399323, 987.394531409156, 996.109949282544]
    pres_level = pres_level[16:]

    # converting netcdf input time to time in datetime
    in_time = get_time_julian(year, len(in_actual_time))
      
    # in_time picks the later part of the time bounds, so we have to shift the time by 6 hours back to get the start time
    in_years = np.array([i.year for i in in_time])
    in_hours = np.array([get_hours_since_year(i) for i in in_time])

    # getting the time index
    time_ind = (in_years == year)
    time = in_hours[time_ind]
    in_data = ds[var_map[var]].isel(time=time_ind)
    pres_level = in_data.pfull.values[16:]

    out_data = np.empty((in_data.shape[0], len(pres_level), in_data.shape[2], in_data.shape[3]))

    print('Time Step:')
    for tstep in tqdm(range(len(time)), total=len(time)):
      # tmp = in_data.isel(time=tstep).interp(pfull=pres_level, method='linear', assume_sorted=True, kwargs={'fill_value': 'extrapolate'})
      tmp = in_data.isel(time=tstep)
      out_data[tstep, :, :, :] = tmp[16:, :, :]

    out_data = xr.DataArray(out_data, coords={'time': time, 'lev': pres_level, 'lat': lat, 'lon': lon}, dims=['time', 'lev', 'lat', 'lon'])
    out_ds = xr.Dataset({var: out_data})

    for key in ds[var_map[var]].attrs.keys():
      out_ds[var].attrs[key] = ds[var_map[var]].attrs[key]


    out_ds['time'].attrs['units'] = f'hours since {year}-01-01 00:00:00'
    out_ds['time'].attrs['calendar'] = 'standard'
    
    out_ds['lat'].attrs['units'] = 'degrees North'
    out_ds['lon'].attrs['units'] = 'degrees East'

    out_file = os.path.join(out_folder, f'transect_{var}.{year}.nc')
    out_ds.to_netcdf(out_file)

