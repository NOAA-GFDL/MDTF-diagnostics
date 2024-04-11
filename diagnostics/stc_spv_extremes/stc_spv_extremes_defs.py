"""
This module contains functions used in the Stratospheric Polar Vortex
Extremes POD.

Contains:
    standardize (standardize a variable)
    deseasonalize (remove daily climatology)
    lat_avg (cosine-weighted averages over latitudes)
    getConsecutiveValues
    ssw_cp07 (find central dates of SSWs)
    spv_vi (find central dates of VIs)
    composite (average pressure-time variable across events)
    ttest_1samp (one sample t-test)          
"""

import numpy as np
import xarray as xr
from scipy import stats

# ***********************************************************************************


def standardize(x):
    r""" Standardize a variable x by subtracting its mean and dividing by its standard
    deviation over the total time period.
    
    Parameters
    ----------
    x : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset for which to standardize, as a function of time
    """
    
    stand_x = (x - x.mean("time")) / x.std("time")
    
    return (stand_x)


# ***********************************************************************************

def deseasonalize(x):
    r""" remove the daily seasonal cycle by subtracting its mean over the total time period.
    Note that x should be organized by .groupby('dayofyear') 
    
    Parameters
    ----------
    x : `xarray.DataArray` or `xarray.Dataset`
        The input DataArray or Dataset for which to standardize, as a function of time
    """
    
    x_anom = (x - x.mean("time")) 
    
    return x_anom

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

# *****************************************************************************


def getConsecutiveValues(arr):
    """
    This calculates and groups consecutive values of an array of numbers, 
    which must be in an ascending order.
    """
    final = []
    end = 0
    start = 0
    if len(arr) == 1:
        final.append(arr)
    else:    
        for i in range(1, len(arr)):
            if arr[i] - arr[i-1] == 1:
                end = i
            else :
                if len(arr[start:end+1]) == 0:
                    final.append(arr[start:start+1])
                else:
                    final.append(arr[start:end+1])
                start = i
            if i == len(arr) - 1:
                if len(arr[start:end+1]) == 0:
                    final.append(arr[start:start+1])
                else:
                    final.append(arr[start:end+1])
    return final

# **************************************************************************


