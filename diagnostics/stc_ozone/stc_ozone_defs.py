"""
This module contains functions used in the Stratospheric Ozone and Circulation POD.

Contains:
    lat_avg (cosine-weighted averages over latitudes)
    calc_fsw (determines dates of final stratospheric warmings based on 
              monthly-mean data)
    l_trend (calculates linear trends as a function of pressure vs month) 
    t_test_corr (t-test for Pearson correlation coefficients)
              
"""

import numpy as np
import xarray as xr
import scipy
from scipy.stats import linregress
from cftime import DatetimeNoLeap

# ************************************************************************************


def lat_avg(ds, lat_lo, lat_hi):
    r""" Calculate a meridional average of data. The average is done using 
        cosine-latitude weighting. 

    Parameters
    ----------
    ds : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset for which to calculate a meridional
        average between the given latitude limits.
    
    lat_lo : Numeric quantity 
        The lower latitude limit (inclusive) for performing the meridional average

    lat_hi : Numeric quantity
        The upper latitude limit (inclusive) for performing the meridional average

    Returns
    -------
    ds_wgt : `xarray.DataArray` or `xarray.Dataset`
         The cos(lat) weighted average of the data between lat_lo and lat_hi

    Notes
    -----
    The input xarray variable ds is assumed to have a dimension named "lat". 
    E.g., if your data has a dimension named "latitude", use the rename method: 
        ds.rename({'latitude':'lat'})

    """

    # Limit the latitude range without assuming the ordering of lats
    ds_tmp = ds.isel(lat=np.logical_and(ds.lat >= lat_lo, ds.lat <= lat_hi))

    # Define the cos(lat) weights
    wgts = np.cos(np.deg2rad(ds_tmp.lat))
    wgts.name = "weights"

    # Apply weighting and take average
    ds_wgt_avg = ds_tmp.weighted(wgts).mean('lat')
    return ds_wgt_avg

# *************************************************************************************


def calc_fsw(u_50mb_60deglat, hemi):
    r""" Calculate the final stratospheric warming date (the date in spring when the 
    zonal winds fall below 5 m/s in the NH and 15 m/s in the SH). To do this using 
    monthly-mean data, we use a similar method to that of Hardimann et al. (2011).
    We assume the monthly-mean data represents the 15th of the month. We then
    calculate the first six harmonics of the full zonal-mean zonal wind time 
    series at 50 mb and 60 deg latitude for each year (using Fast Fourier Transform),
    then calculates when the smoothed harmonic time series crosses below 5 m/s in 
    boreal spring and 15 m/s in austral spring.

    Parameters
    ----------
    u_50mb_60deglat : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset which contains the monthly-mean zonal-mean 
        zonal wind time series at 50 mb and 60 deg latitude (60N for the NH and 60S for 
        the SH). Must have dimensions of "time".
    
    hemi : string 
        Should be either 'NH' or 'SH' for northern/southern hemisphere, 
        respectively
        
    Returns
    -------
    fsw : list
         List of dates of the final stratospheric warming, in YYYY-MM-DD format

    Notes
    -----
    Requires the scipy package to perform the FFT.
    Reference: Hardimann et al. 2011:
        https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011JD015914

    """

    np.seterr(divide='ignore')
    
    tmpu = u_50mb_60deglat
    
    # for data consistency, here force all monthly-means to be centered on the 15th of the month.
    oldyear = tmpu["time.year"]
    oldmo = tmpu["time.month"]
    dates = [DatetimeNoLeap(year, month, 15) for year, month in zip(oldyear, oldmo)]
    tmpu["time"] = dates
    
    fsw = []
    smth = xr.DataArray(data=[0], dims=["time"], coords=dict(time=['1900-12-15']))
    
    yrs = tmpu.groupby("time.year").mean().year.values
   
    # apply to each year separately 
    for i, y in enumerate(yrs):
        if hemi == 'NH':
            raw = tmpu.sel(time=tmpu.time.dt.year.isin([y]))
        if hemi == 'SH':
            raw = tmpu.sel(time=tmpu.time.dt.year.isin([y, y+1]))  # Need data to go into following year
            raw = raw.isel(time=slice(0, 14))  # reduce to just the first year +  Jan of following year
            
        def nharm(x):
            if x.any() == 0:
                return np.zeros(N)
            fft_output = scipy.fft.fft(x)
            freq = scipy.fft.fftfreq(len(x))
            filtered_fft_output = np.array([fft_output[i] if round(np.abs(1/f), 2) in
                                           [round(j, 2) for j in [N, N/2, N/3, N/4, N/5]]
                                            else 0 for i, f in enumerate(freq)])
            filtered_sig = scipy.fft.ifft(filtered_fft_output)
            filtered = filtered_sig.real

            return filtered
    
        N = len(raw)
        tmpvals = raw.values
        tmpvals2 = tmpvals.reshape(N, -1)       
        filt = np.apply_along_axis(nharm, 0, tmpvals2)
        filt = filt.reshape(N)
    
        xfiltered = xr.DataArray(filt, dims=('time'),
                                 coords={'time': raw.time})
        smth_new = xfiltered + raw.mean(dim='time')  
            
        if hemi == 'NH':
            smth_all = xr.concat([smth, smth_new], dim='time')
        if hemi == 'SH':
            smth_all = xr.concat([smth, smth_new.isel(time=slice(0, 12))], dim='time')
        
        if i == 0:
            smth = smth_all[1:]
        else:
            smth = smth_all
    
        # resample to Daily data. Note that this goes from Jan 1-Dec 1 in NH
        resamp = smth_new.resample(time='1D').interpolate('linear')
        
        if hemi == 'NH':
            # find where the resampled, smooth line crosses <5 m/s in boreal spring
            # then confirm that it doesn't return to >5 m/s within 60 days
            # If it does, then use next crossing below 5 m/s
            thresh = 5
            if resamp.where(resamp < thresh).isnull().all():
                print('No FSW detected')
                fsw_date = 'NaN'
            else:
                time1 = resamp.where(resamp < thresh, drop=True).isel(time=0).time
                resamp_new = resamp.sel(time=slice(time1.time,resamp.isel(time=-1).time))
                time2 = resamp_new.where(resamp_new > thresh, drop=True).isel(time=0).time
                if (time2.dt.dayofyear - time1.dt.dayofyear) < 60:
                    resamp_new = resamp.sel(time=slice(time2.time, resamp.isel(time=-1).time))
                    time3 = resamp_new.where(resamp_new < thresh, drop=True).isel(time=0).time
                    fsw_date = time3.dt.strftime("%Y-%m-%d").values.tolist()
                else:
                    fsw_date = time1.dt.strftime("%Y-%m-%d").values.tolist()
        if hemi == 'SH':
            # find where the resampled, smooth line crosses 15 m/s in austral spring
            thresh = 15
            if resamp[200:].where(resamp[200:] < thresh).isnull().all():
                print('No FSW detected')
                fsw_date = 'NaN'
            else:
                u_neg = resamp[200:].where(resamp[200:] < thresh, drop=True)
                fsw_date = u_neg.isel(time=0).time.dt.strftime("%Y-%m-%d").values.tolist()
        fsw.append(fsw_date)
    
    return fsw
