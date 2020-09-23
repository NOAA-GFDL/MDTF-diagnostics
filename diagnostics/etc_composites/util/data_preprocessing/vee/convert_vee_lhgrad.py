from netCDF4 import Dataset
import numpy as np
import glob
import os

out_folder = '/mnt/drive1/jj/MCMS/in_data/VEE/LHGRAD/'
in_folder = '/mnt/drive1/jj/MCMS/orig_data/VEE/LHGRAD'
start_year = 2000
model_year_range = [11, 40]
# in_file_format = 'seasonal_3000xtopography_atl_pac.atmos_native.%04d010100-%04d123123.ps.nc'
in_file_format = 'seasonal_aquaplanet_limited_lh_gradual.atmos_native.%04d010100-%04d123123.ps.nc'
out_file_format = 'slp.%04d.nc'


def get_hours_since_year(time):
  ''' No leap year conversion of time since 01/01/0001 00:00:00 to time since start of year'''

  temp_time = time[0]

  while True:
    temp_time =  temp_time - 365. * 24.
    if (temp_time > 0.):
      time = time - 365.*24.
    else:
      break

  return time

def create_slp_file(nc_file, out_file, year):

  # Reading in the data
  ncid = Dataset(nc_file,'r')
  lat = ncid.variables['lat'][:] # lat
  lon = ncid.variables['lon'][:] # lon

  lat_e = ncid.variables['latb'][:] # lat edges
  lon_e = ncid.variables['lonb'][:] # lon edges
  ps = ncid.variables['ps'][:] # surface pressure, pascals
  time = ncid.variables['time'][:] # no_leap, time since 0001-01-01 00:00:00

  ncid.close()


  slp = ps/100 # converting to mb 
  # time = get_hours_since_1850(2005, time) # converting time from hours since start of year, to hours since 1850

  time = get_hours_since_year(time)

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

year = start_year
for num in range(model_year_range[0], model_year_range[1]+1):
  # nc_file  = '/mnt/drive1/jj/MCMS/VEE/seasonal_aquaplanet.atmos_native.%04d010100-%04d123123.ps.nc'%(num, num)

  # netcdf input file
  nc_file = os.path.join(in_folder, in_file_format%(num, num))

  # output file  
  out_part_file = out_file_format%(year)
  out_file = os.path.join(out_folder, out_part_file)

  # calling the function that creates the SLP variable
  create_slp_file(nc_file, out_file, year)

  print ('Completed Year %d'%(year))

  # incrementing the output year by one
  year += 1