def ssw_cp07(variable, threshold=0, consec_days=20, hem="NH"):
    
    """
    This calculates central dates of sudden stratospheric warmings following the definition in
    Charlton and Polvani (2007).
    Read in reanalysis data of zonal-mean zonal wind U at 10 hPa and 60degLat

    Parameters:
    ----------------------------------------------------
    variable : `xarray.DataArray` 
              The input DataArray or Dataset of zonal-mean zonal wind U at 10 hPa 
              and 60 degLat as a function of time. 
              Note: time variable must be named "time"
              Note: if hem = 'SH', then zonal winds should be for 60 degS latitude
            
    threshold : Numeric quantity
              An optional variable to determine the value below which a SSW occurs; 
              default is 0 m/s
               
    consec_days : Numeric quantity
               The number of consecutive days required that the zonal winds remain
               above `threshold` for a SSW to be independent of the event before it;
               default is 20 days, as defined in Charlton and Polvani (2007).
        
    hem: String quantity
        An optional variable that applies code to either NH or SH; default is NH
    """
    
    year = variable.time.dt.year.values   
    yr = np.arange(year[0], year[-1]+1, 1)
    yr = yr.tolist()
    
    ssw_dates = []
    
    for y in yr:
        
        # look for mid-winter SSWs between Nov-Mar in the NH
        if hem == "NH":
            s_str = str(y) + "-11-01"
            e_str = str(y+1) + "-03-31"
            # print("Calculating NH SSWs for "+s_str+" to "+e_str)
            var = variable.sel(time=slice(s_str, e_str))
            # this variable enables check for final warming
            var_chk = variable.sel(time=slice(s_str, str(y+1) + "-04-30"))
        if hem == "SH":
            s_str = str(y) + "-06-01"
            e_str = str(y) + "-10-31"
            # print("Calculating SH SSWs for "+s_str+" to "+e_str)
            var = variable.sel(time=slice(s_str, e_str))
            var_chk = variable.sel(time=slice(s_str, str(y)+"-11-30"))  # this variable enables check for final warming
        
        var = var.assign_coords(dayofwinter=("time", np.arange(len(var.time.values))))
        var_chk = var_chk.assign_coords(dayofwinter=("time", np.arange(len(var_chk.time.values))))
        
        # Find instances where U1060 is less than threshold
        vor_neg = var.where(var < threshold, drop=True)
        
        # determine consecutive groups of easterlies
        dayswitheasterlies = getConsecutiveValues(vor_neg.dayofwinter.values)
        
        # if there's only one group, check for final warming and if no final warming, append central date to ssw_dates #
        if len(dayswitheasterlies) == 1:
            firstvalue = dayswitheasterlies[0][0]
            lastvalue = dayswitheasterlies[0][-1]

            # search over all winds between end of candidate central event and april 30th for 10 consecutive days of 
            # westerlies. if 10 consecutive days of westerlies are found, append the central date to ssws #
            windsafterwinter = var_chk[lastvalue:]
            westerlies = windsafterwinter.where(windsafterwinter > threshold, drop=True)

            if len(westerlies) > 0:
                westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                westerlygroupslength = [len(group) for group in westerlygroups]
                maxlength = np.nanmax(westerlygroupslength)
                if maxlength > 9:
                    ssw_dates.append(var.dayofwinter[firstvalue].time.dt.strftime("%Y-%m-%d").values.tolist())
        
        # if there are multiple 'groups,' first append the first central date using the exact same code as above #  
        # then, search for additional central dates that are not final warmings #
        if len(dayswitheasterlies) > 1:
        
            firstvalue = dayswitheasterlies[0][0]
            lastvalue = dayswitheasterlies[0][-1]
            windsafterwinter = var_chk[lastvalue:]

            westerlies = windsafterwinter.where(windsafterwinter > threshold, drop=True)
            if len(westerlies) > 0:
                westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                westerlygroupslength = [len(group) for group in westerlygroups]
                maxlength = np.nanmax(westerlygroupslength)
                if maxlength > 9:
                    ssw_dates.append(var.dayofwinter[firstvalue].time.dt.strftime("%Y-%m-%d").values.tolist())
        
        # search for multiple SSWs by looping over 'groups' #
        
        for i, v in enumerate(dayswitheasterlies):

            # "break" statement used b/c the loop always considers a group[i] and the next group[i+1], #
            # so the loop must be exited on the the 2nd to last index #

            if i+1 == len(dayswitheasterlies):
                break

            # Get the first/last index from the current group
            currentgroup = dayswitheasterlies[int(i)]
            last_currentgroup = currentgroup[-1]

            # Get the first index from the next (current+1) group
            nextgroup = dayswitheasterlies[int(i+1)]
            first_nextgroup = nextgroup[0]
            
            # If the groups are separated by "consec_days" of westerlies, check for final warming #
            if first_nextgroup - last_currentgroup > consec_days:
                # search over all winds between candidate central date and april 30th for 10 consecutive
                # days of westerlies #
                # if 10 consecutive days of westerlies are found, append the central date to ssw_dates #
                windsafterwinter = var_chk[first_nextgroup:]
                westerlies = windsafterwinter.where(windsafterwinter > threshold, drop=True)
                if len(westerlies) > 0:
                    westerlygroups = getConsecutiveValues(westerlies.dayofwinter.values)
                    westerlygroupslength = [len(group) for group in westerlygroups]
                    maxlength = np.nanmax(westerlygroupslength)
                    if maxlength > 9:
                        ssw_dates.append(var.dayofwinter[first_nextgroup].time.dt.strftime("%Y-%m-%d").values.tolist())
 
    return ssw_dates

# **************************************************************************


