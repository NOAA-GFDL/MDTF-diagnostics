import numpy as np 
import xarray as xr 
import matplotlib.pyplot as plt 
import cartopy

# read in ERA-I all year SLP data (6-hr)
# all years of SLP should be given in one file...
in_file = '/localdrive/drive6/erai/slp/'
ds = xr.open_dataset(in_file)

ds.close()

# write the output as netcdf file 

out_file = '../../../../inputata/model/QBOi.EXP1.AMIP.001/6hr/QBOi.EXP1.AMIP.001.SLP.6hr.nc'

# # Format of the PRECT variable for 3hr is as follows: 
# 1. time - noleap, days since 1975-01-01 00:00:00
# 2. date - current date
# 3. lat - latitude
# 4. lon - longitude
# 5. time_bnds - time interval endpoints
# 6. SLP - mba, long_name, cell_methods: "time:mean"
