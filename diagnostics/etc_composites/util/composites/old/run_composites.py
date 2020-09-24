#!/usr/bin/python
import numpy as np 
import scipy.io as sio
import matplotlib.pyplot as plt
import os, glob
from netCDF4 import Dataset
    
import old_defines as odefines
import defines
import datetime as dt

import xarray as xr
import pandas as pd
import common

import sys
sys.path.append('../')
import reader

import pdb

# ---------------------- NEW CODE ----------------------------

###################################################################################
################## COPY/LINK THE FILES OVER #######################################
###################################################################################

var_list = ['tp']
to_folder = defines.data_folder
if (not os.path.exists(to_folder)): 
  os.makedirs(to_folder)
for var in var_list: 
  search_string = os.path.join(defines.model_data_directory, f'{var}.*.nc')
  print(search_string)
  for tmp_file in glob.glob(search_string):
    tmp_file = os.path.basename(tmp_file)
    from_file = os.path.join(defines.model_data_directory, tmp_file)
    to_file =  os.path.join(to_folder, tmp_file)
    cmd = f'ln -s {from_file} {to_file}'
    os.system(cmd)

print('Done symlinking the data files...')

# ------------------------------------------------------------
# ---------------------- MAIN --------------------------------
# ------------------------------------------------------------

# defining the years to run the code for 
year_list = range(defines.over_write_years[0], defines.over_write_years[1]+1)

# land mask 
ds = xr.open_dataset(defines.topo_file)
lm = ds.lsm.isel(time=0).values
lm = (lm > defines.thresh_landsea)
ds.close()

# defining the dimensions of the composite values 
circ_dist_bins = np.arange(0, defines.circ['dist_max']+defines.circ['dist_div'], defines.circ['dist_div'])
circ_ang_bins = np.arange(-180., 180+defines.circ['ang_div'], defines.circ['ang_div'])*np.pi/180
circ_H_sum = np.zeros((len(circ_ang_bins)-1, len(circ_dist_bins)-1))
circ_H_cnt = np.zeros((len(circ_ang_bins)-1, len(circ_dist_bins)-1))

area_dist_bins = np.arange(-defines.area['dist_max'], defines.area['dist_max']+defines.area['dist_div'], defines.area['dist_div'])
area_H_sum = np.zeros((len(area_dist_bins)-1, len(area_dist_bins)-1))
area_H_cnt = np.zeros((len(area_dist_bins)-1, len(area_dist_bins)-1))

# composite analysis creating init variables
# ciruclar average, and area average
comp = {}
for hemis in defines.composite_hem_list: 
  comp[hemis] = {}
  for lm_type in ['land', 'ocean']: 
    comp[hemis][lm_type] = {}
    for var in defines.composite_var_list:
      comp[hemis][lm_type][var] = {}
      comp[hemis][lm_type][var]['circ_sum'] = np.zeros(circ_H_sum.shape)
      comp[hemis][lm_type][var]['circ_cnt'] = np.zeros(circ_H_cnt.shape)
      comp[hemis][lm_type][var]['area_sum'] = np.zeros(area_H_sum.shape)
      comp[hemis][lm_type][var]['area_cnt'] = np.zeros(area_H_cnt.shape)

# loop through all the years and create the composite
for year in year_list: 
  print('Debug: Reading in data ...', end=" ")

  # SLP data as the sample dataset
  # getting the reference longitude and latitude values
  slp_file = os.path.join(defines.model_data_directory, f'slp.{year}.nc')
  slp = xr.open_dataset(slp_file)
  reflon = slp.lon.values
  reflat = slp.lat.values

  # creating the co-ordinate grid
  lon, lat = np.meshgrid(reflon, reflat)

  # opening all the necessary variables to create the composites for
  ds_list = {}
  for var in defines.composite_var_list: 
    var_file = os.path.join(defines.model_data_directory, f'{var}.{year}.nc')
    ds_list[var] = xr.open_dataset(var_file)
  
  ############# Get Centers for the given date ######################
  in_file = os.path.join(defines.read_folder, f'{defines.model}_{year}.mat')
  all_centers = reader.read_center_from_mat_file(in_file)

  # loop through all time steps in the year
  for t_step in range(1, len(slp.time)):

    # creating a datetime variable for the current time step
    date = pd.Timestamp(slp.time[t_step].values).to_pydatetime()
    print(date)
  
    fd_date = date
    centers = all_centers.find_centers_for_date(fd_date)

    # looping through all the centers for the given data
    for i_center, _  in enumerate(centers.lat): 
      date_str = fd_date.strftime('%Y%m%d%H')

      center = {}
      for key in centers.keys():
        center[key] = centers[key][i_center]

      # skip all cyclones close to the equator or poles
      if (np.abs(center['lat']) > 60) | (np.abs(center['lat']) < 30): 
        continue

      if (center['lon'] > 40) & (center['lon'] < 320): 
        continue

      if (center['lat'] >= 0):
        hemis_type = 'NH'
      elif (center['lat'] < 0): 
        hemis_type = 'SH'

      # # debug: running only for edge cases
      # if not ((center['lon'] < -165) | (center['lon'] > 165)):
      #   continue

      # distance from given center
      dist_grid = common.compute_dist_from_cdt(lat, lon, center['lat'], center['lon'])
      
      # index of center of cyclone
      c_ind = np.nanargmin(dist_grid)
      cx, cy = np.unravel_index(c_ind, dist_grid.shape)
      lm_flag = lm[cx, cy]
      if (lm_flag): 
        lm_type = 'land'
      else:
        lm_type = 'ocean'

      for var in defines.composite_var_list: 
        ds_tstep = ds_list[var].isel(time=t_step)
        data = ds_tstep.pr.values

        # creating the circular average values and area average values
        circ_H = common.circular_avg_one_step(lat, lon, data, center['lat'], center['lon'], bins=(circ_dist_bins, circ_ang_bins))
        comp[hemis_type][lm_type][var]['circ_sum'] += circ_H.sum
        comp[hemis_type][lm_type][var]['circ_cnt'] += circ_H.cnt

        area_H = common.area_avg_one_step(lat, lon, data, center['lat'], center['lon'], bins=(area_dist_bins, area_dist_bins))
        comp[hemis_type][lm_type][var]['area_sum'] += area_H.sum
        comp[hemis_type][lm_type][var]['area_cnt'] += area_H.cnt
        # end for var

    # end i_center

    # if (date > dt.datetime(year, 1, 31)):
    #   break

  # end t_step

# end year

for hemis_type in defines.composite_hem_list:
  for var in defines.composite_var_list:
    for lm_type in ['land', 'ocean']:

      tmp_dict = comp[hemis_type][lm_type][var]

      plt.close('all')
      tmp = 86400*tmp_dict['circ_sum']/tmp_dict['circ_cnt']
      common.plot_polar(circ_H.y,  circ_H.x, tmp)
      plt.title(f'{var.upper()} {lm_type} {hemis_type}')
      plt.savefig(os.path.join(defines.images_folder, f'circ_{year}_{var}_{hemis_type}_{lm_type}.png'), dpi=300.)

      plt.close('all')
      tmp = 86400*tmp_dict['area_sum']/tmp_dict['area_cnt']
      common.plot_area(area_H.y_edges,  area_H.x_edges, tmp)
      plt.title(f'{var.upper()} {lm_type} {hemis_type}')
      plt.savefig(os.path.join(defines.images_folder, f'area_{year}_{var}_{hemis_type}_{lm_type}.png'), dpi=300.)

