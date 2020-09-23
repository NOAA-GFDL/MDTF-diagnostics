#!/usr/bin/env python

# supressing warnings, because there are a lot of NaN value warnings 
# comment lines below when debugging
# only supress in production
import sys
if not sys.warnoptions:
  import warnings
  warnings.simplefilter("ignore")

import numpy as np 
import front_detection as fd
from scipy.ndimage import label, generate_binary_structure
import glob, os
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import datetime as dt
import xarray as xr

import cartopy

import defines
import pandas as pd
import reader

## JJ Debugging flags
import pdb, time
from tqdm import tqdm
debug = False
debug = True
# stop_at_date = dt.datetime(2008, 1, 9)
stop_at_date = None

# ----------------------- FUNCTIONS --------------------------

def extend_lon(var):
  '''
  Extend the logitude on both sides of the longitude by +/- 360 values and pad up and down with nans
  '''

  # extract the size of the input variable
  boxlen = var.shape[1]
  lat_size = var.shape[0]
  lon_size = var.shape[1]

  # extend the variable in both directions by boxlen
  var_new = np.zeros((lat_size, lon_size*3))*np.nan

  var_new[:, 0:lon_size] = var - 360
  var_new[:, lon_size:lon_size*2] = var
  var_new[:, lon_size*2:lon_size*3] = var + 360

  return var_new

def extend_lat(var):
  '''
  Extend the logitude on both sides of the longitude by +/- 360 values and pad up and down with nans
  '''

  # extract the size of the input variable
  boxlen = var.shape[1]
  lat_size = var.shape[0]
  lon_size = var.shape[1]

  # extend the variable in both directions by boxlen
  var_new = np.zeros((lat_size, lon_size*3))*np.nan

  var_new[:, 0:lon_size] = var
  var_new[:, lon_size:lon_size*2] = var
  var_new[:, lon_size*2:lon_size*3] = var

  return var_new

def get_plus_mask(fit, lon, lat):
  lat_prime = lon*fit[0] + fit[1]
  mask = (lat_prime >= lat)
  return mask

def dextend_dist(lat, lon, dist, lon_size, flag=False):

  lat = lat[:, lon_size:lon_size*2]
  lon = lon[:, lon_size:lon_size*2]

  dist_neg = np.copy(dist)
  dist_neg[dist_neg > 0] = np.nan
  dist_3d = np.empty((3, lat.shape[0], lon_size))
  dist_3d[0, :, :] = dist_neg[:, 0:lon_size]
  dist_3d[1, :, :] = dist_neg[:, lon_size:lon_size*2]
  dist_3d[2, :, :] = dist_neg[:, lon_size*2:]
  # dist_neg = np.nanmax(dist_3d, axis=0)
  if (flag):
    dist_neg = np.nanmin(dist_3d, axis=0)
  else:
    dist_neg = dist_3d[1, :, :]
  
  dist_pos = np.copy(dist)
  dist_pos[dist_pos < 0] = np.nan
  dist_3d = np.empty((3, lat.shape[0], lon_size))
  dist_3d[0, :, :] = dist_pos[:, 0:lon_size]
  dist_3d[1, :, :] = dist_pos[:, lon_size:lon_size*2]
  dist_3d[2, :, :] = dist_pos[:, lon_size*2:]

  if (flag):
    dist_pos = np.nanmin(dist_3d, axis=0)
  else:
    dist_pos = dist_3d[1, :, :]

  dist = np.copy(dist_pos)
  dist[np.isnan(dist_pos)] = dist_neg[np.isnan(dist_pos)]

  # # for the southern hemisphere, I have to copy the negative values to overwrite the positive values
  # # why do I have to do this? 
  # SH = (lat < 0)
  # dist[~np.isnan(dist_neg ) & SH] = dist_neg[~np.isnan(dist_neg ) & SH]

  return lat, lon, dist

