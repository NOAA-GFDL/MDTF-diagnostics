import numpy as np
import os.path
import sys

from numpy import dtype
from sys import byteorder

from scipy.io import netcdf

def read_netcdf_3D(imax, jmax,  zmax, tmax,  variable,  namein, dataout, undef):

##  read in  data from NetCDF file 

 if(os.path.exists( namein)):
     nc = netcdf.netcdf_file( namein, 'r')
     vvar2 = nc.variables[ variable][:]
     dataout1 = vvar2.copy()
     dataout = np.transpose( dataout1)
     dataout = np.ma.masked_greater_equal( dataout, undef, copy=False)
     vvar2 = []
     nc.close()
 else:
     print (" missing file " +  namein )
     print (" needed for the calculations ")
     print (" exiting read_netcdf.py ")
     sys.exit()

 
 return dataout.filled(fill_value = undef)
   
