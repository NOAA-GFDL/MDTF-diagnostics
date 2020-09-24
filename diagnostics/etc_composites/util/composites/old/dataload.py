import numpy as np 
from netCDF4 import Dataset
import os
import pdb
import scipy.io as sio
from datetime import date
import math
import multiprocessing as mp
from joblib import Parallel, delayed
# import get_model_data as gmd

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import defines
import re

import xarray

from numpy.core.records import fromarrays

############## CREATING NETCDF FILES FOR EACH TRACK
def write_netcdf(i_track, select_year, var_name, model_name, hemis):

  out_folder = os.path.join(defines.out_folder, '%s/%s/%d'%(model_name, var_name, select_year))

  # out_folder = os.path.join(defines.out_folder, )

  if (not os.path.exists(out_folder)):
    os.makedirs(out_folder)

  out_file = os.path.join(out_folder, 'track_%s_%s_%s_%d_%d.nc'%(model_name, var_name, hemis, select_year, i_track['UIDsingle'])) 

  track_len = i_track['fulllon'].shape[0]
  gridlen = i_track['data'].shape[1]
  gridleny = i_track['data'].shape[2]

  ncid = Dataset(out_file, 'w')
  # creating dimensions
  ncid.createDimension('track_len', track_len)
  ncid.createDimension('boxlen_x', gridlen)
  ncid.createDimension('boxlen_y', gridleny)
  ncid.createDimension('single', 1)

  # 1d variables
  uidsingle_id = ncid.createVariable('UIDsingle', np.int, ('single',))
  date1_id = ncid.createVariable('date1', np.float, ('single',))
  mon_mode_id = ncid.createVariable('mon_mode', np.int, ('single',))
  yr_mode_id = ncid.createVariable('yr_mode', np.int, ('single',))

  # 2d variables
  uid_id = ncid.createVariable('UID', np.int, ('track_len', ))
  cid_id = ncid.createVariable('CID', np.int, ('track_len', ))
  fulllon_id = ncid.createVariable('fulllon', np.float, ('track_len', ))
  fulllat_id = ncid.createVariable('fulllat', np.float, ('track_len', ))
  fullslp_id = ncid.createVariable('fullslp', np.int, ('track_len', ))
  fulldate_id = ncid.createVariable('fulldate', np.float, ('track_len', ))
  fullyr_id = ncid.createVariable('fullyr', np.int, ('track_len', ))
  fullmon_id = ncid.createVariable('fullmon', np.int, ('track_len', ))
  fullday_id = ncid.createVariable('fullday', np.int, ('track_len', ))
  # fullhr_id = ncid.createVariable('fullhr', np.int, ('track_len', ))
  flag_id = ncid.createVariable('flag', np.int, ('track_len', ))

  # 3d variables
  latgrid_id = ncid.createVariable('latgrid', np.float, ('track_len', 'boxlen_x', 'boxlen_y'))
  longrid_id = ncid.createVariable('longrid', np.float, ('track_len', 'boxlen_x', 'boxlen_y'))
  lm_id = ncid.createVariable('lm', np.float, ('track_len', 'boxlen_x', 'boxlen_y'))
  topo_id = ncid.createVariable('topo', np.float, ('track_len', 'boxlen_x', 'boxlen_y'))
  data_id = ncid.createVariable('data', np.float, ('track_len', 'boxlen_x', 'boxlen_y'))
  
  uidsingle_id[:] = i_track['UIDsingle']
  date1_id[:] = i_track['date1']
  mon_mode_id[:] = i_track['mon_mode']
  yr_mode_id[:] = i_track['yr_mode']
  
  uid_id[:] = i_track['UID']
  cid_id[:] = i_track['CID']
  fulllon_id[:] = i_track['fulllon']
  fulllat_id[:] = i_track['fulllat']
  fullslp_id[:] = i_track['fullslp']
  fulldate_id[:] = i_track['fulldate']
  fullyr_id[:] = i_track['fullyr']
  fullmon_id[:] = i_track['fullmon']
  fullday_id[:] = i_track['fullday']
  # fullhr_id[:] = i_track['fullhr']
  flag_id[:] = i_track['flag']

  latgrid_id[:] = i_track['latgrid']
  longrid_id[:] = i_track['longrid']
  data_id[:] = i_track['data']
  topo_id[:] = i_track['topo']
  lm_id[:] = i_track['lm']

  ncid.close()

