#!/usr/bin/env python
import numpy as np 
import front_detection as fd
from front_detection import catherine
from scipy.ndimage import label, generate_binary_structure
import glob
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import datetime as dt
import plotter
import reader
import xarray as xr

import pdb
import cartopy

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

def dextend_dist(lat, lon, dist, lon_size):

  lat = lat[:, lon_size:lon_size*2]
  lon = lon[:, lon_size:lon_size*2]

  dist_neg = np.copy(dist)
  dist_neg[dist_neg > 0] = np.nan
  dist_3d = np.empty((3, lat.shape[0], lon_size))
  dist_3d[0, :, :] = dist_neg[:, 0:lon_size]
  dist_3d[1, :, :] = dist_neg[:, lon_size:lon_size*2]
  dist_3d[2, :, :] = dist_neg[:, lon_size*2:]
  dist_neg = np.nanmax(dist_3d, axis=0)
  
  dist_pos = np.copy(dist)
  dist_pos[dist_pos < 0] = np.nan
  dist_3d = np.empty((3, lat.shape[0], lon_size))
  dist_3d[0, :, :] = dist_pos[:, 0:lon_size]
  dist_3d[1, :, :] = dist_pos[:, lon_size:lon_size*2]
  dist_3d[2, :, :] = dist_pos[:, lon_size*2:]
  dist_pos = np.nanmin(dist_3d, axis=0)

  dist = np.copy(dist_pos)
  SH = (lat < 0)
  dist[np.isnan(dist_pos)] = dist_neg[np.isnan(dist_pos)]
  dist[~np.isnan(dist_neg ) & SH] = dist_neg[~np.isnan(dist_neg ) & SH]
  return lat, lon, dist

def get_dist_from_front(fit, lon, lat, indexes, f_type='cf'):

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

  # screening out any values greater than 1500
  dist_orig = np.copy(dist) # testing JJ
  dist[dist > 1500] = np.nan

  # check if cf or wf, and make -/+ depending on that
  if (f_type == 'cf'):
    neg_mask = (lon < tmp_lon)
  elif (f_type == 'wf'):
    neg_mask = (lat < tmp_lat)

  # making the distances +/- depending on mask
  dist[neg_mask] *= -1

  dist[np.abs(lat) > 75] = np.nan

  plt.close('all')
  ax = plt.axes(projection=cartopy.crs.PlateCarree())
  ax.coastlines(lw=1., alpha=.5)
  plt.pcolormesh(lon, lat, dist, cmap='bwr', vmin=-500, vmax=500)
  plt.colorbar()
  plt.plot(lon[0, :], np.poly1d(fit)(lon[0, :]), 'r', lw=2., label='Front')
  plt.savefig(f'./images/dist_{f_type}.png', dpi=300)

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
  
  plt.close('all')
  ax = plt.axes(projection=cartopy.crs.PlateCarree())
  ax.coastlines(lw=1., alpha=.5)
  plt.pcolormesh(lon, lat, dist, cmap='bwr', vmin=-500, vmax=500)
  plt.colorbar()
  plt.plot(lon[0, :], np.poly1d(fit)(lon[0, :]), 'r', lw=2., label='Front')
  plt.savefig(f'./images/cropped_dist_{f_type}.png', dpi=300)

  # dextending the distance 3d 
  lat, lon, dist = dextend_dist(lat, lon, dist, lon_size)
  
  return dist

# ----------------------- MAIN CODE ---------------------------
# Main Code 
# plt.style.use(['ggplot', 'classic'])
plt.style.use(['seaborn-talk', 'ggplot'])

### Reading in MERRA-2 data
year = 2007
model_name = 'merra2'
hemis = 'NH'

model_folder = '/mnt/drive5/merra2/six_hrly/'

print('Debug: Reading in data ...', end=" ")

# loading in merra2 inst6_3d_ana_Np data
merra_file = '/localdrive/drive10/merra2/inst6_3d_ana_Np/MERRA2_300.inst6_3d_ana_Np.20070101.nc4'
fronts_file = './merra_2_tmp_out.nc'
merra = xr.open_dataset(merra_file)
fronts = xr.open_dataset(fronts_file)

# creating the cdt grid 
lon, lat = np.meshgrid(merra.lon, merra.lat)

# getting the index of the level 850
lev850 = np.where(merra.lev.values == 850)[0][0]
merra['SLP'] = merra.SLP/100.
merra_850 = merra.sel(lev=850)

print(' Completed!')


