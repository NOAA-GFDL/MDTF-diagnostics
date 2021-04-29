import numpy as np 
from netCDF4 import Dataset
import os
import pdb
import scipy.io as sio

def select_region(cyc, hemis):

  '''
  Select only the tracks that fall into the different hemispheres. 
  '''

  if (hemis == 'NH'):
    cdt_box = [0, 90, 0, 360]
  if (hemis == 'SH'):
    cdt_box = [-90, 0, 0, 360]

  lat = cyc[:]['fulllat']
  lon = cyc[:]['fulllon']

  # create a boolean array for the cyclone tracks, and select only the ones that fall into the region bounding box
  ind = np.zeros(cyc.shape[0], dtype=bool)
  for i in range(0, cyc.shape[0]):
    if (np.any((lon[i] > cdt_box[2]) & (lon[i] < cdt_box[3]) & (lat[i] > cdt_box[0]) & (lat[i] < cdt_box[1]))):
      ind[i] = True

  return cyc[ind]

def set_gridlengths(reflon, reflat, boxlen):

  boxlen = 45
  dx = np.abs(reflon[3] - reflon[2])
  dy = np.abs(reflat[3] - reflat[2])

  gridlen = np.round((boxlen/dx) + 1)
  if (np.mod(gridlen, 2) == 0):
    gridlen = gridlen-1
  
  gridleny = np.round((boxlen/dy) + 1)
  if (np.mod(gridlen, 2) == 0):
    gridleny = gridleny-1

  return gridlen, gridleny
