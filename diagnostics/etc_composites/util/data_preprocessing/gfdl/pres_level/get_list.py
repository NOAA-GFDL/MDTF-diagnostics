import os
import glob
import xarray as xr
from netCDF4 import Dataset

out = '/mnt/drive3/gfdl/6HRLY/KLEV/pres_var_list.txt'
fid = open(out, 'w')
file_list = glob.glob('/mnt/drive3/gfdl/6HRLY/KLEV/*.nc') 
file_list.sort()
for fn in file_list:
  var_name = fn.split('.')[-2]
  print(var_name)
  ds = Dataset(fn, 'r')
  fid.write(f"{var_name:15s}: {ds.variables[var_name].getncattr('long_name')}\n")
fid.close()

out = '/mnt/drive3/gfdl/6HRLY/SURF/surf_var_list.txt'
fid = open(out, 'w')
file_list = glob.glob('/mnt/drive3/gfdl/6HRLY/SURF/*.nc') 
file_list.sort()
for fn in file_list:
  tmp = fn.split('/')[-1]
  if (tmp in ['test.nc', 'test_ci.nc', 'test']):
    continue
  print(fn)
  var_name = fn.split('.')[-2]
  print(var_name)
  ds = Dataset(fn, 'r')
  fid.write(f"{var_name:15s}: {ds.variables[var_name].getncattr('long_name')}\n")
fid.close()
