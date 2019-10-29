#/usr/bin/env python
import eulerian_storm_track as est
import numpy as np 
from netCDF4 import Dataset
import plotter
import os

#### Main Code #####


### Prep the data initially for the Eulerian Storm Track Code
year = [2011, 2012]
era_folder = '/mnt/drive5/ERAINTERIM/V10/'

time = []
data = np.array([])
tot_time = 0
for i_year in range(year[0], year[1]+1): 
  era_file = os.path.join(era_folder, 'V10_%d.nc'%(i_year)) 

  nc = Dataset(era_file, 'r')
  nc.set_always_mask(False)
  in_lat = nc.variables['lat'][:]
  in_time = nc.variables['time'][:]
  in_lon = nc.variables['lon'][:]
  in_data = nc.variables['var166'][:]
  nc.close()

  # stacking slp arrays
  if (data.size == 0):
    data = in_data
  else:
    data = np.concatenate((data, in_data), axis=0)

  # creating the time arrays
  time.extend(list(tot_time + np.arange(0, in_data.shape[0]*6, 6)))
  tot_time += in_data.shape[0]*6
  print ('Reading in year %d [%d]!'%(i_year, tot_time))

# creating the lat and lon in grid format
lonGrid, latGrid = np.meshgrid(in_lon, in_lat)

# converting hourly data into daily, and converting Pascals to hectoPascals
data_daily, time_daily = est.six_hrly_to_daily(data, year[0], time)

# getting the daily difference X(t+1) - X(t)
diff = est.daily_diff(data_daily)

# getting the all year standard deviation average
std_dev, time_std = est.std_dev(diff, year[0], time_daily, time_period='all')
#std_dev, time_std = est.std_dev(diff, year[0], time_daily, time_period='yearly')
# std_dev, time_std = est.std_dev(diff, year[0], time_daily, time_period='seasonally', season='djf')

plotter.plot(lonGrid, latGrid, std_dev)
# plotter.plot(lonGrid, latGrid, std_dev[0, :, :])