def spv_vi(variable, thresh=0.8, persist=10, consec_days=20, hem="NH"):
    
    """
    This calculates central dates of polar vortex intensifications (VIs), 
    which are defined using a percentile threshold of the climatology.
    Read in reanalysis data of zonal-mean zonal wind U at 10 hPa and 60degLat

    Parameters:
    ----------------------------------------------------
    variable : `xarray.DataArray` 
              The input DataArray or Dataset of zonal-mean zonal wind U at 10 hPa 
              and 60 degLat as a function of time. 
              Note: time variable must be named "time"
              Note: if hem = 'SH', then zonal winds should be for 60 degS latitude
    
    thresh : Numeric quantity
            The percentile (in fraction form, [0,1]) by which to define VIs as a
            daily percentile of the climatological values,
            default is 0.8
                       
    persist : Numeric quantity
               The number of consecutive days required that the zonal winds are sustained
               above `thresh` to be considered a VI event; default is 10
    
    consec_days :  Numeric quantity
        The number of consecutive days below the `thresh` for a VI to be independent of the event before it;
               default is 20 days
        
    hem: String quantity
        An optional variable that applies code to either NH or SH; default is NH
    """
    
    year = variable.time.dt.year.values   
    yr = np.arange(year[0],year[-1]+1,1)
    yr = yr.tolist()
    
    vi_dates = []
    
    month_day_str = xr.DataArray(variable.indexes['time'].strftime('%m-%d'), coords=variable.coords,
                                 name='month_day_str')
    daily_thresh = variable.groupby(month_day_str).quantile(thresh,dim='time')
 
    for y in yr:
        
        # look for mid-winter VIs between Nov-Mar in the NH, June-Oct in the SH
        if hem == "NH":
            # uses a fixed threshold representing the "thresh"*100 percentile of the NDJFM values
            
            if y == yr[-1]:
                break
            else:
                s_str = str(y)+"-11-01"
                e_str = str(y+1)+"-03-31"
                # print("Calculating NH VIs for "+s_str+" to "+e_str)
                var = variable.sel(time=slice(s_str,e_str))
                var_chk = variable.sel(time=slice(s_str,str(y+1)+"-04-30")) 
                var_th = xr.concat([daily_thresh.sel(month_day_str=slice('11-01','12-31')),
                                daily_thresh.sel(month_day_str=slice('01-01','03-31'))],dim='month_day_str')
                
                if len(var.time) == 151:
                    # remove leap days from climo for simplicity
                    var_th = var_th.where(~(var_th.month_day_str == '02-29'),drop=True)
        
        if hem == "SH":
            s_str = str(y) + "-06-01"
            e_str = str(y) + "-10-31"
            # print("Calculating SH VIs for "+s_str+" to "+e_str)
            var = variable.sel(time=slice(s_str, e_str))
            var_chk = variable.sel(time=slice(s_str, str(y)+"-11-30"))
            var_th = daily_thresh.sel(month_day_str=slice('06-01','10-31'))
        
        var = var.assign_coords(dayofwinter=("time", np.arange(len(var.time.values))))
        var_chk = var_chk.assign_coords(dayofwinter=("time", np.arange(len(var_chk.time.values))))
        new_thr = xr.DataArray(var_th.values, dims={'time': np.arange(len(var.time.values))})
        
        # Find instances where U1060 is greater than threshold
        vor_int = var.where(var > new_thr,drop=True) 

        # determine consecutive groups of days above threshold
        daysabovethreshold = getConsecutiveValues(vor_int.dayofwinter.values)
        # if there's only one group, check that winds are sustained for consec_days and append central date to vi_dates
        if len(daysabovethreshold) == 1:
            firstvalue = daysabovethreshold[0][0]
            lastvalue = daysabovethreshold[0][-1]
        
            if (lastvalue - firstvalue) > persist-1:
                vi_dates.append(var.dayofwinter[firstvalue].time.dt.strftime("%Y-%m-%d").values.tolist())

        if len(daysabovethreshold) > 1:  # if there are multiple 'groups':
            # search for multiple VIs by looping over 'groups' #
            last_date = np.array([])
            for i, v in enumerate(daysabovethreshold):
            
                # Get the first/last index from the current group
                currentgroup = daysabovethreshold[int(i)]
                first_currentgroup = currentgroup[0]
                last_currentgroup = currentgroup[-1]
            
                if (last_currentgroup - first_currentgroup) > persist-1:

                    if i == 0 or last_date.size == 0:  # on first iteration/event, no separation check needed
                        vi_dates.append(
                            var.dayofwinter[first_currentgroup].time.dt.strftime("%Y-%m-%d").values.tolist())
                        last_date = last_currentgroup  # this sets the last_date as the last date of a valid event
                    
                    else:
                        # Get the last index from the previous (current-1) group
                        if (first_currentgroup - last_date) > consec_days-1:
                            vi_dates.append(
                                var.dayofwinter[first_currentgroup].time.dt.strftime("%Y-%m-%d").values.tolist())
                            # this sets the last_date as the last date of a valid event
                            last_date = last_currentgroup

    return vi_dates