################# GRABING DATA FROM THE DATA LOADED FOR ALL THE CYCLONES
# def process_track(track, boxlen, box_grid_lat, box_grid_lon, lat_grid, lon_grid, lat_grid_search, lon_grid_search, lat_grid_extend, lon_grid_extend, topo_extend, lm_extend, full_date, var_name, model_name, var_data, select_year, track_loop):
def process_track(in_dict):
  ''' Grabbing data from the data loaded for all the cyclones. '''

  track = in_dict['track']
  boxlen = in_dict['boxlen']
  box_grid_lat = in_dict['box_grid_lat']
  box_grid_lon = in_dict['box_grid_lon']
  lat_grid = in_dict['lat_grid']
  lon_grid = in_dict['lon_grid']
  lon_grid_search = in_dict['lon_grid_search']
  lat_grid_search = in_dict['lat_grid_search']
  lat_grid_extend = in_dict['lat_grid_extend']
  lon_grid_extend = in_dict['lon_grid_extend']
  topo_extend = in_dict['topo_extend']
  lm_extend = in_dict['lm_extend']
  full_date = in_dict['full_date']
  var_name = in_dict['var_name']
  model_name = in_dict['model_name']
  var_data = in_dict['var_data']
  select_year = in_dict['select_year']
  track_loop = in_dict['track_loop']
  hemis = in_dict['hemis']

  # getting the size of the track
  track_size = track['fulldate'].shape[0]
   
  # # creating an empty array for the extracted data
  # var_track = np.zeros((track_size, box_grid_lon.shape[0], box_grid_lat.shape[0]))*np.nan
  # topo_track = np.zeros((track_size, box_grid_lon.shape[0], box_grid_lat.shape[0]))*np.nan
  # lm_track = np.zeros((track_size, box_grid_lon.shape[0], box_grid_lat.shape[0]))*np.nan
  # lat_track = np.zeros((track_size, box_grid_lon.shape[0], box_grid_lat.shape[0]))*np.nan
  # lon_track = np.zeros((track_size, box_grid_lon.shape[0], box_grid_lat.shape[0]))*np.nan
  
  # creating empty array for the extracted data, but here I have to flip the box
  # so that we save the values correctly, in netcdf
  var_track = np.zeros((track_size, box_grid_lat.shape[0], box_grid_lon.shape[0]))*np.nan
  topo_track = np.zeros((track_size, box_grid_lat.shape[0], box_grid_lon.shape[0]))*np.nan
  lm_track = np.zeros((track_size, box_grid_lat.shape[0], box_grid_lon.shape[0]))*np.nan
  lat_track = np.zeros((track_size, box_grid_lat.shape[0], box_grid_lon.shape[0]))*np.nan
  lon_track = np.zeros((track_size, box_grid_lat.shape[0], box_grid_lon.shape[0]))*np.nan

  # looping through each of the cyclones in the track
  for cyc_loop in range(0, track_size):
    cyc_center_lon = track['fulllon'][cyc_loop][0]
    cyc_center_lat = track['fulllat'][cyc_loop][0]
    cyc_fulldate = track['fulldate'][cyc_loop][0]

    # get the matching time index for the time of the cyclone
    time_ind_bool = (cyc_fulldate == full_date)

    # if the time is not found, then we raise an error
    if (not np.any(time_ind_bool)):
      continue
      # raise Exception('dataload.py: Timestep not found in model full_date!')

    # getting the index of the matching full_date for the cyclone time step
    time_ind = np.where(time_ind_bool)[0][0]

    # extract the timestep for the data variable
    var_time_step = var_data[:, :, time_ind]
    var_extend = extend_var(var_time_step, boxlen)

    # finding the cordinate of the center lat and lon in the grid 
    dist = compute_dist_from_cdt(lon_grid_search, lat_grid_search, cyc_center_lon, cyc_center_lat) 
    dist_ind = np.nanargmin(dist)
    dist_ind_x, dist_ind_y = np.unravel_index(dist_ind, lat_grid_search.shape)

    # getting the x and y indexes to extract information
    xmin = dist_ind_x + box_grid_lon[0]
    xmax = dist_ind_x + box_grid_lon[-1] + 1
    ymin = dist_ind_y + box_grid_lat[0]
    ymax = dist_ind_y + box_grid_lat[-1] + 1

    var_extract = var_extend[xmin:xmax, ymin:ymax]
    topo_extract = topo_extend[xmin:xmax, ymin:ymax]
    lm_extract = lm_extend[xmin:xmax, ymin:ymax]
    lon_extract = lon_grid_extend[xmin:xmax, ymin:ymax]
    lat_extract = lat_grid_extend[xmin:xmax, ymin:ymax]
  
    # have to transpose to make the orientation into lon x lat 
    var_track[cyc_loop, :, :] = var_extract.T
    topo_track[cyc_loop, :, :] = topo_extract.T
    lm_track[cyc_loop, :, :] = lm_extract.T
    lat_track[cyc_loop, :, :] = lat_extract.T
    lon_track[cyc_loop, :, :] = lon_extract.T
    
  # for each track create a netcdf file
  temp_dict = {'UID': np.asarray(np.squeeze(track['UID']), dtype=int), \
    'UIDsingle':np.squeeze(track['UIDsingle']), \
    'CID':np.squeeze(track['CID']), \
    'fulllon':np.squeeze(track['fulllon']), \
    'fulllat':np.squeeze(track['fulllat']), \
    'fullslp':np.squeeze(track['fullslp']), \
    'flag':np.squeeze(track['flag']), \
    'fulldate':np.squeeze(track['fulldate']), \
    'date1':np.squeeze(track['date1']), \
    'fullyr':np.squeeze(track['fullyr']), \
    'fullmon':np.squeeze(track['fullmon']), \
    'fullday':np.squeeze(track['fullday']), \
    # 'fullhr':np.squeeze(track['fullhr']), \
    'mon_mode':np.squeeze(track['mon_mode']), \
    'yr_mode':np.squeeze(track['yr_mode']), \
    'data': np.asarray(var_track, dtype=float), \
    'topo': np.asarray(topo_track, dtype=float), \
    'lm': np.asarray(lm_track, dtype=float), \
    'latgrid': np.asarray(lat_track, dtype=float), \
    'longrid': np.asarray(lon_track, dtype=float), \
    }
  
  write_netcdf(temp_dict, select_year, var_name, model_name, hemis)

  # print ('%d - %d'%(select_year, track_loop))

