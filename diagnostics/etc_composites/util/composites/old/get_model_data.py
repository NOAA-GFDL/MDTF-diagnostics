import os
import numpy as np 
from netCDF4 import Dataset
from datetime import date

def get_erai(var_name, select_year):
  '''
  Read in era interim data from the netcdf files
  '''
  if (var_name == 'slp'):
    model_pre_folder = '/mnt/drive5/ERAINTERIM/SLP'
    model_file = os.path.join(model_pre_folder, 'SLP_%d.nc'%(select_year))
    model_var_name = 'msl'

  ncid = Dataset(model_file, 'r')
  var_data = ncid.variables[model_var_name][:]
  ncid.close()
  full_date = get_model_date(select_year, 'julian')

  return var_data, full_date

def get_merra2(var_name, select_year):
  '''
  Read in MERRA-2 data from the netcdf files
  '''
  if (var_name == 'slp'):
    model_pre_folder = '/mnt/drive5/merra2/six_hrly/'
    model_file = os.path.join(model_pre_folder, 'MERRA_%d_slv.nc'%(select_year))
    model_var_name = 'slp'
  
  ncid = Dataset(model_file, 'r')
  var_data = ncid.variables[model_var_name][:]
  ncid.close()
  full_date = get_model_date(select_year, 'julian')

  return var_data, full_date


def get_data(in_folder, model_name, var_name, select_year):
  '''
  Read in MERRA-2 data from the netcdf files
  '''
  model_pre_folder = in_folder
  model_file = os.path.join(model_pre_folder, '%s_%d.nc'%(model_name, select_year))
  model_var_name = var_name
  
  ncid = Dataset(model_file, 'r')
  var_data = ncid.variables[model_var_name][:]
  ncid.close()

  full_date = get_model_date(select_year, 'julian')

  return var_data, full_date



######################### CREATE MODEL TIME 
def get_model_date(select_year, calendar_type):
  if (calendar_type == 'julian'):
    # have to add 366 to get matlab datenum
    full_date = np.arange(date.toordinal(date(select_year, 1, 1))+366., date.toordinal(date(select_year, 12, 31))+366.+1., .25)
  
  return full_date