# **************************************************************************


def composite(variable, yre, mne, dye, lag_before=20, lag_after=60):
    
    """
    This averages a variable (with time and pressure level coordinates) across
    specified events, which must be provided as (same-length) integer arrays of event year,
    event month, and event day. The daily average across events is found for the time period
    lag_before the event to lag_after the event in days.

    Parameters:
    ----------------------------------------------------
    variable : `xarray.DataArray` 
              The input DataArray or Dataset as a function of time in days
              and pressure level. 

    yre : `numpy.Array`
            An integer array of event years
                       
    mne : `numpy.Array`
            An integer array of event months
            
    dye : `numpy.Array`
            An integer array of event days
            
    lag_before: `integer value`
            A single integer specifying how many days before the event to 
            composite. Default = 20
    
    lag_after: `integer value`
            A single integer specifying how many days after the event to 
            composite. Default = 60
            
    """
    
    from datetime import datetime,timedelta
    
    # initialize with first event
    count = np.arange(len(yre))
    cen = datetime(year=yre[0], day=dye[0], month=mne[0])
    en = cen + timedelta(days=lag_after-1)
    sta = cen - timedelta(days=lag_before)
    lag = np.arange(-lag_before, lag_after, 1)
    edate = en.strftime("%Y-%m-%d")
    stdate = sta.strftime("%Y-%m-%d")
    avgvar = variable.sel(time=slice(stdate, edate))
    avgvar = avgvar.assign_coords(time=lag)
    avgvar = avgvar.expand_dims(dim="event")
        
    for dat in count[1:]:
        cen = datetime(year=yre[dat], day=dye[dat], month=mne[dat])
        en = cen + timedelta(days=lag_after-1)
        sta = cen - timedelta(days=lag_before)
        edate = en.strftime("%Y-%m-%d")
        stdate = sta.strftime("%Y-%m-%d")
        newvar = variable.sel(time=slice(stdate, edate))
        newvar = newvar.assign_coords(time=lag)
        newvar = newvar.expand_dims(dim="event")
   
        allvar = xr.concat([avgvar, newvar], dim='event')
        avgvar = allvar
       
    return avgvar

# ****************************************************************************


def ttest_1samp(a, popmean, dim):
    """
    This is a two-sided test for the null hypothesis that the expected value
    (mean) of a sample of independent observations `a` is equal to the given
    population mean, `popmean`
   
    Inspired here: https://github.com/scipy/scipy/blob/v0.19.0/scipy/stats/stats.py#L3769-L3846
   
    Parameters
    ----------
    a : `xarray.DataArray`
        sample observation
    popmean : float or array_like
        expected value in null hypothesis, if array_like than it must have the
        same shape as `a` excluding the axis dimension
    dim : string
        dimension along which to compute test
   
    Returns
    -------
    mean : xarray
        averaged sample along which dimension t-test was computed
    pvalue : xarray
        two-tailed p-value
    """
    n = a[dim].shape[0]
    df = n - 1
    a_mean = a.mean(dim)
    d = a_mean - popmean
    v = a.var(dim, ddof=1)
    denom = np.sqrt(v / float(n))

    t = d / denom
    prob = stats.distributions.t.sf(np.fabs(t), df) * 2
    prob_xa = xr.DataArray(prob, coords=a_mean.coords)
    return a_mean, prob_xa

# **************************************************************************************