# ********************************************************************************************************


def l_trend(var, start_yr, end_yr, sig=True):
    r""" Calculate a least squares linear fit trend line to each 
    grid of var as a function of month of year (i.e, trend for all Januarys, Februarys,
    etc.) between start_yr and end_yr. If sig=True (default), output
    the p-values of the trend lines.

    Parameters
    ----------
    var : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset for which to calculate trends,
        must have one dimension be time and one is pressure level.
    
    start_yr : Numeric quantity (string format) 
        The starting year of the trend (inclusive)

    end_yr : Numeric quantity (string format)
        The ending year of the trend (inclusive)
    sig: boolean value indicating whether to output the trend line p-values

    Returns
    -------
    A_trend : `xarray.DataArray` or `xarray.Dataset`
         Matrix of linear trends as a function of month and spatial 
         dimension
    
    A_pvalue : `xarray.DataArray` or `xarray.Dataset`
         Matrix of p-values as a function of month and spatial 
         dimension.

    Notes
    -----
    The input xarray variable var is assumed to have a dimension named "time",
    and a dimension named "lev". 
    Requires scipy.stats.linregress.

    """
    
    # applied to monthly data, the code produces trends per year (as a function of
    # month. To scale to "per decade", set SCALE to 10
    SCALE = 10.
    
    lev = var.lev.values
    
    A_trend = xr.DataArray(dims=["month", "lev"], coords=dict(
                           month=(["month"], np.arange(1, 13)),
                           lev=(["lev"], lev))
                           )
    
    A_pvalue = xr.DataArray(dims=["month","lev"], coords=dict(
                            month=(["month"], np.arange(1, 13)),
                            lev=(["lev"], lev))
                            )
    
    var = var.sel(time=slice(start_yr, end_yr))
    
    nlev = len(lev)
    for j in range(1, 13):
        vart = np.zeros(nlev)
        varp = np.zeros(nlev)
            
        # subset by month
        tmp = var.sel(time=(var['time.month'] == j))
        nt = len(tmp.time)
        N = range(nt)
        
        for i in range(nlev):
            v = tmp[:, i]
            # note: intercept, r_value, and std_err are unused variables but
            # we retain them here as dummy variables to serve as a reference
            # for what is available from linregress
            vart[i], intercept, r_value, varp[i], std_err = linregress(N, v)
        
        ind = A_trend["month"] == j
        A_trend[ind, ...] = vart*SCALE
        A_pvalue[ind, ...] = varp

    if not sig:
        return A_trend
    else:                  
        return A_trend, A_pvalue

# *******************************************************************************************************

# t-test (two-tailed) for Pearson correlation coefficients
# ttest variable is TRUE where NOT significant


def t_test_corr(alpha, r, n):
    
    tstat = r/np.sqrt((1-r**2)/(n-2))
    tcrit = scipy.stats.t.ppf(1-alpha/2., n-2)
    ttest = abs(tstat) < tcrit

    return ttest

# ********************************************************************************************************
# END 
# ********************************************************************************************************
