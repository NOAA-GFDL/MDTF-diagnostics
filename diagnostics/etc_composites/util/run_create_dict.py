#!/usr/bin/python
import scipy.io as sio
import numpy as np
import os
import pandas as pd

# # temp stuff
# os.environ['DATADIR'] = '/localdrive/drive10/jj/mdtf/inputdata/model/ERA5.ALL.DEG15.001'
# # os.environ['WK_DIR'] = '/localdrive/drive10/jj/mdtf/wkdir/MDTF_ERA5.ALL.DEG15.001_1950_1950/etc_composites'
# os.environ['WK_DIR'] = '/localdrive/drive10/jj/mdtf/wkdir/MDTF_ERA5.ALL.DEG15.001_1950_2019/etc_composites'
# os.environ['POD_HOME'] = '/localdrive/drive10/jj/mdtf/MDTF-diagnostics/diagnostics/etc_composites'
# os.environ['topo_file'] = '/localdrive/drive10/jj/mdtf/inputdata/model/ERA5.ALL.DEG15.001/topo.nc'
# os.environ['obs_lat_distrib_file'] = '/localdrive/drive10/jj/mdtf/inputdata/obs_data/etc_composites/erai_lat_distrib.pkl'
# os.environ['FIRSTYR'] = '1950'
# os.environ['LASTYR'] = '2019'
# os.environ['RUN_MCMS'] = 'True'
# os.environ['USE_EXTERNAL_TRACKS'] = 'True'

import defines
import xarray as xr
import composites

from scipy.stats import mode
from datetime import date
from numpy.core.records import fromarrays


def read_in_txt_file(start_year, end_year):
  ''' Code used to read in a text file with the tracks. 
  The tracks file must have 8 columns separated by white spaces. 
  The columns are as follows: 
  1. yy - year
  2. mm - month
  3. dd - day 
  4. hh - hour
  5. lat - latitude of cyclone center (provided as integer value, (90 - lat)*100)
  6. lon - longitude of cyclone center (provided as integer value, 100*lon)
  7. slp - SLP at cyclone center 
  8. uid - unique identifier for each track
  lat & lon is provided in this format to avoid decimal places and to avoid negative values 
  lon is provided from 0 to 360, hence no need to add any value
  '''

  # the input track file has to be provided as track_data.txt in the "inputdata/{model}/6hr" directory, under the model name
  # the tracks are normally tracked on 6 hourly data 
  # track_file = f"{os.environ['DATADIR']}/6hr/track_output.txt"
  track_file = defines.track_file

  main_df = pd.read_csv(track_file, sep='\s+') 

  # extracting only the certain columns I need from the main dataframe
  df = main_df.iloc[:, [0, 1, 2, 3, 4, 5, 6, 7]].copy()
  df = df.copy()

  # naming the dataframe columns
  df.columns = ['yy', 'mm', 'dd', 'hh', 'lat', 'lon', 'slp', 'usi']
  df.lat = 90 - df.lat/100.
  df.lon = df.lon/100.

  return df
  
def read_in_MCMS_txt_file(base_dir, in_model, start_year, end_year):

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
if (not os.path.exists(base_dir)):
  os.makedirs(base_dir)

# reading in txt file with the tracks for all the years
# This depends on which tracker I am using 
# If the MCMS tracker is run then read in the MCMS output
if (os.environ['USE_EXTERNAL_TRACKS'] == 'True'): 
  df = read_in_txt_file(start_year, end_year)
elif (os.environ['USE_EXTERNAL_TRACKS'] == 'False'): 
  df = read_in_MCMS_txt_file(base_dir, in_model, start_year, end_year)

# Reading in the topographic information
# also reading in the lat/lon values for the topo file
ds = xr.open_dataset(defines.topo_file)
reflat = ds.lat.values
reflon = ds.lon.values
reflon, reflat = np.meshgrid(reflon, reflat)
if ('time' in ds.coords.keys()): 
  lm = ds.lsm.isel(time=0).values
else: 
  lm = ds.lsm.values
lm = (lm > defines.thresh_landsea_lsm)

