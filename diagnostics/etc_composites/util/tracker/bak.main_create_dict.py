#!/usr/bin/python
import scipy.io as sio
import numpy as np
import os
import pandas as pd
import defines

from scipy.stats import mode
from datetime import date
from numpy.core.records import fromarrays

def read_in_txt_file(base_dir, in_model, start_year, end_year):
  ''' Code used to read in a text file with the tracks. 
  If start_year is the same as end_year then it will read in the text file as
  if it only contains one year of tracks. 
  If start_year is different from end_year it will read it as if the text file 
  has all the years in the same file. 
  '''


  # Read in the cyc file
  if (start_year == end_year):
    in_file = os.path.join(base_dir, 'out_%s_output_%04d.txt'%(in_model, start_year))
  else:
    in_file = os.path.join(base_dir, 'out_%s_output_%04d_%04d.txt'%(in_model, start_year, end_year))

  main_df = pd.read_csv(in_file, sep='\s+') 

  # extracting only the certain columns I need from the main dataframe
  df = main_df.iloc[:, [0, 1, 2, 3, 5, 6, 8, 11, 14, 15]].copy()

  # naming the dataframe columns
  df.columns = ['yy', 'mm', 'dd', 'hh', 'lat', 'lon', 'slp', 'flags', 'csi', 'usi']
  df.lat = 90. - df.lat/100.
  df.lon = df.lon/100.

  return df

########################################
################ Main Code #############
########################################

start_year = defines.over_write_years[0]
end_year = defines.over_write_years[1]

in_model = defines.model
base_dir = os.path.join(defines.main_folder_location, in_model, 'read_%s'%(in_model))

# reading in txt file with the tracks for all the years
df = read_in_txt_file(base_dir, in_model, start_year, end_year)

# loop through all the years and create the datacycs
for i_year in range(start_year, end_year+1):

  # get the usi values of the tracks that are for the given year
  uni_usi = df.usi[df['yy'] == i_year].unique()
 
  # create empty arrays
  temp_uid = []
  temp_uidsingle = []
  temp_cid = []
  temp_fulllon = []
  temp_fulllat = []
  temp_fullslp = []
  temp_flag = []
  
  temp_fulldate = []
  temp_date1 = []
  temp_fullyr = []
  temp_fullmon = []
  temp_fullday = []
  temp_fullhr = []
  temp_mon_mode = []
  temp_yr_mode = []

  # loop through all the unique usi values that have a cyclone for the given i_year
  for i_ind, i_usi in enumerate(uni_usi): 

    # getting the index that match each usi value
    usi_ind = df.index[df.usi == i_usi].tolist()
    
    # check if the total track time extends atleast 36 hours
    # we have to account for the detla_t in this case
    # because we run for hourly and six-hourly
    hh = np.asarray(df.hh[usi_ind],dtype=int)
    delta_t = hh[1] - hh[0]
    if (len(hh)*delta_t) < 36: 
      continue
    
    # creating numpy arrays from dataframe for processing full_date
    yy = np.asarray(df.yy[usi_ind],dtype=int)
    mm = np.asarray(df.mm[usi_ind],dtype=int)
    dd = np.asarray(df.dd[usi_ind],dtype=int)
    hh = np.asarray(df.hh[usi_ind],dtype=int)
   
    # creating full_date 
    # matlab datenum format
    full_date = [date.toordinal(date(i_yy, i_mm, i_dd))+366.+i_hh/24. for i_yy, i_mm, i_dd, i_hh in zip(yy, mm, dd, hh)]
  
    # checking if the mode year is the current year, if not this track will be passed onto the next year or previous year accordingly
    if (mode(yy).mode[0] != i_year):
      continue

    # appending to the temporary list of data variables, to be saved as mat files 
    temp_yr_mode.append(mode(yy).mode[0])
    temp_fulldate.append(full_date)
    temp_date1.append(full_date[0])
    temp_fullyr.append(yy)
    temp_fullmon.append(mm) 
    temp_fullday.append(dd)
    temp_fullhr.append(hh)
    temp_mon_mode.append(mode(mm).mode[0])

    temp_uid.append(np.asarray(df.usi[usi_ind], dtype=float))
    temp_uidsingle.append(np.asarray(df.usi[usi_ind[0]], dtype=float))
    temp_cid.append(np.asarray(df.csi[usi_ind], dtype=float))
    temp_fulllon.append(np.asarray(df.lon[usi_ind], dtype=float))
    temp_fulllat.append(np.asarray(df.lat[usi_ind], dtype=float))
    temp_fullslp.append(np.asarray(df.slp[usi_ind], dtype=float))
    temp_flag.append(np.asarray(df.flags[usi_ind], dtype=int))

    # print ('%d in %d'%(i_ind, uni_usi.shape[0]))

  # creating a record to save mat files, like the one jimmy creates using matlab
  out_cyc = fromarrays([temp_uid, temp_uidsingle, temp_cid, temp_fulllon, temp_fulllat, temp_fullslp, temp_flag, temp_fulldate, temp_date1, temp_fullyr, temp_fullmon, temp_fullday, temp_fullhr, temp_mon_mode, temp_yr_mode], names=['UID', 'UIDsingle', 'CID', 'fulllon', 'fulllat', 'fullslp', 'flag', 'fulldate', 'date1', 'fullyr', 'fullmon', 'fullday', 'fullhr', 'mon_mode', 'yr_mode'])

  # saving mat files for each year
  out_mat_file = os.path.join(defines.main_folder_location, '%s/read_%s/%s_%d.mat'%(in_model, in_model, in_model, i_year))
  sio.savemat(out_mat_file, {'cyc':out_cyc})

  print(f'Created .mat file for {i_year}.')