############ Grabbing the data from the variable around a 45 degree box
def grab_data(cyc, in_boxlen, var_data, full_date, reflon, reflat, var_name, topo, lm, select_year, hemis):
  ''' Grabbing the data from the variable around a 45 degree box. '''

  model_name = defines.model_name
  boxlen = max(in_boxlen)

  box_grid_lat = np.arange(np.ceil(-in_boxlen[1]/2), np.ceil(in_boxlen[1]/2), dtype=int)
  box_grid_lon = np.arange(np.ceil(-in_boxlen[0]/2), np.ceil(in_boxlen[0]/2), dtype=int)
  
  # create cdt grid from the reference lat and lon values
  lat_grid, lon_grid = np.meshgrid(reflat, reflon)
  
  # extend lat and lon grids with nan values, used for searching
  lat_grid_search = extend_nan(lat_grid, boxlen)
  lon_grid_search = extend_nan(lon_grid, boxlen)

  # extend the lat and lon for grabbing the data
  lat_grid_extend = extend_var(lat_grid, boxlen)
  lon_grid_extend = extend_lon(lon_grid, boxlen)

  # extending the topographic and land mask grids
  topo_extend = extend_var(topo, boxlen)
  lm_extend = extend_var(lm, boxlen)

  # looping through all the tracks

  # # parallel processing
  # num_cores = mp.cpu_count()
  temp_list = [{'track': track, 'boxlen': boxlen, 'box_grid_lat': box_grid_lat, 'box_grid_lon': box_grid_lon, \
      'lat_grid': lat_grid, 'lon_grid': lon_grid, 'lat_grid_search': lat_grid_search, \
      'lon_grid_search': lon_grid_search, 'lon_grid_extend': lon_grid_extend, \
      'lat_grid_extend': lat_grid_extend, 'topo_extend': topo_extend, 'lm_extend': lm_extend, \
      'full_date': full_date, 'var_name': var_name, 'model_name': model_name, \
      'var_data': var_data, 'select_year': select_year, 'track_loop': track_loop, 'hemis': hemis} \
      for track_loop, track in enumerate(cyc)]

  # # Parallel processing
  # pool = mp.Pool(processes=num_cores)
  # pool.map(process_track, temp_list)

  if (defines.num_cores == 1):
    print ('\tSerial Processing of Tracks!')
    # Serial Processing 
    for i, i_list in enumerate(temp_list): 
      print(f'{i} of {len(temp_list)}')
      process_track(i_list)
  else:
    print ('\tParallel Processing of Tracks using %d cores!'%(defines.num_cores))
    # Parallel processing
    pool = mp.Pool(processes=defines.num_cores)
    pool.map(process_track, temp_list)

  return 