# loop through all the years and create the datacycs
for i_year in range(start_year, end_year+1):

  # get the usi values of the tracks that are for the given year
  uni_usi = df.usi[df['yy'] == i_year].unique()
 
  # create empty arrays
  temp_uid = []
  temp_uidsingle = []
  temp_fulllon = []
  temp_fulllat = []
  temp_fullslp = []
  
  temp_fulldate = []
  temp_date1 = []
  temp_fullyr = []
  temp_fullmon = []
  temp_fullday = []
  temp_fullhr = []
  temp_mon_mode = []
  temp_yr_mode = []
  
  temp_lm_flag = []
  temp_warm_flag = []
  temp_obs_flag = []

  # loop through all the unique usi values that have a cyclone for the given i_year
  for i_ind, i_usi in enumerate(uni_usi): 

    # getting the index that match each usi value
    usi_ind = df.index[df.usi == i_usi].tolist()
    
    # check if the total track time extends atleast 36 hours
    # we have to account for the detla_t in this case
    # because we run for hourly and six-hourly
    # hh = np.asarray(df.hh[usi_ind],dtype=int)
    # delta_t = 6.0
    # if (len(hh)*delta_t) < 36: 
    #   continue
    
    # creating numpy arrays from dataframe for processing full_date
    yy = np.asarray(df.yy[usi_ind],dtype=int)
    mm = np.asarray(df.mm[usi_ind],dtype=int)
    dd = np.asarray(df.dd[usi_ind],dtype=int)
    hh = np.asarray(df.hh[usi_ind],dtype=int)
   
    # creating full_date 
    # matlab datenum format
    full_date = [date.toordinal(date(i_yy, i_mm, i_dd))+366.+i_hh/24. for i_yy, i_mm, i_dd, i_hh in zip(yy, mm, dd, hh)]

    # check if the total track time extends atleast 36 hours
    # we have to account for delta_t to have the capability to run the tracker for hourly or 6-hourly data
    delta_t = (full_date[1] - full_date[0])*24
    if (len(hh)*delta_t) < 36: 
      continue
  
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
    temp_fulllon.append(np.asarray(df.lon[usi_ind], dtype=float))
    temp_fulllat.append(np.asarray(df.lat[usi_ind], dtype=float))
    temp_fullslp.append(np.asarray(df.slp[usi_ind], dtype=float))
    
    # creating flags that will be used in the POD
    # sh_ocean_warm called the obs_flag
    # land/ocean called the lm_flag
    lm_flag = np.zeros((len(df.lat[usi_ind])), dtype=int)
    warm_flag = np.zeros((len(df.lat[usi_ind])), dtype=int)
    obs_flag = np.zeros((len(df.lat[usi_ind])), dtype=int)
    for i, (ilon, ilat, imm) in enumerate(zip(df.lon[usi_ind], df.lat[usi_ind], mm)):
      dist_grid = composites.compute_dist_from_cdt(reflat, reflon, ilat, ilon)
      c_ind = np.nanargmin(dist_grid)
      cx, cy = np.unravel_index(c_ind, dist_grid.shape)
      lm_flag[i] = int(lm[cx, cy])
      if ((imm == 11) | (imm == 12) | (imm == 1) | (imm == 2) | (imm == 3)):
        warm_flag[i] = 1
      if (ilat < 0) & (warm_flag[i] == 1) & (lm_flag[i] == 0):
        obs_flag[i] = 1
        

    temp_lm_flag.append(np.asarray(lm_flag, dtype=int))
    temp_warm_flag.append(np.asarray(warm_flag, dtype=int))
    temp_obs_flag.append(np.asarray(obs_flag, dtype=int))


    # print ('%d in %d'%(i_ind, uni_usi.shape[0]))

  # creating a record to save mat files, like the one jimmy creates using matlab
  out_cyc = fromarrays([temp_uid, temp_uidsingle, temp_fulllon, temp_fulllat, temp_fullslp, temp_fulldate, temp_date1, temp_fullyr, temp_fullmon, temp_fullday, temp_fullhr, temp_mon_mode, temp_yr_mode, temp_lm_flag, temp_warm_flag, temp_obs_flag], names=['UID', 'UIDsingle', 'fulllon', 'fulllat', 'fullslp', 'fulldate', 'date1', 'fullyr', 'fullmon', 'fullday', 'fullhr', 'mon_mode', 'yr_mode', 'lm_flag', 'warm_flag', 'obs_flag'])

  # saving mat files for each year
  out_mat_file = os.path.join(defines.main_folder_location, '%s/read_%s/%s_%d.mat'%(in_model, in_model, in_model, i_year))
  sio.savemat(out_mat_file, {'cyc':out_cyc})

  print(f'Created .mat file for {i_year}.')
