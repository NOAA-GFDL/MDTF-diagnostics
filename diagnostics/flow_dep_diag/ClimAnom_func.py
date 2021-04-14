import os
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime
import dask
import cftime
np.seterr(divide='ignore', invalid='ignore')

#function to calculate climatology anomalies for eah variable
def climAnom(var_path, var_name):

    ddir = var_path
    va = var_name

    ds = xr.open_dataset(ddir, decode_times = True)
    ds['time'] = ds.indexes['time'].to_datetimeindex()
    # Drop 1 dimensional coordinates
    ds = ds.squeeze()
    da = ds[va]
    da_ensmean = da.copy()
    #would need to make envt var or something so you could use either 'time' or 'S' as coordinate name without an issue
    da_day_clim = da_ensmean.groupby('time.dayofyear').mean('time')
    da_day_anom = da.groupby('time.dayofyear') - da_day_clim
    da_day_anom = da_day_anom.drop('dayofyear')

    return da_day_anom
