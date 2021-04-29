#!/usr/bin/env python

############# EULERIAN STROM TRACKER ############
###### Created by: Jeyavinoth Jeyaratnam     ####
###### Created Date: 03/29/2019              ####
###### Last Modified: 05/09/2019             ####
#################################################

# Importing standard libraries
import numpy as np 
import datetime as dt
import os
from netCDF4 import Dataset
import warnings

def transient_eddies(daily_data):
  '''
  Data has to be provided as daily_data
  it will compute the difference between the current day and the previous day
  i.e. X(t+1) - X(t), nans for the last index 
  in Booth et al., 2017, vprime = (x(t+1) - x(t))/2. 
  '''
  # pad the right of the array with nan values along the first dimension
  # then extract the values from the 2nd column (index = 1) to the end
  # this will give us a shifted array of daily data, i.e. X(t+1)
  daily_data_shift = np.pad(daily_data, ((0,1), (0,0), (0,0)), mode='constant', constant_values=np.nan)[1:, :, :]

  return (daily_data_shift - daily_data)/2. # X(t+1) - X(t), with nan values for the last time dimension

def model_std_dev(data, start_year, time, season='djf'):
  '''
  Data input should be in the format (time, lat, lon)
  We will calculate the std_dev for the given time_ind, the time_ind has to be a logical array of the size of the time dimension 
  '''
  # convert time as numpy array
  time = np.asarray(time)

  # getting the datetime values for the time index
  dates_month=[]
  dates_year=[]
  for i_time in time: 
    temp_time = dt.datetime(start_year, 1, 1) + dt.timedelta(days=np.float(i_time)-1)
    dates_month.append(temp_time.month)
    dates_year.append(temp_time.year)

  dates_month = np.asarray(dates_month)
  dates_year = np.asarray(dates_year)

  eddy_year = []
  for i_year in range(int(os.environ['FIRSTYR']), int(os.environ['LASTYR'])+1):
    if (season == 'djf'):
      time_ind = ((dates_year == i_year) & (dates_month == 1)) | ((dates_year == i_year) & (dates_month == 2)) | ((dates_year == i_year-1) & (dates_month == 12)) 
    elif (season == 'mam'):
      time_ind = ((dates_year == i_year) & (dates_month == 3)) | ((dates_year == i_year) & (dates_month == 4)) | ((dates_year == i_year) & (dates_month == 5)) 
    elif (season == 'jja'):
      time_ind = ((dates_year == i_year) & (dates_month == 6)) | ((dates_year == i_year) & (dates_month == 7)) | ((dates_year == i_year) & (dates_month == 8)) 
    elif (season == 'son'):
      time_ind = ((dates_year == i_year) & (dates_month == 9)) | ((dates_year == i_year) & (dates_month == 10)) | ((dates_year == i_year) & (dates_month == 11)) 

    with warnings.catch_warnings():
      warnings.simplefilter("ignore", category=RuntimeWarning)
      eddy_season_mean = np.sqrt(np.nanmean(data[time_ind, :, :] ** 2, axis=0))
      eddy_year.append(eddy_season_mean)

  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    eddy_year = np.asarray(eddy_year)
    out_std_dev = np.nanmean(eddy_year, axis=0)
    zonal_mean = np.nanmean(out_std_dev, axis=1)
    zonal_mean[zonal_mean == 0] = np.nan

  # out_sum = np.nansum(eddy_year, axis=0)
  # out_cnt = np.count_nonzero(~np.isnan(eddy_year), axis=0)
  # return out_std_dev, out_sum, out_cnt

  return out_std_dev, zonal_mean

def obs_std_dev(obs_data_file, obs_topo_file):
  '''
  Data input should be in the format (time, lat, lon)
  We will calculate the std_dev for the given time_ind, the time_ind has to be a logical array of the size of the time dimension 
  '''

  nc = Dataset(obs_data_file, 'r')
  nc.set_auto_mask(False)

  in_lat = nc.variables['lat'][:]
  in_lon = nc.variables['lon'][:]
  in_time = nc.variables['time'][:]

  in_jf = nc.variables['jf_sq_eddy'][:]
  in_mam = nc.variables['mam_sq_eddy'][:]
  in_jja = nc.variables['jja_sq_eddy'][:]
  in_son = nc.variables['son_sq_eddy'][:]
  in_dec = nc.variables['dec_sq_eddy'][:]
  
  nc.close()

  # read in the topography information to filter before computing the zonal mean 
  nc = Dataset(obs_topo_file, 'r')
  in_topo = nc.variables['topo'][:]
  nc.close()

  topo_cond = (in_topo > 1000)

  djf_year = []
  mam_year = []
  jja_year = []
  son_year = []

  start_year = int(os.environ['FIRSTYR'])
  end_year = int(os.environ['LASTYR'])

  start_year = max([start_year, min(in_time)])
  end_year = min([end_year, max(in_time)])

  for i_year in range(start_year, end_year+1):

    if not ((i_year == start_year)):
      i_djf = np.squeeze(in_dec[in_time == i_year-1, :, :, :] + in_jf[in_time == i_year, :, :, :])
      i_djf = np.sqrt(i_djf[0, :, :]/i_djf[1, :, :])
      djf_year.append(i_djf)
    
    i_mam = np.squeeze(in_mam[in_time == i_year, :, :, :])
    i_mam = np.sqrt(i_mam[0, :, :]/i_mam[1, :, :])
    mam_year.append(i_mam)

    i_jja = np.squeeze(in_jja[in_time == i_year, :, :, :])
    i_jja = np.sqrt(i_jja[0, :, :]/i_jja[1, :, :])
    jja_year.append(i_jja)
    
    i_son = np.squeeze(in_son[in_time == i_year, :, :, :])
    i_son = np.sqrt(i_son[0, :, :]/i_son[1, :, :])
    son_year.append(i_son)

  djf_year = np.asarray(djf_year)
  djf = np.nanmean(djf_year, axis=0)
  djf[topo_cond] = np.nan
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    zonal_djf = np.nanmean(djf, axis=1)
    zonal_djf[zonal_djf == 0] = np.nan
  
  mam_year = np.asarray(mam_year)
  mam = np.nanmean(mam_year, axis=0)
  mam[topo_cond] = np.nan
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    zonal_mam = np.nanmean(mam, axis=1)
    zonal_mam[zonal_mam == 0] = np.nan
  
  jja_year = np.asarray(jja_year)
  jja = np.nanmean(jja_year, axis=0)
  jja[topo_cond] = np.nan
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    zonal_jja = np.nanmean(jja, axis=1)
    zonal_jja[zonal_jja == 0] = np.nan
  
  son_year = np.asarray(son_year)
  son = np.nanmean(son_year, axis=0)
  son[topo_cond] = np.nan
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    zonal_son = np.nanmean(son, axis=1)
    zonal_son[zonal_son == 0] = np.nan
  
  lonGrid, latGrid = np.meshgrid(in_lon, in_lat)

  zonal_means = {'djf': zonal_djf, 'jja': zonal_jja, 'son': zonal_son, 'mam': zonal_mam, 'lat': in_lat}

  # import matplotlib.pyplot as plt; 
  # plt.style.use(['classic', 'dark_background'])
  # import pdb; pdb.set_trace()

  return latGrid, lonGrid, djf, mam, jja, son, start_year, end_year, zonal_means

