#### Function for calculating trend and mean based from linear regression 
from scipy import stats
import xarray as xr
import numpy as np



def da_var_detrend_3d(da_var,dim='time'):
    """
    The function remove the trend in da_var
    Trend is calculated based on stats.linregress
    
    Input :
    da_ts (xr.DataArray) -  time series
    

    """
    # create same data array with same attribute
    da_new = da_var.copy()*np.nan
    
    # find NaN location
    notnull_ind = np.where(~np.isnan(da_var.values))
    
    # remove NaN (front of end of the time series) 
    # => cannot remove the NaN in the middle of the time series exist only in some points
    da_var = da_var.where(da_var.notnull(),drop=True)
        
    da_time = da_var.time.copy()
    year = da_var['time.year'].values
    month = da_var['time.month'].values
    da_time = year+month/12. 
    
#     # perform linear regression
#     da_slope, da_intercept, da_r_value, da_p_value, da_std_err\
#     =xr.apply_ufunc(
#         stats.linregress,\
#         da_time,da_var.load(),\
#         input_core_dims=[[dim],[dim]],\
#         output_core_dims=[[],[],[],[],[]],
#         vectorize=True,dask='allowed')
    
    # calculate linear model 
    da_linear=da_var.copy()*0.
    for tind,tt in enumerate(da_time):
        da_linear[tind,:,:]=tt*da_slope+da_intercept
    
    da_new[notnull_ind] = da_var.values-da_linear.values

    return da_new



def linregress_3d(da_data1,da_data2,dim='time'):
    
    # perform linear regression
    da_slope, da_intercept, da_r_value, da_p_value, da_std_err\
     =xr.apply_ufunc(
        stats.linregress,\
        da_data1,da_data2,\
        input_core_dims=[[dim],[dim]],\
        output_core_dims=[[],[],[],[],[]],
        vectorize=True,dask='allowed')
    
    dict1 = {}
    dict1['coeff'] = da_slope
    dict1['intercept'] = da_intercept
    dict1['r'] = da_r_value
    dict1['p'] = da_p_value
    dict1['err'] = da_std_err
    
    
    return dict1

def linregress_3d_skipna(da_data1,da_data2,xname='x',yname='y',stTconfint=0.99):
    """
    regress between two data with 3-d 
    first dimension must be TIME dim
    the regression is along the time dim
    
    """

    nx = len(da_data1[xname])
    ny = len(da_data1[yname])
    
    da_slope = da_data1[0,:,:].copy()*np.nan    
    da_intercept = da_slope.copy()*np.nan
    da_r_value = da_slope.copy()*np.nan
    da_p_value = da_slope.copy()*np.nan
    da_std_err = da_slope.copy()*np.nan
    da_conf = da_slope.copy()*np.nan

           
    for xx in range(nx):
        for yy in range(ny):
            da_ts1 = da_data1[:,yy,xx].where(da_data1[:,yy,xx].notnull(),drop=True)
            da_ts2 = da_data2[:,yy,xx].where(da_data2[:,yy,xx].notnull(),drop=True)
            if (len(da_ts1) > 0) & (len(da_ts2) > 0):
                # perform linear regression
                slope, intercept, r_value, p_value, std_err=stats.linregress(da_ts1.values,da_ts2.values)
                da_slope[yy,xx] = slope
                da_intercept[yy,xx] = intercept 
                da_r_value[yy,xx] = r_value
                da_p_value[yy,xx] = p_value
                da_std_err[yy,xx] = std_err
    
    ### calculate confidence interval 
    # calculate the error bar base on the number of standard error
    # the number related to dist. percentage is derived base on Students's T
    # distribution
    dof = len(da_time)-1
    alpha = 1.0-stTconfint
    nstd = stats.t.ppf(1.0-(alpha/2.0),dof)  # 2-side
    da_conf = nstd*da_std_err
    
    ds_linregress = xr.Dataset()
    ds_linregress['slope'] = da_slope
    ds_linregress['intercept'] = da_intercept 
    ds_linregress['r'] = da_r_value 
    ds_linregress['p'] = da_p_value 
    ds_linregress['std_err'] = da_std_err 
    ds_linregress['conf_int_%i'%(stTconfint*100)] = da_conf
    

    return ds_linregress



def da_ts_detrend(da_ts,skipna=True):
    """
    The function remove the trend in da_ts
    Trend is calculated based on stats.linregress
    
    Input :
    da_ts (xr.DataArray) -  time series
    

    """
    
    if skipna == True :
        notnull_ind = np.where(~np.isnan(da_ts.values))
        da_new = da_ts.copy()*np.nan
        da_ts = da_ts.where(da_ts.notnull(),drop=True)
        if len(da_ts) < 0:
            slope = np.nan
            return slope
        
    da_time = da_ts.time.copy()
    year = da_ts['time.year'].values
    month = da_ts['time.month'].values
    da_time = year+month/12. 
    
    # perform linear regression
    slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)
    
    linear =  da_time*slope+intercept
    da_new[notnull_ind] = da_ts.values-linear

    return da_new


def da_ts_trend(da_ts,skipna=True):
    """
    The function calculate the trend   
    Trend is calculated based on stats.linregress
    
    Input :
    da_ts (xr.DataArray) - time series
    
    Output :
    slope - output slope of the time series 
    
    One can use ds.apply(da_ts_trend) to apply the function to all time series in 
    the dataset
    
    """
    
    
    if skipna == True :
        da_ts = da_ts.where(da_ts.notnull(),drop=True)
        if len(da_ts) > 0:
            da_time = da_ts.time.copy()
            year = da_ts['time.year'].values
            month = da_ts['time.month'].values

            da_time = year+month/12. 
            # perform linear regression
            slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)
            
    
    else:
        da_time = da_data.time.copy()
        year = da_data['time.year'].values
        month = da_data['time.month'].values

        da_time = year+month/12. 

        # perform linear regression
        slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)
    

    return slope


