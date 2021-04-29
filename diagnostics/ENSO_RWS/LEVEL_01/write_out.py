import numpy as np
import os.path

import netCDF4 as nc
from netCDF4 import Dataset 

def write_out( lons, lats, plevs, variable, unit, dataout,  prefixout, undef):
##   construct the output name 
    nameout = os.path.join( prefixout + variable + ".nc")
    os.system("rm " + nameout + " 2> /dev/null")
##  write netcdf file 

    fid = Dataset( nameout, 'w', format='NETCDF3_CLASSIC')

    fid.description = "ENSO seasonal composite  " 

    ndims =  dataout.ndim

    time = fid.createDimension('time',  1)
    time = fid.createVariable('time', np.float32, ('time'))
    time.units = 'hours since 1900-01-01 00:00:00'
    time.calendar = "standard"
    time.axis = "T" 
    fid.variables['time'][:] = 0.


    if( ndims == 3 ):
        xyz   =  dataout.shape

        imax = xyz[0]
        jmax = xyz[1]
        zmax = xyz[2]

        lat = fid.createDimension('lat',  jmax)     # latitude axis
        lon = fid.createDimension('lon',  imax)    # longitude axis
        lev = fid.createDimension('lev',  zmax) # 

        lat = fid.createVariable('lat', np.float32, ('lat'))
        lat.units = 'degrees_north'
        lat.long_name = 'latitude'
        lat.axis = "Y"

        lon = fid.createVariable('lon', np.float32, ('lon'))
        lon.units = 'degrees_east'
        lon.long_name = 'longitude'
        lon.axis = "X"

        lev = fid.createVariable('lev', np.float32, ('lev'))
        lev.units = '[mb]'
        lev.long_name = 'pressure'
        lev.positive = 'down'
        lev.axis = "Z"
        
###  
        fid.variables['lev'][:] = plevs
        fid.variables['lat'][:] = lats
        fid.variables['lon'][:] = lons
   
        nc_var = fid.createVariable( variable, np.float32,  ('time', 'lev', 'lat', 'lon'), fill_value=undef)
        nc_var.units = unit
        nc_var.standard_name = variable
        xdataout =  np.zeros((1,zmax,jmax,imax),dtype='float32')

        xdataout[0,:,:,:] = np.swapaxes(dataout,0,2)
        fid.variables[ variable][:] = xdataout ###  np.swapaxes(dataout,0,2)
        fid.close() 


    if( ndims == 2 ):
        xyz   =  dataout.shape

        imax = xyz[0]
        jmax = xyz[1]

        lat = fid.createDimension('lat',  jmax)     # latitude axis
        lon = fid.createDimension('lon',  imax)    # longitude axis

        lat = fid.createVariable('lat', np.float32, ('lat'))
        lat.units = 'degrees_north'
        lat.long_name = 'latitude'
        lat.axis = "Y"

        lon = fid.createVariable('lon', np.float32, ('lon'))
        lon.units = 'degrees_east'
        lon.long_name = 'longitude'
        lon.axis = "X"

###
        fid.variables['lat'][:] = lats
        fid.variables['lon'][:] = lons

        nc_var = fid.createVariable( variable, np.float32,  ('lat', 'lon'), fill_value=undef)
        nc_var.units = unit
        nc_var.standard_name = variable

        fid.variables[ variable][:] = np.swapaxes(dataout,0,1)
        xdataout =  np.zeros((1,jmax,imax),dtype='float32')

        xdataout[0,:,:] = np.swapaxes(dataout,0,1)
        fid.variables[ variable][:] = xdataout
        fid.close()