for t_step in range(1, len(fronts.time)):
  # creating a datetime variable for the current time step
  minutes = np.asscalar(fronts.time[t_step])
  date = dt.datetime(year, 1, 1) + dt.timedelta(minutes=minutes)
  merra_tstep = merra.isel(time=t_step)
  fronts_tstep = fronts.isel(time=t_step)
  print(date)

  ############# Get Centers for the given date ######################
  fd_date = date
  in_file = '/mnt/drive1/processed_data/tracks/merra2_tracks/ERAI_%d_cyc.mat'%(fd_date.year)
  all_centers = reader.read_center_from_mat_file(in_file)
  centers = all_centers.find_centers_for_date(fd_date)

  for i_center, _  in enumerate(centers.lat): 
    center = {}
    for key in centers.keys():
      center[key] = centers[key][i_center]

    # distance from given center
    dist_grid = fd.compute_dist_from_cdt(lat, lon, center['lat'], center['lon'])
    mask_valid_fronts = (dist_grid < 1000)

    # fit lines through the detected fronts
    cf_lat = lat[mask_valid_fronts & (fronts_tstep.cf == 1)]

    if (len(cf_lat) == 0):
      continue

    if (i_center != 11): 
      continue
  
    # getting the lat, lon of the fronts
    cf_indexes = np.argwhere(mask_valid_fronts & (fronts_tstep.cf == 1).values)
    cf_lon = lon[mask_valid_fronts & (fronts_tstep.cf == 1)]
    cf_weights = dist_grid[mask_valid_fronts & (fronts_tstep.cf == 1)]
    wf_indexes = np.argwhere(mask_valid_fronts & (fronts_tstep.wf == 1).values)
    wf_lat = lat[mask_valid_fronts & (fronts_tstep.wf == 1)]
    wf_lon = lon[mask_valid_fronts & (fronts_tstep.wf == 1)]
    wf_weights = dist_grid[mask_valid_fronts & (fronts_tstep.wf == 1)]

    # adding center point before fitting the front line
    cf_lon = np.append(cf_lon, center['lon'])
    cf_lat = np.append(cf_lat, center['lat'])
    cf_weights = np.append(cf_weights, np.nanmax(cf_weights))
    wf_lon = np.append(wf_lon, center['lon'])
    wf_lat = np.append(wf_lat, center['lat'])
    wf_weights = np.append(wf_weights, np.nanmax(wf_weights))

    # fitting a line through the front points
    # weight it according to how far away from the center the values are
    cf_fit = np.polyfit(cf_lon, cf_lat, 1, w=1/cf_weights)
    wf_fit = np.polyfit(wf_lon, wf_lat, 1, w=1/wf_weights)

    # testing 
    plt.close('all')
    plt.figure()
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    ax.coastlines()
    ax.set_global()
    ax.plot(cf_lon, cf_lat, 'b*')
    ax.plot(wf_lon, wf_lat, 'r*')
    ax.plot(center['lon'], center['lat'], 'y*')
    plt.savefig('./images/tmp.png', dpi=300.)

    # index of center of cyclone
    c_ind = np.nanargmin(dist_grid)
    cx, cy = np.unravel_index(c_ind, dist_grid.shape)
   
    # getting the distance from the front
    dist_from_front = get_dist_from_front(cf_fit, lon, lat, cf_indexes, 'cf')
    dist_from_front[dist_grid > 5000] = np.nan
    
    # getting the distance from the front
    dist_from_front_wf = get_dist_from_front(wf_fit, lon, lat, wf_indexes, 'wf')
    dist_from_front_wf[dist_grid > 5000] = np.nan
  
    # if the center is near the dateline, then we have to replace the appropriate edges
    # if the center is 30 degrees from the edge, then we have to replace the appropraite portion of the grid
    plt.close('all')
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    ax.coastlines(lw=1., alpha=.5)
    plt.pcolormesh(lon, lat, dist_from_front, cmap='bwr', vmin=-500, vmax=500)
    plt.colorbar()
    plt.plot(lon[0, :], np.poly1d(cf_fit)(lon[0, :]), 'r', lw=2., label='Front')
    plt.plot(lon[cx,cy], lat[cx,cy], 'g*', markersize=10, label='Point')
    plt.savefig('./images/cropped_dist.png', dpi=300)
    
    plt.close('all')
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    ax.coastlines(lw=1., alpha=.5)
    plt.pcolormesh(lon, lat, dist_from_front_wf, cmap='bwr', vmin=-500, vmax=500)
    plt.colorbar()
    plt.plot(lon[0, :], np.poly1d(wf_fit)(lon[0, :]), 'r', lw=2., label='Front')
    plt.plot(lon[cx,cy], lat[cx,cy], 'g*', markersize=10, label='Point')
    plt.savefig('./images/cropped_dist_wf.png', dpi=300)

    # repeat distance matrix into 3d structure 
    # ------------------------------------ CF 
    dist_3d = np.repeat(dist_from_front[np.newaxis, :, :], len(merra_tstep.lev), axis=0)
    front_type = 'cf'
    merra_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front))
    merra_mask = merra_tstep.where(merra_tstep.mask == 1)
    merra_dist = dist_3d.flatten()
    merra_H = (merra_mask.H/1000.).values.flatten()
    for var_name in ['V', 'U', 'T', 'QV', 'O3']:
      merra_val = (merra_mask[var_name]).values.flatten()
      ind = ~np.isnan(merra_dist) & ~np.isnan(merra_H) & ~np.isnan(merra_val)

      H_sum, x,y = np.histogram2d(merra_dist[ind], merra_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)), weights=merra_val[ind])
      H_cnts, x,y = np.histogram2d(merra_dist[ind], merra_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)))
      x_mid = x[:-1] + (x[1] - x[0])/2.
      y_mid = y[:-1] + (y[1] - y[0])/2.

      H = H_sum/H_cnts
      
      plt.close('all')
      plt.contourf(x_mid,y_mid,H.T);
      plt.colorbar(); 
      plt.title(f'Across {front_type.upper()}: {var_name}')
      plt.savefig(f'./images/transect_{var_name}_{front_type}.png', dpi=300.)
    
    # ------------------------------------ WF 
    dist_3d = np.repeat(dist_from_front_wf[np.newaxis, :, :], len(merra_tstep.lev), axis=0)
    front_type = 'wf'
    merra_tstep.coords['mask'] = (('lat', 'lon'), ~np.isnan(dist_from_front_wf))
    merra_mask = merra_tstep.where(merra_tstep.mask == 1)
    merra_dist = dist_3d.flatten()
    merra_H = (merra_mask.H/1000.).values.flatten()
    for var_name in ['V', 'U', 'T', 'QV', 'O3']:
      merra_val = (merra_mask[var_name]).values.flatten()
      ind = ~np.isnan(merra_dist) & ~np.isnan(merra_H) & ~np.isnan(merra_val)

      H_sum, x,y = np.histogram2d(merra_dist[ind], merra_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)), weights=merra_val[ind])
      H_cnts, x,y = np.histogram2d(merra_dist[ind], merra_H[ind], bins=(np.arange(-1450, 1550, 100), np.arange(0, 15, 1.)))
      x_mid = x[:-1] + (x[1] - x[0])/2.
      y_mid = y[:-1] + (y[1] - y[0])/2.

      H = H_sum/H_cnts
      
      plt.close('all')
      plt.contourf(x_mid,y_mid,H.T);
      plt.colorbar(); 
      plt.title(f'Across {front_type.upper()}: {var_name}')
      plt.savefig(f'./images/transect_{var_name}_{front_type}.png', dpi=300.)

    # plotting the Cloud front and the mask 
    plt.close('all')
    ax = plt.subplot(1,2,1, projection=cartopy.crs.PlateCarree())
    ax.coastlines(lw=.5, alpha=0.5)
    div = 50 
    ax.set_extent([center['lon']-div, center['lon']+div, center['lat']-div, 90])
    # ax.set_global()
    pc = ax.pcolormesh(lon, lat, np.double(dist_from_front), cmap='bwr', vmin=-1500, vmax=1500)
    ax.plot(merra.lon, np.poly1d(cf_fit)(merra.lon), 'k--', lw=2.)
    ax.plot(center['lon'], center['lat'], 'y*', markersize=15)
    ax.plot(cf_lon, cf_lat, 'b*', markersize=5)
    plt.colorbar(pc, ax=ax)
    
    ax = plt.subplot(1,2,2, projection=cartopy.crs.PlateCarree())
    ax.coastlines(lw=.5, alpha=0.5)
    div = 50 
    ax.set_extent([center['lon']-div, center['lon']+div, center['lat']-div, 90])
    # ax.set_global()
    pc = ax.pcolormesh(lon, lat, np.double(dist_from_front_wf), cmap='bwr', vmin=-1500, vmax=1500)
    ax.plot(merra.lon, np.poly1d(wf_fit)(merra.lon), 'k--', lw=2.)
    ax.plot(center['lon'], center['lat'], 'y*', markersize=15)
    ax.plot(wf_lon, wf_lat, 'r*', markersize=5)
    plt.colorbar(pc, ax=ax)

    plt.tight_layout()
    plt.savefig('./images/cropped_fronts_dist_fig.png', dpi=300.)

    pdb.set_trace()

    continue