def da_ts_trend_conf(da_ts,stTconfint=0.99,skipna=True):
    """
    The function calculate the trend confidence interval 
     Trend is calculated based on stats.linregress
    
    Input :
    da_ts (xr.DataArray) - time series
    
    Output :
    conf - output slope confidence interval 
    
    One can use ds.apply(da_ts_trend_conf) to apply the function to all time series in 
    the dataset
    
    
    """
    
    
    if skipna == True :
        da_ts = da_ts.where(da_ts.notnull(),drop=True)
        if len(da_ts) > 0:
            da_time = da_ts.time.copy()
            year = da_ts['time.year'].values
            month = da_ts['time.month'].values

            da_time = year+month/12. 

            # perform linear regression
            slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)
            
    
    else:
        da_time = da_data.time.copy()
        year = da_data['time.year'].values
        month = da_data['time.month'].values

        da_time = year+month/12. 

        # perform linear regression
        slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)
        
    
    ### calculate confidence interval 
    # calculate the error bar base on the number of standard error
    # the number related to dist. percentage is derived base on Students's T
    # distribution
    dof = len(da_time)-1
    alpha = 1.0-stTconfint
    nstd = stats.t.ppf(1.0-(alpha/2.0),dof)  # 2-side
    conf = nstd*std_err

    return conf



def da_linregress(da_data,xname='x',yname='y',stTconfint=0.99,skipna=False):
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
    if skipna == True :
        
        nx = len(da_data[xname])
        ny = len(da_data[yname])
        
        da_slope = da_data[0,:,:].copy()*np.nan
        da_intercept = da_slope.copy()*np.nan
        da_r_value = da_slope.copy()*np.nan
        da_p_value = da_slope.copy()*np.nan
        da_std_err = da_slope.copy()*np.nan
        da_conf = da_slope.copy()*np.nan
           
        for xx in range(nx):
            for yy in range(ny):
                da_ts = da_data[:,yy,xx].where(da_data[:,yy,xx].notnull(),drop=True)
                if len(da_ts) > 0:
                    da_time = da_ts.time.copy()
                    year = da_ts['time.year'].values
                    month = da_ts['time.month'].values

                    da_time = year+month/12. 

                    # perform linear regression
                    slope, intercept, r_value, p_value, std_err=stats.linregress(da_time,da_ts.values)

#                     print(xx,yy,slope)
                    da_slope[yy,xx] = slope
                    da_intercept[yy,xx] = intercept 
                    da_r_value[yy,xx] = r_value
                    da_p_value[yy,xx] = p_value
                    da_std_err[yy,xx] = std_err
    
    else:
        da_time = da_data.time.copy()
        year = da_data['time.year'].values
        month = da_data['time.month'].values

        da_time = year+month/12. 

        # perform linear regression
        da_slope, da_intercept, da_r_value, da_p_value, da_std_err\
        =xr.apply_ufunc(
            stats.linregress,\
            da_time,da_data,\
            input_core_dims=[['time'],['time']],\
            output_core_dims=[[],[],[],[],[]],
            vectorize=True,dask='allowed')
    
    ### calculate confidence interval 
    # calculate the error bar base on the number of standard error
    # the number related to dist. percentage is derived base on Students's T
    # distribution
    dof = len(da_time)-1
    alpha = 1.0-stTconfint
    nstd = stats.t.ppf(1.0-(alpha/2.0),dof)  # 2-side
    da_conf = nstd*da_std_err
    
    ds_linregress = xr.Dataset()
    ds_linregress['slope'] = da_slope
    ds_linregress['intercept'] = da_intercept 
    ds_linregress['r'] = da_r_value 
    ds_linregress['p'] = da_p_value 
    ds_linregress['std_err'] = da_std_err 
    ds_linregress['conf_int_%i'%(stTconfint*100)] = da_conf
    

    return ds_linregress



def linregress_trend_mean(da_time,da_data,dim='time'):
    
    # perform linear regression
    da_slope, da_intercept, da_r_value, da_p_value, da_std_err\
    =xr.apply_ufunc(
        stats.linregress,\
        da_time,da_data,\
        input_core_dims=[[dim],[dim]],\
        output_core_dims=[[],[],[],[],[]],
        vectorize=True,dask='allowed')
    
    # calculate linear model 
    da_linear=da_data.copy()*0.
    ndim=da_linear.ndim
    if ndim == 3:
        for tind,tt in enumerate(da_time.values):
            da_linear[tind,:,:]=tt*da_slope+da_intercept
    elif ndim == 1:
        for tind,tt in enumerate(da_time.values):
            da_linear[tind]=tt*da_slope+da_intercept
    
    da_mean=xr.apply_ufunc(np.mean,da_linear,\
                 input_core_dims=[[dim]],\
                 vectorize=True)
    
    return da_mean,da_slope


#### function for calculate area array for obs
from spherical_area import cal_area

def cal_area_vec_obs(da_lon,da_lat,lonname,latname):
    
    # output unite : cm^2
    da_dlon=da_lon.copy()*0.
    da_dlon.values[1:]=da_lon.diff(lonname).values
    da_dlon.values[0]=da_dlon.values[1]
    
    da_dlat=da_lat.copy()*0.
    da_dlat.values[1:]=da_lat.diff(latname).values
    da_dlat.values[0]=da_dlat.values[1]
    
    da_area=xr.apply_ufunc(cal_area, 
                           da_lon, 
                           da_lat, 
                           da_dlon, 
                           da_dlat,
                           vectorize=True)
    return da_area