def get_dist_from_front_old(fit, lon, lat, indexes, f_type='cf', debug_append=''):

  # extend lat and lon on both sides
  lon_size = lat.shape[1]
  lon = extend_lon(lon)
  lat = extend_lat(lat)

  # get the distance from the straight line

  front_slope = fit[0]
  front_intercept = fit[1]

  # getting the slope of the perpendicular line
  perp_slope = -1/front_slope

  # getting the intercept using the cdt lon and lat values
  perp_intercept = lat - perp_slope*lon

  # point of intercept of perpendicular & front line 
  tmp_lon = (front_intercept - perp_intercept)/(perp_slope - front_slope)
  tmp_lat = perp_slope * tmp_lon + perp_intercept

  # getting distance
  # dist = np.sqrt((lat - tmp_lat)**2 + (lon - tmp_lon)**2)*np.cos(lat*np.pi/180.)*111.12
  # dist = fd.dist_between_grids(lat, lon, tmp_lat, tmp_lon)
  # dist = fd.compute_dist_from_cdt(lat, lon, tmp_lat, tmp_lon)
  dist = fd.dist_transect(lat, lon, tmp_lat, tmp_lon)

  left_edge_lat = np.abs(front_slope * (0) + front_intercept)
  right_edge_lat = np.abs(front_slope * (360) + front_intercept)
  if (left_edge_lat > 90) | (right_edge_lat > 90): 
    dextend_flag = True
  else:
    dextend_flag = False

  # screening out any values greater than 1500
  dist_orig = np.copy(dist) # testing JJ
  dist[dist > 1500] = np.nan

  # check if cf or wf, and make -/+ depending on that
  if (f_type == 'cf'):
    neg_mask = (lon < tmp_lon)
  elif (f_type == 'wf'):
    neg_mask = (np.abs(lat) < np.abs(tmp_lat))

  # making the distances +/- depending on mask
  dist[neg_mask] *= -1

  dist[np.abs(lat) > 75] = np.nan

  # loop through all my cold front points, 
  # and get the min and max values, i.e. places I need to chop off my front line
  if (f_type == 'cf'):
    mask_greater = np.ones(lat.shape)
    mask_less = np.ones(lon.shape)
    for idx in indexes: 
      ps = perp_slope
      pi = perp_intercept[idx[0], idx[1]+lon_size]
      
      i_tmp_lat = lon*ps + pi
      mask_greater[i_tmp_lat < lat] = 0.
      mask_less[i_tmp_lat > lat] = 0.
    
    dist[mask_less == 1] = np.nan
    dist[mask_greater == 1] = np.nan
  elif (f_type == 'wf'):
    mask_greater = np.ones(lat.shape)
    mask_less = np.ones(lon.shape)
    for idx in indexes: 
      ps = perp_slope
      pi = perp_intercept[idx[0], idx[1]+lon_size]
      
      # i_tmp_lat = lon*ps + pi
      # mask_greater[i_tmp_lat < lat] = 0.
      # mask_less[i_tmp_lat > lat] = 0.
      
      i_tmp_lon = (lat-pi)/ps
      mask_greater[i_tmp_lon < lon] = 0.
      mask_less[i_tmp_lon > lon] = 0.
      
    dist[mask_less == 1] = np.nan
    dist[mask_greater == 1] = np.nan
 
  # dextending the distance 3d 
  lat, lon, dist = dextend_dist(lat, lon, dist, lon_size, flag=dextend_flag)
  
  return dist

def linidx_take(val_arr,z_indices):
  # code i got from stackoverflow to get the value given z_indices

  # Get number of columns and rows in values array
  _,nR,nC = val_arr.shape

  # Get linear indices and thus extract elements with np.take
  idx = nC*nR*z_indices + nC*np.arange(nR)[:,None] + np.arange(nC)
  return np.take(val_arr,idx) # Or val_arr.ravel()[idx]
  # return val_arr.ravel()[idx]

