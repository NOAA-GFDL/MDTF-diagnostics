# Importing standard libraries
import numpy as np 
from netCDF4 import Dataset
import os
import eulerian_storm_track_util as est
import datetime as dt

# # Debuggin
# import pdb
# import matplotlib.pyplot as plt
# plt.style.use(['classic', 'dark_background'])


def six_hrly_to_daily(data, time):
  '''
  Data has to be provided as six hourly timesteps, in a numpy array format (time x lon x lat), lon and lat can be changed, but keep track of it 
  the time variable has to be given in six hourly increments, since the start_year [0, 6, 12, 18, 24, 30, 36, 42, 48]

  Output:
  numpy array in the format time x lon x lat (lon, lat depends on your input)
  output time dimension size will be the number of days provided in the time array
  '''
  # convert time to numpy array 
  time = np.asarray(time)

  # check if time array and data time dimension is the same
  if (len(time) != data.shape[0]):
    raise Exception ("Time dimensions don't match!")

  # converting six hrly timesteps into the days
  time_in_days = np.asarray((time//24) + 1, dtype=int)
  
  min_time = min(time_in_days)
  max_time = max(time_in_days)
  time_range = range(min_time, max_time+1)

  out_time = np.empty((len(time_range),))*np.nan
  out_data = np.empty((len(time_range), data.shape[1], data.shape[2]))*np.nan

  # looping through the days and creating the output array
  for ind, day in enumerate(time_range):
    out_data[ind, :, :] = np.nanmean(data[time_in_days == day, :, :], axis=0)
    out_time[ind] = day

  return out_data, out_time

def yearly_std_dev(data, start_year, time):
  '''
  Data input should be in the format (time, lat, lon)
  We will calculate the std_dev for the given time_ind, the time_ind has to be a logical array of the size of the time dimension 
  '''
  # convert time as numpy array
  time = np.asarray(time)

  jf = np.zeros((2,data.shape[1], data.shape[2]))
  mam = np.zeros((2,data.shape[1], data.shape[2]))
  jja = np.zeros((2,data.shape[1], data.shape[2]))
  son = np.zeros((2,data.shape[1], data.shape[2]))
  dec = np.zeros((2,data.shape[1], data.shape[2]))

  # getting the datetime values for the time index
  dates_month=[]
  dates_year=[]
  for i_time in time: 
    temp_time = dt.datetime(start_year, 1, 1) + dt.timedelta(days=np.float(i_time)-1)
    dates_month.append(temp_time.month)
    dates_year.append(temp_time.year)

  dates_month = np.asarray(dates_month)
  dates_year = np.asarray(dates_year)

  time_ind = (dates_month == 1) | (dates_month == 2) 
  jf[0, :, :] = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  jf[1, :, :] = np.count_nonzero(~np.isnan(data[time_ind, :, :]), axis=0)
  
  time_ind = (dates_month == 3) | (dates_month == 4) | (dates_month == 5)
  eddy_sq_sum = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  mam[0, :, :] = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  mam[1, :, :] = np.count_nonzero(~np.isnan(data[time_ind, :, :]), axis=0)

  time_ind = (dates_month == 6) | (dates_month == 7) | (dates_month == 8)
  eddy_sq_sum = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  jja[0, :, :] = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  jja[1, :, :] = np.count_nonzero(~np.isnan(data[time_ind, :, :]), axis=0)

  time_ind = (dates_month == 9) | (dates_month == 10) | (dates_month == 11)
  eddy_sq_sum = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  son[0, :, :] = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  son[1, :, :] = np.count_nonzero(~np.isnan(data[time_ind, :, :]), axis=0)

  time_ind = (dates_month == 12)
  eddy_sq_sum = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  dec[0, :, :] = np.nansum(data[time_ind, :, :] ** 2, axis=0)
  dec[1, :, :] = np.count_nonzero(~np.isnan(data[time_ind, :, :]), axis=0)

  return jf, mam, jja, son, dec


def plot(data):
  plt.pcolormesh(data); 
  plt.colorbar(); plt.show()


################################################################################
########## MAIN CODE TO CREATE THE OBS DATA FROM LOCAL SERVER ##################
################################################################################

### Prep the data initially for the Eulerian Storm Track Code

# ERA-Interim
reanalysis = 'era5'
year = [1979, 2015]
obs_folder = '/mnt/drive5/ERAINTERIM/V850/'

# ERA-5
reanalysis = 'era5'
year = [1979, 2018]
obs_folder = '/mnt/drive5/era5/data/V850/'

out_year = []
out_jf = []
out_mam = []
out_jja = []
out_son = []
out_dec = []

for i_year in range(year[0], year[1]+1): 

  if (reanalysis == 'erai'):
    # get filename
    obs_file = os.path.join(obs_folder, 'V0850_%d.nc'%(i_year)) 

    # read in the data
    nc = Dataset(obs_file, 'r')
    nc.set_always_mask(False)
    in_lat = nc.variables['lat'][:]
    in_time = nc.variables['time'][:]
    in_lon = nc.variables['lon'][:]
    in_data = np.squeeze(nc.variables['var132'][:])
    nc.close()
  elif (reanalysis == 'era5'):
    # get filename
    obs_file = os.path.join(obs_folder, 'V850_%d.nc'%(i_year)) 

    # read in the data
    nc = Dataset(obs_file, 'r')
    nc.set_always_mask(False)
    in_lat = nc.variables['latitude'][:]
    in_time = nc.variables['time'][:]
    in_lon = nc.variables['longitude'][:]
    in_data = np.squeeze(nc.variables['v'][:])
    nc.close()

    start_hr = (dt.datetime(1900, 1, 1, 0, 0) + dt.timedelta(hours=float(in_time[0]))).hour
    in_time = start_hr + np.arange(0, in_time.size*6, 6)

  # roll the arrays, so that the lons are from 0 to 360 
  if (np.any(in_lon < 0)): 
    lon_shift_ind = np.argwhere(in_lon == 0)[0][0]
    in_lon[in_lon < 0] += 360
    in_lon = np.roll(in_lon, lon_shift_ind)
    in_data = np.roll(in_data, lon_shift_ind, axis=2)

  # convert the V10 arrays to six_hourly, and get the dates
  data, time = six_hrly_to_daily(in_data, in_time)
  # date_time = [dt.datetime(i_year, 1, 1) + dt.timedelta(days=i_time-1) for i_time in time]
  # dates = np.asarray([[date.year, date.month] for date in date_time])

  eddies = est.transient_eddies(data)

  jf, mam, jja, son, dec  = yearly_std_dev(eddies, i_year, time)
  out_jf.append(jf)
  out_mam.append(mam)
  out_jja.append(jja)
  out_son.append(son)
  out_dec.append(dec)
  out_year.append(i_year)
  print(i_year)

out_jf = np.asarray(out_jf)
out_mam = np.asarray(out_mam)
out_jja = np.asarray(out_jja)
out_son = np.asarray(out_son)
out_dec = np.asarray(out_dec)
out_year = np.asarray(out_year)

# creating the lat and lon in grid format
lonGrid, latGrid = np.meshgrid(in_lon, in_lat)

nc = Dataset('%s.nc'%(reanalysis), 'w')
nc.set_fill_off()

nc.createDimension('lat', lonGrid.shape[0])
nc.createDimension('lon', lonGrid.shape[1])
nc.createDimension('time', len(out_year))
nc.createDimension('cnts', 2)

lat_id = nc.createVariable('lat', 'float32', ('lat',))
lon_id = nc.createVariable('lon', 'float32', ('lon',))
time_id = nc.createVariable('time', 'int32', ('time',))

jf_id = nc.createVariable('jf_sq_eddy', 'float32', ('time','cnts', 'lat', 'lon'))
mam_id = nc.createVariable('mam_sq_eddy', 'float32', ('time','cnts', 'lat', 'lon'))
jja_id = nc.createVariable('jja_sq_eddy', 'float32', ('time','cnts', 'lat', 'lon'))
son_id = nc.createVariable('son_sq_eddy', 'float32', ('time','cnts', 'lat', 'lon'))
dec_id = nc.createVariable('dec_sq_eddy', 'float32', ('time','cnts', 'lat', 'lon'))

lat_id.setncatts({'long_name': u'Latitude', 'units':'degrees_North'})
lon_id.setncatts({'long_name': u'Longitude', 'units':'degrees_East'})

jf_id.setncatts({'long_name': u'Sum and Cnts of Eddies Squared for Jan, Feb [sum = (time, 1, lat, lon), cnt = (time, 2, lat, lon)]', 'units':'(m/s)^2'})
mam_id.setncatts({'long_name': u'Sum and Cnts of Eddies Squared for Mar, Apr, May [sum = (time, 1, lat, lon), cnt = (time, 2, lat, lon)]', 'units':'(m/s)^2'})
jja_id.setncatts({'long_name': u'Sum and Cnts of Eddies Squared for Jun, Jul, Aug [sum = (time, 1, lat, lon), cnt = (time, 2, lat, lon)]', 'units':'(m/s)^2'})
son_id.setncatts({'long_name': u'Sum and Cnts of Eddies Squared for Sep, Oct, Nov [sum = (time, 1, lat, lon), cnt = (time, 2, lat, lon)]', 'units':'(m/s)^2'})
dec_id.setncatts({'long_name': u'Sum and Cnts of Eddies Squared for Dec [sum = (time, 1, lat, lon), cnt = (time, 2, lat, lon)]', 'units':'(m/s)^2'})

lat_id[:] = in_lat
lon_id[:] = in_lon
time_id[:] = out_year

jf_id[:] = out_jf
mam_id[:] = out_mam
jja_id[:] = out_jja
son_id[:] = out_son
dec_id[:] = out_dec

nc.close()

os.system('rsync --progress ./%s.nc ../../../inputdata/obs_data/eulerian_storm_track/'%(reanalysis))

