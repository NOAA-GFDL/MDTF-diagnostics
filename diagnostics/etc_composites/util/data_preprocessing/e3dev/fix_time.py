#!/usr/bin/python 
import numpy as np 
from netCDF4 import Dataset
import os
import pdb

def get_hours_since_year(time, year):
  '''Get time variable for a given year'''
  time_size = time.shape[0]

  time_delta = 6
  time = np.arange(0, (time_size)*time_delta, time_delta)

  return time

def create_slp_file(nc_file, out_file, year):

  # Reading in the data
  ncid = Dataset(nc_file,'r')
  lat = ncid.variables['lat'][:] # lat
  lon = ncid.variables['lon'][:] # lon

  ps = ncid.variables['slp'][:] # surface pressure, pascals
  time = ncid.variables['time'][:] # no_leap, time since 0001-01-01 00:00:00

  ncid.close()


  slp = ps/100 # converting to mb 

  # getting the time variable for a given year, as hours since year-01-01 00:00:00
  time = get_hours_since_year(time, year)

  ncid = Dataset(out_file, 'w')

  ncid.createDimension('lon',lon.shape[0])
  ncid.createDimension('lat',lat.shape[0])
  ncid.createDimension('time',time.shape[0])

  nc_lon = ncid.createVariable('lon', np.float32, ('lon',))
  nc_lat = ncid.createVariable('lat', np.float32, ('lat',))
  nc_time = ncid.createVariable('time', np.float32, ('time',))
  nc_slp = ncid.createVariable('slp', np.float32, ('time','lat','lon'))

  nc_lat.units = 'degrees_north'
  nc_lon.units = 'degrees_east'
  nc_time.units = 'hours since %d-01-01 00:00:00'%(year)
  nc_slp.units = 'mb'

  nc_lat.axis = 'Y'
  nc_lon.axis = 'X'
  nc_time.calendar = '365_day'
  nc_slp.long_name = 'Sea Level Pressure'

  nc_lat[:] = lat
  nc_lon[:] = lon
  nc_time[:] = time
  nc_slp[:] = slp

  ncid.close()

##############################################################
######################## MAIN ################################
##############################################################

out_folder = '/mnt/drive1/jj/MCMS/in_data/E3dev/'
in_folder = '/localdrive/drive7/E3dev_L104_gse2018Nov15/subdaily/'
start_year = 2010
model_year_range = [2010, 2013]
in_file_format = 'slp.%04d.time.nc'
out_file_format = 'slp.%04d.nc'

year = start_year
for num in range(model_year_range[0], model_year_range[1]+1):

  # netcdf input file
  nc_file = os.path.join(in_folder, in_file_format%(num))

  # output file  
  out_part_file = out_file_format%(year)
  out_file = os.path.join(out_folder, out_part_file)

  # calling the function that creates the SLP variable
  create_slp_file(nc_file, out_file, year)

  print ('Completed Year %d'%(year))

  # incrementing the output year by one
  year += 1


