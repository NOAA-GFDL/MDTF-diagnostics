import os
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime
np.seterr(divide='ignore', invalid='ignore')

### Function to calculate climatology anomalies for each variable in the diagnostic.

time_var = os.environ["time_coord"] #set environment variable for time equal to var for function
#function to calculate climatology anomalies for eah variable
def climAnom(var_path, var_name):

    ds = xr.open_dataset(var_path, decode_times = True)
    ds[time_var] = ds.indexes[time_var].to_datetimeindex() #convert time to datetime so we can use groupby functionality
    # Drop 1 dimensional coordinates
    ds = ds.squeeze()
    da = ds[var_name]
    da_ensmean = da.copy()
    da_day_clim = da_ensmean.groupby('{time_coord}.dayofyear'.format(**os.environ)).mean(time_var) #.format(**os.environ)
    da_day_anom = da.groupby('{time_coord}.dayofyear'.format(**os.environ)) - da_day_clim
    da_day_anom = da_day_anom.drop('dayofyear')
    da_day_anom.to_netcdf("{WK_DIR}/model/netCDF/".format(**os.environ) + var_name + "_climAnom.nc")
    return da_day_anom