def get_sign_grid(lat, lon, i_lat, i_lon, f_type, dist_thres=2000): 
  sign_grid = np.zeros(lon.shape)
  if (f_type == 'cf'): 
    # east is +ve, west is -ve
    sign_grid[lon >= i_lon] = 1
    sign_grid[lon < i_lon] = -1

    # if the front point is at the edges of 0 - 360, then we have to set the signs to overlap
    lon_360 = np.all(lon > 0)
    if (i_lon > 300) & (lon_360):  # if the front point is > 300 & lon is in the range 0 - 360
      sign_grid[lon < 60] = 1
    if (i_lon < 60) & (lon_360):  # if the front point is < 60 and lon is in the range of 0 - 360
      sign_grid[lon > 300] = -1

    # if the front point is at the edges of -180 to 180 then we have to set the signs to overlap
    lon_180 = np.any(lon < 0)
    if (i_lon > 120) & (lon_180):  # if the front point is < 120 and lon is in the range of -180 to 180
      sign_grid[lon < -120] = 1
    if (i_lon < -120) & (lon_180):  # if the front point is < 120 and lon is in the range of -180 to 180
      sign_grid[lon > 120] = -1

  elif (f_type == 'wf'): 
    # poleward is +ve, equatorward is -ve
    ind = np.abs(lat) >= np.abs(i_lat)
    sign_grid[ind] = 1
    sign_grid[np.invert(ind)] = -1

  return sign_grid

def get_dist_from_front(f_lon, f_lat, lon, lat, f_type): 

  # loop through all the front points
  # get the distance from the point to all the points on the grid
  dist_grid = np.zeros((len(f_lon), lon.shape[0], lon.shape[1]))
  sign_grid = np.zeros((len(f_lon), lon.shape[0], lon.shape[1]))
  i = 0
  for i_f_lon, i_f_lat in zip(f_lon, f_lat): 
    dist_grid[i, :, :] = fd.compute_dist_from_cdt(lat, lon, i_f_lat, i_f_lon)
    sign_grid[i, :, :] = get_sign_grid(lat, lon, i_f_lat, i_f_lon, f_type) 
    i += 1


  # getting the index of minimum distances from the fronts
  dist_grid_argmin = np.nanargmin(dist_grid, axis=0)

  # getting the index of minimum distances from the fronts
  sign_grid_min = linidx_take(sign_grid, dist_grid_argmin)

  # getting the index of minimum distances from the fronts
  dist_grid_min = np.nanmin(dist_grid, axis=0)

  dist_grid_final = dist_grid_min * sign_grid_min

  return dist_grid_final
    
###############################################################
# ----------------------- MAIN CODE ---------------------------
###############################################################

start_time = time.time()
# Main Code 
# plt.style.use(['ggplot', 'classic'])
plt.style.use(['seaborn-talk', 'ggplot'])

year_list = range(defines.transect_years[0], defines.transect_years[1]+1)
# Debug: overwriting the year list

# getting land ocean mask for era-interim
# ds = xr.open_dataset('/localdrive/drive6/erai/invariants.nc')
ds = xr.open_dataset(defines.topo_file)
if ('time' in ds.coords.keys()):
  lm = ds.lsm.isel(time=0).values
else:
  lm = ds.lsm.values
lm = (lm > defines.thresh_landsea)
ds.close()

# creating the transect analysis
front_dist_bins = np.arange(-1450, 1550, 100)
height_bins = np.arange(0, 15, 1)

front_dist_bins_mid = front_dist_bins[:-1] + (front_dist_bins[1] - front_dist_bins[0])/2.
height_bins_mid = height_bins[:-1] + (height_bins[1] - height_bins[0])/2.

