#!/usr/bin/env python
import numpy as np
import common
from netCDF4 import Dataset
import glob
import os

#debug 
from tqdm import tqdm
import matplotlib.pyplot as plt

# read in data  
folder = '/localdrive/drive10/jj/datacycs/out_nc/merra2/pr/2007'

# bins for histogram
dist_div = 50
ang_div = 20.
circ_dist_bins = np.arange(0, 1500+dist_div, dist_div)
circ_ang_bins = np.arange(-180., 180+ang_div, ang_div)*np.pi/180
# circ_H_sum = np.zeros((len(circ_dist_bins)-1, len(circ_ang_bins)-1))
# circ_H_cnt = np.zeros((len(circ_dist_bins)-1, len(circ_ang_bins)-1))
circ_H_sum = np.zeros((len(circ_ang_bins)-1, len(circ_dist_bins)-1))
circ_H_cnt = np.zeros((len(circ_ang_bins)-1, len(circ_dist_bins)-1))

dist_div = 50
area_dist_bins = np.arange(-1500, 1500+dist_div, dist_div)
area_H_sum = np.zeros((len(area_dist_bins)-1, len(area_dist_bins)-1))
area_H_cnt = np.zeros((len(area_dist_bins)-1, len(area_dist_bins)-1))

for file in tqdm(glob.glob(os.path.join(folder, '*.nc'))):
  nc = Dataset(file, 'r')
  nc.set_auto_mask(False)
  centerLat = nc.variables['fulllat'][:]
  centerLon = nc.variables['fulllon'][:]
  lat = nc.variables['latgrid'][:]
  lon = nc.variables['longrid'][:]
  data = nc.variables['data'][:]
  nc.close()

  if (np.any(np.isnan(lat))):
    continue
  
  for i in range(len(centerLat)):
    circ_H = common.circular_avg_one_step(lat[i, :, :], lon[i, :, :], data[i, :, :], centerLat[i], centerLon[i], bins=(circ_dist_bins, circ_ang_bins))
    circ_H_sum += circ_H.sum
    circ_H_cnt += circ_H.cnt

    area_H = common.area_avg_one_step(lat[i, :, :], lon[i, :, :], data[i, :, :], centerLat[i], centerLon[i], bins=(area_dist_bins, area_dist_bins))
    area_H_sum += area_H.sum
    area_H_cnt += area_H.cnt

plt.ion()
common.plot_polar(circ_H.y,  circ_H.x, 86400*circ_H_sum/circ_H_cnt)
common.plot_area(area_H.y_edges,  area_H.x_edges, 86400*area_H_sum/area_H_cnt)
plt.show()
