#!/usr/bin/env python

############# EULERIAN STROM TRACKER ############
############# Necessary Functions ###############
###### Created by: Jeyavinoth Jeyaratnam     ####
###### Created Date: 03/29/2019              ####
###### Last Modified: 01/17/2020             ####
#################################################

# Importing standard libraries
import numpy as np 
import datetime as dt

'''
Tracker Notes: 
  1) Average 6hrly to daily
  2) take x(t+1) - x(t)
  3) for each year, for season, get std_dev
  4) avergae std_dev for all years
'''

def six_hrly_to_daily(data, start_year, time):
  '''
  Data has to be provided as six hourly timesteps, in a numpy array format (time x lon x lat), lon and lat can be changed, but keep track of it 
  the time variable has to be given in six hourly increments, since the start_year [0, 6, 12, 18, 24, 30, 36, 42, 48]
  where start_year is the starting year of the given data

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
  time_in_days = (time//24) + 1
  
  min_time = min(time_in_days)
  max_time = max(time_in_days)
  time_range = range(min_time, max_time+1)

  out_time = np.empty((len(time_range),))*np.nan
  out_data = np.empty((len(time_range), data.shape[1], data.shape[2]))*np.nan

  # looping through the days and creating the output array
  for ind, day in enumerate(time_range):
    out_data[ind, :, :] = np.nansum(data[time_in_days == day, :, :], axis=0)
    out_time[ind] = day

  return out_data, out_time

def daily_diff(daily_data):
  '''
  Data has to be provided as daily_data
  it will compute the difference between the current day and the previous day
  i.e. X(t+1) - X(t), nans for the last index 
  '''
  # pad the right of the array with nan values along the first dimension
  # then extract the values from the 2nd column (index = 1) to the end
  # this will give us a shifted array of daily data, i.e. X(t+1)
  daily_data_shift = np.pad(daily_data, ((0,1), (0,0), (0,0)), mode='constant', constant_values=np.nan)[1:, :, :]

  return daily_data_shift - daily_data # X(t+1) - X(t), with nan values for the last time dimension


def std_dev(data, time_ind):
  '''
  Given data input in the format (time, lat, lon)
  we will calculate the std_dev for the given time_ind, the time_ind has to be a logical array of the size of the time dimension 
  '''
  out_std_dev = np.empty((data.shape[1], data.shape[2]))*np.nan

  # check if any value is true for the selected time, if so then return nan values, else compute standard deviation 
  if np.all(np.invert(time_ind)):
    print ('No time index selected!')
    return (out_std_dev)
  else:
    return np.nanstd(data[time_ind, :, :], axis=0)

def get_time_ind(start_year, time, season='djf'):
  ''' Get the time index for the given season '''

  # convert time as numpy array
  time = np.asarray(time)

  # getting the datetime values for the time index
  dates_month=[]
  dates_year=[]
  for i_time in time: 
    temp_time = dt.datetime(start_year, 1, 1) + dt.timedelta(days=np.float(i_time)-1)
    dates_month.append(temp_time.month)
    dates_year.append(temp_time.year)

  uni_year = sorted(set(dates_year))
  dates_month = np.asarray(dates_month)
  dates_year = np.asarray(dates_year)

  # getting the time index
  if (season == ''):
    raise Exception('Set which season you want to extract!')
  elif (season == 'djf'):
    time_ind = (dates_month == 12) | (dates_month == 1) | (dates_month == 2)
  elif (season == 'mam'):
    time_ind = (dates_month == 3) | (dates_month == 4) | (dates_month == 5)
  elif (season == 'jja'):
    time_ind = (dates_month == 6) | (dates_month == 7) | (dates_month == 8)
  elif (season == 'son'):
    time_ind = (dates_month == 9) | (dates_month == 10) | (dates_month == 11)

  return time_ind

def old_std_dev(data, start_year, time, time_period='yearly', season=''):
  '''
  Data input has to be daily in the format (time, lat, lon)
  start_year has to be the start year of the given array
  if an incomplete data array along the time dimension is provided, then you have to specify the time variable
  time vaiable has to be specified in days, since start_year [1,2,3,4,5,6,7], default=finds the time starting from day 1
  time_period includes 'yearly', 'seasonally', 'all', default='all' means avarage of all years
  if 'byseason' then have to set season variable to be: djf', 'mam', 'jja', 'son'

  Output: 
  returns standard_deviation for the given time_period, and the time array that corresponds to the std_dev output
  out_time is zero for time_period='all'
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

  uni_year = sorted(set(dates_year))
  dates_month = np.asarray(dates_month)
  dates_year = np.asarray(dates_year)

  # getting the time_ind
  if (time_period == 'all'):
    return np.nanstd(data, axis=0), 0
  else:
    # getting the time index
    if (time_period == 'yearly'):
      time_ind = (dates_month > 0)
    elif (time_period == 'seasonally'):
      if (season == ''):
        raise Exception('Set which season you want to extract!')
      elif (season == 'djf'):
        time_ind = (dates_month == 12) | (dates_month == 1) | (dates_month == 2)
      elif (season == 'mam'):
        time_ind = (dates_month == 3) | (dates_month == 4) | (dates_month == 5)
      elif (season == 'jja'):
        time_ind = (dates_month == 6) | (dates_month == 7) | (dates_month == 8)
      elif (season == 'son'):
        time_ind = (dates_month == 9) | (dates_month == 10) | (dates_month == 11)
    else: 
      raise Exception('Error in the time_period set!')

    # initialize output array
    out_time = np.empty((len(uni_year),))*np.nan
    out_std_dev = np.empty((len(uni_year), data.shape[1], data.shape[2]))*np.nan
    
    # for each year we have to get the std_dev data
    for out_ind, year in enumerate(uni_year):

      # setting the time array output
      out_time[out_ind] = year 

      # getting the matching index for the each unique year
      year_ind = (dates_year == year)

      # overlapping with the season index, or all if time_period is yearly
      final_ind = year_ind & time_ind

      # check if any value is true for the selected time, if so then continue, else compute standard deviation 
      if np.all(np.invert(final_ind)):
        print ('Debug: Nothing found!')
        breakpoint()
        continue
      else:
        out_std_dev[out_ind, :, :]  = np.nanstd(data[final_ind, :, :], axis=0)

    return out_std_dev, out_time