transect = {}
transect['front_dist'] = front_dist_bins_mid
transect['height'] = height_bins_mid
hemis = ['NH', 'SH']
front_types = ['cf', 'wf']
for var_name in defines.transect_var_list: 
  transect[var_name] = {}
  for i_hemis in hemis: 
    transect[var_name][i_hemis] = {}
    for i_type in front_types: 
      transect[var_name][i_hemis][i_type] = {}
      for i_lm in ['land', 'ocean']:
        transect[var_name][i_hemis][i_type][i_lm] = {}
        for i_season in ['all', 'djf', 'jja', 'mam', 'son', 'warm']:
          transect[var_name][i_hemis][i_type][i_lm][i_season] = {'sum': np.zeros((len(front_dist_bins_mid), len(height_bins_mid))), 'cnts': np.zeros((len(front_dist_bins_mid), len(height_bins_mid)))}

for year in year_list: 
  print('Debug: Reading in data ...', end=" ")

  # filenames for the necessary files
  slp_file = os.path.join(defines.slp_data_directory, f'slp.{year}.nc')
  front_file = os.path.join(defines.fronts_folder, f'fronts_{defines.model}_{year}.nc')

  # getting hte info for the model and fronts data
  model_slp = xr.open_dataset(slp_file)
  fronts = xr.open_dataset(front_file)

  # make sure that the fronts lon/lat are the same as the variable lat/lon
  assert(np.all((model_slp.lon - fronts.lon) == 0) & np.all((model_slp.lat - fronts.lat) == 0.))

  # creating the cdt grid 
  lon, lat = np.meshgrid(model_slp.lon, model_slp.lat)

  print(' Completed!')
    
  ############# Get Centers for the given date ######################
  in_file = os.path.join(defines.read_folder, f'{defines.model}_{year}.mat')
  all_centers = reader.read_center_from_mat_file(in_file)

  # loop through all hte time steps in the year
  for t_step in tqdm(range(1, len(fronts.time)), total=len(fronts.time), desc=f'{year}: '):

    # creating a datetime variable for the current time step
    date = pd.Timestamp(fronts.time[t_step].values).to_pydatetime()
    model_slp_tstep = model_slp.isel(time=t_step)
    fronts_tstep = fronts.isel(time=t_step)

    # if np.any(fronts_tstep.cf > 0): 
    #   plt.figure()
    #   plt.pcolormesh(lon, lat, model_slp_tstep.slp); 
    #   plt.colorbar()
    #   plt.pcolormesh(lon, lat, fronts_tstep.cf); 
    #   plt.show()
    #   import pdb; pdb.set_trace(); 

    # getting the season for the given time step date
    t_step_month = date.month
    if (t_step_month == 12) | (t_step_month == 1) | (t_step_month == 2):
      t_season = 'djf'
    elif (t_step_month == 3) | (t_step_month == 4) | (t_step_month == 5):
      t_season = 'mam'
    elif (t_step_month == 6) | (t_step_month == 7) | (t_step_month == 8):
      t_season = 'jja'
    elif (t_step_month == 9) | (t_step_month == 10) | (t_step_month == 11):
      t_season = 'son'

    t_season_warm = False
    if (t_step_month == 11) | (t_step_month == 12) | (t_step_month == 1) | (t_step_month == 2) | (t_step_month == 3):
      t_season_warm = True

    # check if the t_season is requested in the defines.py
    # atleast 'all' should be given in the season_list
    if ('all' not in defines.transect_season_list) & (t_season not in defines.transect_season_list) & ('warm' not in defines.transect_season_list): 
      continue
    
    # minutes = np.asscalar(fronts.time[t_step].values)
    # date = dt.datetime(year, 1, 1) + dt.timedelta(minutes=minutes)
  
    fd_date = date
    centers = all_centers.find_centers_for_date(fd_date)

    for i_center, _  in enumerate(centers.lat): 
      date_str = fd_date.strftime('%Y%m%d%H')
      debug_append = f'{date_str}{i_center:03d}'
      center = {}
      for key in centers.keys():
        center[key] = centers[key][i_center]

      if not ((np.abs(center['lat']) >= defines.transect_centers_range[0]) & (np.abs(center['lat']) <= defines.transect_centers_range[1])):
        continue

      # distance from given center
      dist_grid = fd.compute_dist_from_cdt(lat, lon, center['lat'], center['lon'])
      
      # index of center of cyclone
      c_ind = np.nanargmin(dist_grid)
      cx, cy = np.unravel_index(c_ind, dist_grid.shape)
      lm_flag = lm[cx, cy]
      if (lm_flag): 
        lm_type = 'land'
      else:
        lm_type = 'ocean'

      # Notes: 
      # front detection I save unique labels for the fronts, 
      # but I have to match the correct label again to the storm center
      # I could probably make the code below much faster, think about it

      # Getting the cf_mask for the given center 
      # new method: get the label of the front (cold/warm) that is closest to the center
      cf_flag = False
      ind_cf_fronts = (fronts_tstep.cf.values > 0) & (dist_grid < 500)
      if(np.any(ind_cf_fronts)): 
        tmp_dists = dist_grid[ind_cf_fronts]
        tmp_labels = fronts_tstep.cf.values[ind_cf_fronts]
        tmp_ind = np.nanargmin(tmp_dists)
        cf_mask = (fronts_tstep.cf.values == tmp_labels[tmp_ind])
        if (np.any(cf_mask)):
          cf_flag = True
      
      # Getting the wf_mask for the given center 
      # new method: get the label of the front (cold/warm) that is closest to the center
      wf_flag = False
      ind_wf_fronts = (fronts_tstep.wf.values > 0) & (dist_grid < 500)
      if(np.any(ind_wf_fronts)): 
        tmp_dists = dist_grid[ind_wf_fronts]
        tmp_labels = fronts_tstep.wf.values[ind_wf_fronts]
        tmp_ind = np.nanargmin(tmp_dists)
        wf_mask = (fronts_tstep.wf.values == tmp_labels[tmp_ind])
        if (np.any(wf_mask)):
          wf_flag = True

      # if no warm or cold front, then just skip this center
      if (not wf_flag) & (not cf_flag): 
        continue

      # filtering out cyclones with centers within 30-60 N/S
      if (np.abs(center['lat']) > 60) | (np.abs(center['lat']) < 30):
        continue
      
      if (cf_flag):
        # getting the lat, lon of the fronts for the diven date
        cf_indexes = np.argwhere(cf_mask)

        # # here i use only the cold front points that are greater than 500 from the center
        # cf_lat = lat[cf_mask & (dist_grid > 500)] 
        # cf_lon = lon[cf_mask & (dist_grid > 500)]

        # here i use all the cold front points
        cf_lat = lat[cf_mask] 
        cf_lon = lon[cf_mask]
        cf_weights = dist_grid[cf_mask]
      
        # if np.any(fronts_tstep.cf > 0): 
        #   plt.figure()
        #   plt.pcolormesh(lon, lat, model_slp_tstep.slp); 
        #   plt.colorbar()
        #   tmp = fronts_tstep.cf.values
        #   tmp[tmp == 0] = np.nan
        #   plt.pcolormesh(lon, lat, fronts_tstep.cf, cmap='jet'); 
        #   plt.plot(center['lon'], center['lat'], '*k', markersize=20)
        #   plt.plot(cf_lon, cf_lat, '*r')
        #   plt.title(f"{center['lon']}, {center['lat']}")
        #   plt.show()
        #   import pdb; pdb.set_trace(); 

        if (len(cf_lat) == 0): 
          cf_flag = False
        else:
          # getting distance from the front line fit
          # things added: remove distances above and below the fronts,
          # also removed anything above the center for cold front 
          dist_from_front_cf = get_dist_from_front(cf_lon, cf_lat, lon, lat, 'cf')
          dist_from_front_cf[(dist_grid > 5000) | (dist_grid < 500)] = np.nan
          min_cf_lat = np.nanmin(np.abs(cf_lat))
          max_cf_lat = np.nanmax(np.abs(cf_lat))
          dist_from_front_cf[np.abs(lat) < min_cf_lat] = np.nan
          dist_from_front_cf[np.abs(lat) > max_cf_lat] = np.nan
          dist_from_front_cf[np.abs(lat) > np.abs(center['lat'])] = np.nan

      if (wf_flag):
        wf_indexes = np.argwhere(wf_mask)
        wf_lat = lat[wf_mask]
        wf_lon = lon[wf_mask]
        wf_weights = dist_grid[wf_mask]

        # getting the distance from the front line
        dist_from_front_wf = get_dist_from_front(wf_lon, wf_lat, lon, lat, 'wf')
        dist_from_front_wf[(dist_grid > 5000) | (dist_grid < 500)] = np.nan

      # if (cf_flag & wf_flag & (center['lat'] < 0)):
      #   plt.figure(figsize=(12,4))
      #   ax1 = plt.subplot(1,2,1)
      #   ax2 = plt.subplot(1,2,2)
      #   if (cf_flag): 
      #     ax1.set_title('Cold Front')
      #     pc = ax1.pcolormesh(lon, lat, dist_from_front_cf, cmap='bwr', vmin=-500, vmax=500)
      #     plt.colorbar(pc, ax=ax1)
      #     ax1.plot(center['lon'], center['lat'], 'r*')
      #     ax1.plot(cf_lon, cf_lat, 'k.')
      #   if (wf_flag): 
      #     ax2.set_title('Warm Front')
      #     pc = ax2.pcolormesh(lon, lat, dist_from_front_wf, cmap='bwr', vmin=-500, vmax=500)
      #     plt.colorbar(pc, ax=ax2)
      #     ax2.plot(center['lon'], center['lat'], 'r*')
      #     ax2.plot(wf_lon, wf_lat, 'k.')
      #   # plt.savefig('./RUNDIR/tmp_imgs/transect/single_case_new_method.png', dpi=300.)
      #   plt.show()
      #   import pdb; pdb.set_trace()

      # Geo-potential height (3d) file datasets
      model_z = xr.open_dataset(os.path.join(defines.var_data_directory, f'z.{year}.nc'))
      model_z_tstep = model_z.isel(time=t_step)

      # repeat distance matrix into 3d structure 
      if (cf_flag):
        # ------------------------------------ CF 
        # create the distance from front as 3d matrix
        dist_3d = np.repeat(dist_from_front_cf[np.newaxis, :, :], len(model_z_tstep.lev), axis=0)
        front_type = 'cf'

        # loop through all the 3d variables, and create the transects
        for var_ind, var_name in enumerate(defines.transect_var_list):
          
          # variable dataset
          model_var = xr.open_dataset(os.path.join(defines.var_data_directory, f'{var_name}.{year}.nc'))

          # getting the time step
          model_var_tstep = model_var.isel(time=t_step)

          # masking out the Z values for region that we need to compute transects for
        
          model_z_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front_cf))
          model_var_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front_cf))

          # z_values
          model_z_mask = model_z_tstep.where(model_z_tstep.mask == 1)
          model_dist = dist_3d.flatten()
          model_H = (model_z_mask.z).values.flatten()

          # var values
          model_var_mask = model_var_tstep.where(model_var_tstep.mask == 1)
          model_val = (model_var_mask[var_name]).values.flatten()

          ind = ~np.isnan(model_dist) & ~np.isnan(model_H) & ~np.isnan(model_val)

          # Using only model values above a given threshold
          if (defines.transect_var_thres[var_ind] is not None): 
            ind = ind & (model_val > defines.transect_var_thres[var_ind])

          H_sum, x,y = np.histogram2d(model_dist[ind], model_H[ind], bins=(front_dist_bins, height_bins), weights=model_val[ind])
          H_cnts, x,y = np.histogram2d(model_dist[ind], model_H[ind], bins=(front_dist_bins, height_bins))

          # # zero'ing out any nan values that I encounter from histogram2d function 
          # # making sure I only use cases where is atleast one cloud when I average out multiple histograms
          # nan_ind = np.isnan(H_sum) | np.isnan(H_cnts)
          # H_sum[nan_ind] = 0
          # H_cnts[nan_ind] = 0
          H_sum[H_sum<=0] = 0
          H_cnts[H_sum<=0] = 0

          H = H_sum/H_cnts

          if (center['lat'] < 0):
            hemis = 'SH'
          elif (center['lat'] >= 0):
            hemis = 'NH'
          transect[var_name][hemis][front_type][lm_type]['all']['sum'] += H_sum
          transect[var_name][hemis][front_type][lm_type]['all']['cnts'] += H_cnts

          if (t_season_warm):
            transect[var_name][hemis][front_type][lm_type]['warm']['sum'] += H_sum
            transect[var_name][hemis][front_type][lm_type]['warm']['cnts'] += H_cnts
          
          # incrementing the sum and cnt of the appropriate season
          transect[var_name][hemis][front_type][lm_type][t_season]['sum'] += H_sum
          transect[var_name][hemis][front_type][lm_type][t_season]['cnts'] += H_cnts

          # close the 3d var file
          model_var.close()

          # if (hemis == 'SH') & (lm_type == 'ocean') & (t_season_warm) & (var_name == 'rh'):
          #   plt.close('all')
          #   plt.figure()
          #   plt.subplot(1,2,1)
          #   plt.pcolormesh(lon, lat, dist_from_front_cf, cmap='jet')
          #   plt.plot(cf_lon, cf_lat, 'k*')
          #   plt.plot(center['lon'], center['lat'], 'r*')
          #   plt.subplot(1,2,2)
          #   plt.pcolormesh(transect['front_dist'], transect['height'], (H_sum/H_cnts).T, cmap='jet');
          #   plt.colorbar(); 
          #   plt.show()
          #   import pdb; pdb.set_trace()

         
      if (wf_flag):
        # ------------------------------------ WF 
        # create the distance from front as 3d matrix
        dist_3d = np.repeat(dist_from_front_wf[np.newaxis, :, :], len(model_z_tstep.lev), axis=0)
        front_type = 'wf'

        # loop through all the 3d variables, and create the transects
        for var_ind, var_name in enumerate(defines.transect_var_list):
          
          # variable dataset
          model_var = xr.open_dataset(os.path.join(defines.var_data_directory, f'{var_name}.{year}.nc'))

          # getting the time step
          model_var_tstep = model_var.isel(time=t_step)

          # masking out the Z values for region that we need to compute transects for
          model_z_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front_wf))
          model_var_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front_wf))

          # z_values
          model_z_mask = model_z_tstep.where(model_z_tstep.mask == 1)
          model_dist = dist_3d.flatten()
          model_H = (model_z_mask.z).values.flatten()

          # var values
          model_var_mask = model_var_tstep.where(model_var_tstep.mask == 1)
          model_val = (model_var_mask[var_name]).values.flatten()

          ind = ~np.isnan(model_dist) & ~np.isnan(model_H) & ~np.isnan(model_val)
          
          # Using only model values above a given threshold
          if (defines.transect_var_thres[var_ind] is not None): 
            ind = ind & (model_val > defines.transect_var_thres[var_ind])

          H_sum, x,y = np.histogram2d(model_dist[ind], model_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)), weights=model_val[ind])
          H_cnts, x,y = np.histogram2d(model_dist[ind], model_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)))
          x_mid = x[:-1] + (x[1] - x[0])/2.
          y_mid = y[:-1] + (y[1] - y[0])/2.
          
          # # zero'ing out any nan values that I encounter from histogram2d function 
          # # making sure I only use cases where is atleast one cloud when I average out multiple histograms
          # nan_ind = np.isnan(H_sum) | np.isnan(H_cnts)
          # H_sum[nan_ind] = 0
          # H_cnts[nan_ind] = 0
          H_sum[H_sum<=0] = 0
          H_cnts[H_sum<=0] = 0

          H = H_sum/H_cnts
          
          if (center['lat'] < 0):
            hemis = 'SH'
          elif (center['lat'] >= 0):
            hemis = 'NH'
          transect[var_name][hemis][front_type][lm_type]['all']['sum'] += H_sum
          transect[var_name][hemis][front_type][lm_type]['all']['cnts'] += H_cnts

          if (t_season_warm):
            transect[var_name][hemis][front_type][lm_type]['warm']['sum'] += H_sum
            transect[var_name][hemis][front_type][lm_type]['warm']['cnts'] += H_cnts
         
          # incrementing the sum and cnt of the appropriate season
          transect[var_name][hemis][front_type][lm_type][t_season]['sum'] += H_sum
          transect[var_name][hemis][front_type][lm_type][t_season]['cnts'] += H_cnts

          # close the 3d var file
          model_var.close()
         
      # close the 3d z file
      model_z.close()

    # if (date > dt.datetime(1979, 1, 10)): 
    if (stop_at_date is not None): 
      if (date > stop_at_date): 
        print('Done!')
        break

  if (stop_at_date is not None):
    break

