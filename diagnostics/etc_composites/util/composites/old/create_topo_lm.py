#!/usr/bin/python
from netCDF4 import Dataset
import numpy as np 
import os
import scipy.io as sio
import pdb
import matplotlib.pyplot as plt


model_name = 'erai'
out_folder = './topo_lm_data/'

if (model_name == 'merra2'): 
  topo_file = '/mnt/drive5/merra2/common/MERRA2_101.const_2d_asm_Nx.00000000.nc4'  
  nc = Dataset(topo_file, 'r')
  topo = np.squeeze(nc.variables['PHIS'][:])/9.8
  lm = np.squeeze(nc.variables['FRLAND'][:])
  nc.close()

  topo = np.moveaxis(topo, [0, 1], [1, 0])
  lm = np.moveaxis(lm, [0, 1], [1, 0])

elif (model_name == 'erai'):
  topo_file = '/mnt/drive1/processed_data/tracks/era_tracks/erai_hgt.mat'
  lm_file = '/mnt/drive1/processed_data/tracks/era_tracks/ERAI_newlm.mat'

  topo = sio.loadmat(topo_file)['erai_hgt'][:]
  lm = sio.loadmat(lm_file)['newlm'][:]
  
  topo = np.moveaxis(topo, [0, 1], [1, 0])
  lm = np.moveaxis(lm, [0, 1], [1, 0])


lat_len = topo.shape[0]
lon_len = topo.shape[1]

out_file = os.path.join(out_folder, '%s_topo.nc'%(model_name))
nc = Dataset(out_file, 'w')

nc.createDimension('lat', lat_len)
nc.createDimension('lon', lon_len)

topo_id = nc.createVariable('topo', np.float, ('lat', 'lon'))
lm_id = nc.createVariable('lm', np.int, ('lat', 'lon'))

topo_id[:] = topo
lm_id[:] = lm

nc.close()
