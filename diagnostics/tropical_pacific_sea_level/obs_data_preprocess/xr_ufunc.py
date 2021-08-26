#### Function for calculating trend and mean based from linear regression
from scipy import stats
import xarray as xr
import numpy as np


def da_linregress(da_data,xname="x",yname="y",tname="time",stTconfint=0.99,skipna=False):
    """
    The function calculate the trend of each trend in the gridded data. 
    Trend is calculated based on stats.linregress
    
    Input :
    da_data (xr.DataArray) - a 3 dimension data with the first dimension as the time axis,
    
    Output :
    da_slope (xr.DataArray) - a 2 dimension gridded data representing the linear trend
    da_intercept (xr.DataArray) - a 2 dimension gridded data representing the intercept
    da_r_value (xr.DataArray) - a 2 dimension gridded data representing the r value of the regress
    da_p_value (xr.DataArray) - a 2 dimension gridded data representing the p value of the linear trend
    da_std_err (xr.DataArray) - a 2 dimension gridded data representing the standard error of the linear trend
    da_conf (xr.DataArray) - a 2 dimension gridded data representing the confidence interval of the linear trend
    
    """
    if skipna == True:

        # make sure the order of the dataarray is correct
        da_data = da_data.transpose(tname,yname,xname)
        
        nx = len(da_data[xname])
        ny = len(da_data[yname])

        da_slope = da_data[0, :, :].copy() * np.nan
        da_intercept = da_slope.copy() * np.nan
        da_r_value = da_slope.copy() * np.nan
        da_p_value = da_slope.copy() * np.nan
        da_std_err = da_slope.copy() * np.nan
        da_conf = da_slope.copy() * np.nan

        for xx in range(nx):
            for yy in range(ny):
                da_ts = da_data[:, yy, xx].where(
                    da_data[:, yy, xx].notnull(), drop=True
                )
                if len(da_ts) > 0:
                    da_time = da_ts.time.copy()
                    year = da_ts["time.year"].values
                    month = da_ts["time.month"].values

                    da_time = year + month / 12.0

                    # perform linear regression
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        da_time, da_ts.values
                    )
                    da_slope[yy, xx] = slope
                    da_intercept[yy, xx] = intercept
                    da_r_value[yy, xx] = r_value
                    da_p_value[yy, xx] = p_value
                    da_std_err[yy, xx] = std_err

    else:
        da_time = da_data.time.copy()
        year = da_data["time.year"].values
        month = da_data["time.month"].values

        da_time = year + month / 12.0

        # Dask parallelization not working below. Load DataArray here
        da_data.load()

        # perform linear regression
        da_slope, da_intercept, da_r_value, da_p_value, da_std_err = xr.apply_ufunc(
            stats.linregress,
            da_time,
            da_data,
            input_core_dims=[["time"], ["time"]],
            output_core_dims=[[], [], [], [], []],
            vectorize=True,
        )

        # commented out Dask options
        # vectorize=True,dask='parallelized',
        # dask_gufunc_kwargs={"allow_rechunk":True})

    ### calculate confidence interval
    # calculate the error bar base on the number of standard error
    # the number related to dist. percentage is derived base on Students's T
    # distribution
    dof = len(da_time) - 1
    alpha = 1.0 - stTconfint
    nstd = stats.t.ppf(1.0 - (alpha / 2.0), dof)  # 2-side
    da_conf = nstd * da_std_err

    ds_linregress = xr.Dataset()
    ds_linregress["slope"] = da_slope
    ds_linregress["intercept"] = da_intercept
    ds_linregress["r"] = da_r_value
    ds_linregress["p"] = da_p_value
    ds_linregress["std_err"] = da_std_err
    ds_linregress["conf_int_%i" % (stTconfint * 100)] = da_conf

    return ds_linregress