print(f'--- {time.time() - start_time} seconds --- ')


# # -----------------------------------------
# # Testing out the plots
# # -----------------------------------------

if (stop_at_date is not None): 
  plt.figure()
  var_name = 'rh'
  ftype = 'cf'
  lm_type = 'ocean'
  hemis = 'SH'
  season='warm'
  tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
  plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap='jet');
  plt.colorbar(); 
  plt.show()

import pickle

out_fn = f'transect_out_{defines.transect_centers_range[0]}_{defines.transect_centers_range[1]}.pkl'
pickle.dump(transect, open(os.path.join(defines.read_folder, out_fn), 'wb'))

# pickle.dump(transect, open(os.path.join(defines.read_folder, 'transect_out.pkl'), 'wb'))

# # ---------------- Plotting the transect analysis outputs -------------------
# # Creating plots for the various variables 
#
#
# for season in defines.transect_season_list:
#   # Looping through all the 3d variables 
#   for var_name in defines.transect_var_list:
#     # Looping through the different hemispheres
#     for hemis in defines.transect_hemis_list:
#       plt.close('all')
#       plt.figure()
#
#       if (var_name == 'T'):
#         levels = np.arange(210, 290, 10);  cmap='default' # T
#       elif (var_name in ['U', 'V']):
#         levels = np.arange(-40, 40, 5); cmap='bwr' # U
#       else: 
#         levels = 20; cmap='viridis'
#       plt.subplot(2,2,1)
#       ftype = 'cf'
#       lm_type = 'ocean'
#       tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
#       # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
#       plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
#       plt.colorbar(); 
#       plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
#
#       plt.subplot(2,2,2)
#       ftype = 'wf'
#       lm_type = 'ocean'
#       tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
#       # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
#       plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
#       plt.colorbar(); 
#       plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
#
#       plt.subplot(2,2,3)
#       ftype = 'cf'
#       lm_type = 'land'
#       tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
#       # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
#       plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
#       plt.colorbar(); 
#       plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
#
#       plt.subplot(2,2,4)
#       ftype = 'wf'
#       lm_type = 'land'
#       tmp = (transect[var_name][hemis][ftype][lm_type][season]['sum']/transect[var_name][hemis][ftype][lm_type][season]['cnts']).T
#       # plt.contourf(transect['front_dist'], transect['height'], tmp, levels=levels, extend='both', cmap=cmap);
#       plt.pcolormesh(transect['front_dist'], transect['height'], tmp, cmap=cmap);
#       plt.colorbar(); 
#       plt.title(f'Across {hemis.upper()} - {lm_type.upper()}, {ftype.upper()}: {var_name.upper()} {season.upper()}')
#
#       plt.tight_layout()
#       out_file = os.path.join(defines.images_folder, f'{defines.model}_{defines.transect_years[0]}_{defines.transect_years[1]}_transect_{hemis.upper()}_{var_name.upper()}_{season.upper()}.png')
#       plt.savefig(out_file, dpi=300.) 
#
#       plt.show()
