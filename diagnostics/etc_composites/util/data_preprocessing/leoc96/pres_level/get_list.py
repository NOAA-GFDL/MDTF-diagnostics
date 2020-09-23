import os
import glob
import xarray as xr
from netCDF4 import Dataset

out = '/mnt/drive6/LEOC96/level/atmos_level/ts/6hr/1yr/pres_var_list.txt'
fid = open(out, 'w')
file_list = glob.glob('/mnt/drive6/LEOC96/level/atmos_level/ts/6hr/1yr/*.nc') 
file_list.sort()
for fn in file_list:
  var_name = fn.split('.')[-2]
  print(var_name)
  ds = Dataset(fn, 'r')
  fid.write(f"{var_name:15s}: {ds.variables[var_name].getncattr('long_name')}\n")
fid.close()

out = '/mnt/drive6/LEOC96/atmos/ts/6hr/1yr/surf_var_list.txt'
fid = open(out, 'w')
file_list = glob.glob('/mnt/drive6/LEOC96/atmos/ts/6hr/1yr/*.nc') 
file_list.sort()
for fn in file_list:
  tmp = fn.split('/')[-1]
  if (tmp in ['test.nc', 'test_ci.nc', 'test']):
    continue
  var_name = fn.split('.')[-2]
  print(var_name)
  ds = Dataset(fn, 'r')
  fid.write(f"{var_name:15s}: {ds.variables[var_name].getncattr('long_name')}\n")
fid.close()
