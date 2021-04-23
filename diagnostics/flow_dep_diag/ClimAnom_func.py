import os
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime
import dask
import cftime
np.seterr(divide='ignore', invalid='ignore')

time_var = os.environ["time_coord"]
#function to calculate climatology anomalies for eah variable
def climAnom(var_path, var_name):

    ddir = var_path
    va = var_name

    ds = xr.open_dataset(ddir, decode_times = True)
    ds[time_var] = ds.indexes[time_var].to_datetimeindex()
    # Drop 1 dimensional coordinates
    ds = ds.squeeze()
    da = ds[va]
    da_ensmean = da.copy()
    #would need to make envt var or something so you could use either 'time' or 'S' as coordinate name without an issue
    da_day_clim = da_ensmean.groupby('{time_coord}.dayofyear'.format(**os.environ)).mean(time_var) #.format(**os.environ)
    da_day_anom = da.groupby('{time_coord}.dayofyear'.format(**os.environ)) - da_day_clim
    da_day_anom = da_day_anom.drop('dayofyear')

    return da_day_anom