############## 2d array manupilation, extend_var, extend_lon, extend_nan
def extend_var(var, boxlen):
  '''
  Extend the variable data on both sides of the longitude and pad up and down with nans
  '''

  boxlen = int(boxlen)

  # extract the size of the input variable
  lon_size = var.shape[0]
  lat_size = var.shape[1]  + boxlen*2

  # extend the variable in both directions by boxlen
  var_new = np.zeros((lon_size*3, lat_size))*np.nan
  var_new[lon_size:lon_size*2,boxlen:lat_size-boxlen] = var

  var_new[0:lon_size,boxlen:lat_size-boxlen] = var
  var_new[lon_size*2:lon_size*3,boxlen:lat_size-boxlen] = var

  return var_new

def extend_lon(var, boxlen):
  '''
  Extend the logitude on both sides of the longitude by +/- 360 values and pad up and down with nans
  '''

  boxlen = int(boxlen)

  # extract the size of the input variable
  lon_size = var.shape[0]
  lat_size = var.shape[1]  + boxlen*2

  # extend the variable in both directions by boxlen
  var_new = np.zeros((lon_size*3, lat_size))*np.nan
  var_new[lon_size:lon_size*2,boxlen:lat_size-boxlen] = var;

  # padding both sides by lon values upto -720 to 720
  # temp_var = var.copy()
  # temp_var[temp_var > 180.] = temp_var[temp_var > 180.] - 360. 

  var_new[0:lon_size,boxlen:lat_size-boxlen] = var - 360
  var_new[lon_size*2:lon_size*3,boxlen:lat_size-boxlen] = var + 360

  return var_new

def extend_nan(var, boxlen):
  '''
  Extend all the variables on both sides (lon and lat) by nan values
  '''

  boxlen = int(boxlen)

  # extract the size of the input variable
  lon_size = var.shape[0]
  lat_size = var.shape[1]  + boxlen*2

  # extend the variable in both directions by boxlen
  var_new = np.zeros((lon_size*3, lat_size))*np.nan
  var_new[lon_size:lon_size*2,boxlen:lat_size-boxlen] = var;

  # var_new[0:lon_size,boxlen:lat_size-boxlen] = var
  # var_new[lon_size*2:lon_size*3,boxlen:lat_size-boxlen] = var

  return var_new

################## LOADING MODEL DATA FOR VARIABLE NAME
def load_model_var(var_name_ind, select_year, flip_lon_flag, flip_lon_val):
  '''
  Function to load in the model data for the given variable name. 
  '''

  # if (model_name == 'erai'):
  #   var_data, full_date = gmd.get_erai(var_name, select_year)
  #   var_data = np.moveaxis(var_data, [0, 1, 2], [2, 1, 0])
  # elif (model_name == 'merra2'):
  #   var_data, full_date = gmd.get_merra2(var_name, select_year)
  #   var_data = np.moveaxis(var_data, [0, 1, 2], [2, 1, 0])

  var_data, full_date = get_model_data(var_name_ind, select_year)
  var_data = np.moveaxis(var_data, [0, 1, 2], [2, 1, 0])

  if (flip_lon_flag): 
    var_data = np.roll(var_data, flip_lon_val, axis=0)
  
  return var_data, full_date

########################### TOPOGRAPHIC INFORMATION LOADING 
def load_topo_lm():
  '''
  Load in the model topographic information. 
  '''
  ## Topography file

  ncid = Dataset(defines.topo_lm_file, 'r')
  topo = ncid.variables['topo'][:]
  lm = ncid.variables['lm'][:]
  ncid.close()

  return topo, lm

