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
import glob
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import datetime as dt
import xarray as xr
import os, glob, pdb
import pandas as pd

import reader

import defines
import tqdm

###################################################################################
################## COPY/LINK THE FILES OVER #######################################
###################################################################################

# required variables to run the tracker
var_list = ['u850', 'v850', 't', 'z850', 'slp', 'ps', 'z']
to_folder = defines.data_folder
if (not os.path.exists(to_folder)): 
  os.makedirs(to_folder)
for var in var_list: 
  search_string = os.path.join(defines.var_data_directory, f'{var}.*.nc')
  print(search_string)
  for tmp_file in glob.glob(search_string):
    tmp_file = os.path.basename(tmp_file)
    from_file = os.path.join(defines.var_data_directory, tmp_file)
    to_file =  os.path.join(to_folder, tmp_file)
    # check if var file exists, if not quit program
    if (not os.path.exists(from_file)):
      print(f'Variable file not found: {var}')
      sys.exit(0)
    cmd = f'ln -s {from_file} {to_file}'
    os.system(cmd)

print('Done symlinking the data files...')

###################################################################################
################## MAIN RUN OF FRONT DETECTION ####################################
###################################################################################
year = defines.over_write_years[0]

for year in range(defines.over_write_years[0], defines.over_write_years[1]+1): 

  # year = 2007
  # model_name = 'merra2'
  # hemis = 'NH'

  # print('Debug: Reading in data ...', end=" ")
  print('Debug: Reading in data ...',) # python 2 syntaxing

  # reading in ERA-Interim data
  t_file = os.path.join(defines.var_data_directory, f't.{year}.nc')
  ds_t = xr.open_dataset(t_file)
  in_lon = ds_t.lon.values
  in_lat = ds_t.lat.values
  in_lev = ds_t.lev.values
  in_time = ds_t.time.values
  in_t = ds_t.t

  slp_file = os.path.join(defines.var_data_directory, f'slp.{year}.nc')
  ds_slp = xr.open_dataset(slp_file)
  in_slp = ds_slp.slp

  ps_file = os.path.join(defines.var_data_directory, f'ps.{year}.nc')
  ds_ps = xr.open_dataset(ps_file)
  in_ps = ds_ps.ps

  u850_file = os.path.join(defines.var_data_directory, f'u850.{year}.nc')
  ds_u850 = xr.open_dataset(u850_file)
  in_u850 = ds_u850.u850

  v850_file = os.path.join(defines.var_data_directory, f'v850.{year}.nc')
  ds_v850 = xr.open_dataset(v850_file)
  in_v850 = ds_v850.v850

  z_file = os.path.join(defines.var_data_directory, f'z.{year}.nc')
  ds_z = xr.open_dataset(z_file)
  in_z = ds_z.z

  # creating cdt grid
  lon, lat = np.meshgrid(in_lon, in_lat)

  # getting the index of the level 850
  lev850 = np.where(in_lev == 850)[0][0]

  ## remove this 
  # # loading in merra2 inst6_3d_ana_Np data
  # ncid = Dataset('/localdrive/drive10/merra2/inst6_3d_ana_Np/MERRA2_300.inst6_3d_ana_Np.20070101.nc4', 'r')
  # ncid.set_auto_mask(False)
  # in_lon = ncid.variables['lon'][:]
  # in_lat = ncid.variables['lat'][:]
  # in_lev = ncid.variables['lev'][:]
  # in_time = np.asarray(ncid.variables['time'][:], dtype=float)
  #
  # in_slp = ncid.variables['SLP']
  # T = ncid.variables['T']
  # U = ncid.variables['U']
  # V = ncid.variables['V']
  # geoH = ncid.variables['H']
  # PS = ncid.variables['PS']
  #
  # # creating the cdt grid 
  # lon, lat = np.meshgrid(in_lon, in_lat)
  #
  # # getting the index of the level 850
  # lev850 = np.where(in_lev == 850)[0][0]
  #

  print(' Completed!')

  # TODO
  # I can probably move the read in all centers here, for the given range of years!

  cf_all = np.empty((len(in_time), len(in_lat), len(in_lon)))
  wf_all = np.empty((len(in_time), len(in_lat), len(in_lon)))

  for t_step in tqdm.tqdm(range(2, in_time.shape[0]), total=in_time.shape[0], desc=f'{year}: '):

    # creating a datetime variable for the current time step
    # date = dt.datetime(year, 1, 1) + dt.timedelta(minutes=in_time[t_step])
    date = pd.Timestamp(in_time[t_step]).to_pydatetime()

    # getting SLP values for MERRA2 
    # should already be in mb/hPa
    slp = in_slp[t_step, :, :]

    
    # getting Wind and temperature at 850 hPa for MERRA2
    prev_u850 = in_u850[t_step-1, :, :]
    u850 = in_u850[t_step, :, :]

    prev_v850 = in_v850[t_step-1, :, :]
    v850 = in_v850[t_step, :, :]
   
    # getting the temperature at 850 hPa
    t850 = in_t[t_step, lev850, :, :]
    theta850 = fd.theta_from_temp_pres(t850.values, 850)
    

    # getting the 1km values of temperature
    # the code below is a work around to speed up the code, isntead of running a nest for loop

    # getting the height values from MERRA2
    H = in_z[t_step, :, :, :]
    H850 = in_z[t_step, lev850, :, :].values

    # getting the surface pressure in hPa 
    surface_pres = in_ps[t_step, :, :].values/100.
    

    pres_3d = np.repeat(np.array(in_lev[:, np.newaxis], dtype=np.float), H.shape[1], axis=-1) # creating the pressure level into 3d array
    pres_3d = np.repeat(pres_3d[:, :, np.newaxis], H.shape[2], axis=-1) # creating the pressure level into 3d array 

    ps_3d = np.repeat(surface_pres[np.newaxis,:,:], H.shape[0], axis=0)

    # getting the surface height using the surface pressure and geo-potential height 
    pres_diff = np.abs(pres_3d - ps_3d)
    pres_diff_min_val = np.nanmin(pres_diff, axis=0) 
    pres_diff_min_val3d = np.repeat(pres_diff_min_val[np.newaxis, :, :], H.shape[0], axis=0)
    surface_H_ind = (pres_diff == pres_diff_min_val3d)
    ps_height = np.ma.masked_array(np.copy(H), mask=~surface_H_ind, fill_value=np.nan)  
    ps_height = np.nanmin(ps_height.filled(), axis=0) # surface height in km 

    # 1km height above surface
    h1km = ps_height + 1000. 
    h1km_3d = np.repeat(h1km[np.newaxis, :, :], H.shape[0], axis=0); 

    # difference between geopotential height and 1km height
    h1km_diff = np.abs(H - h1km_3d) 
    h1km_diff_min_val = np.nanmin(h1km_diff, axis=0) 
    h1km_diff_min_val_3d = np.repeat(h1km_diff_min_val[np.newaxis, :, :], H.shape[0], axis=0)
    h1km_ind = (h1km_diff == h1km_diff_min_val_3d)
    
    T_3d = np.ma.masked_array(in_t[t_step, :, :, :], mask=~h1km_ind, fill_value=np.nan) # creating a temperature 3d array
    t1km = np.nanmin(T_3d.filled(),axis=0)  # getting the 1km value by finding the minimum value
    
    pres = np.ma.masked_array(pres_3d, mask=~h1km_ind, fill_value=np.nan) # masking out pressure values using minimum 1km mask
    p1km = np.nanmin(pres.filled(), axis=0) # getting the pressure at 1km

    # computing the theta value at 1km
    theta1km = fd.theta_from_temp_pres(t1km, p1km) 

    # smoothing out the read in arrays
    iter_smooth = 10
    center_weight = 4.

    theta850 = fd.smooth_grid(theta850, iter=iter_smooth, center_weight=center_weight) 
    theta1km = fd.smooth_grid(theta1km, iter=iter_smooth, center_weight=center_weight) 

    prev_u850 = fd.smooth_grid(prev_u850, iter=iter_smooth, center_weight=center_weight) 
    u850 = fd.smooth_grid(u850, iter=iter_smooth, center_weight=center_weight) 
    prev_v850 = fd.smooth_grid(prev_v850, iter=iter_smooth, center_weight=center_weight) 
    v850 = fd.smooth_grid(v850, iter=iter_smooth, center_weight=center_weight) 


    # TODO: include below code into front_detection/__init__.py to clean up fronts? 
    # maybe I can clean up depending on storm centers. 

    # computing the simmonds fronts
    f_sim = fd.simmonds_et_al_2012(lat, lon, prev_u850, prev_v850, u850, v850) 

    # computing the hewson fronts using 1km temperature values, and geostrophic U & V winds at 850 hPa
    f_hew, var = fd.hewson_1998(lat, lon, theta1km, H850)
    
    # getting the front types
    wf_hew = f_hew['wf']
    cf_hew = f_hew['cf']
    cf_sim = f_sim['cf']
    wf_temp_grad = f_hew['temp_grad']

    wf_hew[np.isnan(wf_hew)] = 0
    cf_hew[np.isnan(cf_hew)] = 0
    cf_sim[np.isnan(cf_sim)] = 0

    wf = np.copy(wf_hew)
    cf = np.double((cf_hew + cf_sim) > 0)

    orig_wf = np.copy(wf)
    orig_cf = np.copy(cf)

    # cf = np.copy(cf_hew)
    
    ################################################################################
    ############################ CODE TO CLEAN UP THE FRONTS #######################
    ################################################################################
    wf_struct, cf_struct = fd.clean_up_fronts(wf, cf, lat, lon)

    wf = wf_struct[0]
    cf = cf_struct[0]

    w_lat = wf_struct[1]['lat']
    w_lon = wf_struct[1]['lon']
    w_label = wf_struct[1]['label']

    c_lat = cf_struct[1]['lat']
    c_lon = cf_struct[1]['lon']
    c_label = cf_struct[1]['label']

    # have to read in the centers 
    ############# Get Centers for the given date ######################
    # create tracked cyclone centers
    # find the centers for the given date
    # 
    # fd_date = date - dt.timedelta(hours=6.)
    # FIXME move the all_centers read to the top
    # FIXME check for edges/dateline - DONE
    fd_date = date
    # in_file = '/mnt/drive1/processed_data/tracks/merra2_tracks/ERAI_%d_cyc.mat'%(fd_date.year)
    in_file = os.path.join(defines.read_folder, f'{defines.model}_{fd_date.year}.mat')
    all_centers = reader.read_center_from_mat_file(in_file)
    center = all_centers.find_centers_for_date(fd_date)

    # newly added storm_attribution code
    tmp_cf, tmp_wf = fd.storm_attribution(lat, lon, w_label, c_label, center, wf_temp_grad)

    # JJ testing -- here I remove the number of front groups that have less than 3 points

    # setting the fronts to the correct time step
    cf_all[t_step, :, :] = tmp_cf
    wf_all[t_step, :, :] = tmp_wf


  cf_all = np.array(cf_all, dtype=np.float32)
  wf_all = np.array(wf_all, dtype=np.float32)
  out_fronts_file = os.path.join(defines.fronts_folder, f'fronts_{defines.model}_{year}.nc')
  out_ds = xr.Dataset({'cf': (('time', 'lat', 'lon'), cf_all), \
      'wf': (('time', 'lat', 'lon'), wf_all)}, coords={'time': in_time, 'lat': in_lat, 'lon': in_lon})
  out_ds.to_netcdf(out_fronts_file)

def plot_orig(): 
  plt.figure()
  fronts = orig_wf*10 + orig_cf*-10
  fronts[~((fronts == 10) | (fronts == -10))] = np.nan
  m = Basemap(projection='cyl', urcrnrlat=ulat, llcrnrlat=llat, urcrnrlon=ulon, llcrnrlon=llon)
  csf = plt.contourf(lon, lat, var)
  cs = plt.contour(lon, lat, slp, lw=0.1, alpha=0.5, ls='--', colors='k', levels=np.arange(980, 1100, 5))
  plt.clabel(cs, inline=1., fontsize=10., fmt='%.0f')
  pc = m.pcolormesh(lon, lat, fronts, cmap='bwr')
  m.colorbar(csf)
  m.drawcoastlines(linewidth=0.2)
  plt.axhline(y=0., linewidth=1.0, linestyle='--')
  plt.plot(center.lon, center.lat, 'y*', markersize=center_size)
  plt.title('Before Storm Attribution Fronts')
  plt.ion()
  plt.show()

