import xarray as xr
import numpy as np 
import os

year_list = [2018, 2018]
erai_folder = '/localdrive/drive6/erai/dl/'

for year in range(year_list[0], year_list[1]+1):
  ncfile = os.path.join(erai_folder, '')

# loading in merra2 inst6_3d_ana_Np data
ncid = Dataset('/localdrive/drive10/merra2/inst6_3d_ana_Np/MERRA2_300.inst6_3d_ana_Np.20070101.nc4', 'r')
ncid.set_auto_mask(False)
in_lon = ncid.variables['lon'][:]
in_lat = ncid.variables['lat'][:]
in_lev = ncid.variables['lev'][:]
in_time = np.asarray(ncid.variables['time'][:], dtype=float)

in_slp = ncid.variables['SLP']
T = ncid.variables['T']
U = ncid.variables['U']
V = ncid.variables['V']
geoH = ncid.variables['H']
PS = ncid.variables['PS']

# creating the cdt grid 
lon, lat = np.meshgrid(in_lon, in_lat)

# getting the index of the level 850
lev850 = np.where(in_lev == 850)[0][0]

print(' Completed!')