########################### CO-ORDINATE INFORMATION LOADING 
def load_model_cdt(select_year, var_name):
  '''
  Load sample model co-ordinate data (lat/lon) for the given year. 
  Return the reference longitude, latitude
  Here we don't care if the data has to be flipped or not, we assume all data is pre-processed
  '''

  model_file = os.path.join(defines.)
  
  try:
    ncid = Dataset(model_file, 'r')
  except Exception as e:
    print (str(e))
    raise Exception ('Error reading file {:s}'.format(model_file))

  reflat = ncid.variables['lat'][:]
  reflon = ncid.variables['lon'][:]
  ncid.close()

  if (np.any(reflon > 180)):
    flip_lon_flag = True
    flip_lon_val = np.int(np.floor(reflon.shape[0]/2.))
    reflon =  np.roll(reflon, flip_lon_val, axis=0)

  reflon[reflon < 0] = reflon[reflon < 0] + 360.

  return reflon, reflat, flip_lon_flag, flip_lon_val

################# COMPUTING THE DISTACNE GIVEN THE LAT AND LON GRID
def compute_dist_from_cdt(lon, lat, centerLon, centerLat):

    # km per degree value
    mean_radius_earth = 6371

    # Haversine function to find distances between lat and lon
    lat1 = lat * math.pi / 180; 
    lat2 = centerLat * math.pi / 180; 
    
    lon1 = lon * math.pi / 180; 
    lon2 = centerLon * math.pi / 180; 
    
    # convert dx and dy to radians as well
    dLat = lat1 - lat2
    dLon = lon1 - lon2

    R = mean_radius_earth

    # computing distance in X direction
    a = np.sin(dLat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2)**2
    c = np.arctan2(np.sqrt(a), np.sqrt(1-a)); 
    dist = 2 * R * c; 

    return dist


################# READING IN DATA FROM THE MODELS
################# READING IN MODEL DATA AS PER THE VARIABLE NAME
def get_model_data(var_name_ind, select_year):
  '''
  Read in MERRA-2 data from the netcdf files
  '''
  # model_pre_folder = in_folder
  # model_file = os.path.join(model_pre_folder, '%s_%d.nc'%(model_name, select_year))
  model_file = file_format_parser(defines.vardata_file_format, defines.var_names[var_name_ind], select_year)
  model_var_name = defines.model_var_names[var_name_ind]

  if (not model_var_name):
    model_var_name = defines.var_names[var_name_ind]
  
  ncid = Dataset(model_file, 'r')
  var_data = ncid.variables[model_var_name][:]
  ncid.close()

  full_date = get_model_date(select_year, defines.model_calendar_type)

  return var_data, full_date

######################### CREATE MODEL TIME 
def get_model_date(select_year, calendar_type):
  if (calendar_type == 'julian'):
    # have to add 366 to get matlab datenum
    full_date = np.arange(date.toordinal(date(select_year, 1, 1))+366., date.toordinal(date(select_year, 12, 31))+366.+1., .25)
  
  return full_date

######################## PARSE THE FOLDER OUTPUT LOCATION
def file_format_parser(file_format, var_name, select_year):

  # sanity check for close and open brackets
  open_ind = [match.start() for match in re.finditer('{', file_format)]
  close_ind = [match.start() for match in re.finditer('}', file_format)]

  # model_var_name = defines.model_var_names[defines.var_names.index(var_name)]

  if (len(open_ind) != len(close_ind)):
    raise Exception('String has unbalanced {} !')

  len_string = len(file_format)
  i = 0
  while i < len_string:
  
    # find the starting location of {
    if (file_format[i] == '{'):
      open_ind = i

    # find the starting location of }
    if (file_format[i] == '}'):
      close_ind = i
      parse_string = file_format[open_ind:close_ind+1]

      caps = False
      if (parse_string.isupper()):
        caps = True

      if (parse_string.lower() == '{var_name}'):
        if (caps):
          file_format = file_format.replace(parse_string, var_name.upper())
        else:
          file_format = file_format.replace(parse_string, var_name)
      elif (parse_string.lower() == '{model_name}'):
        if (caps):
          file_format = file_format.replace(parse_string, model_name.upper())
        else:
          file_format = file_format.replace(parse_string, model_name)
      elif (parse_string.lower() == '{year}'):
          file_format = file_format.replace(parse_string, '%d'%(select_year))
      
      len_string = len(file_format)
      i = open_ind
    
    i+=1 

  return file_format

   
      
    


