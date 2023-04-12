# ==============================================================================
# MDTF Strat-Trop Coupling: Annular Modes POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Annular Modes POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt). It defines
# the diagnostic computation functions used by the main driver script.

import numpy as np
import xarray as xr

from scipy import signal
from scipy import ndimage
from scipy import optimize

from eofs.xarray import Eof


def longest_chain_zeros(arr):
    r""" A utility function for finding the indices that
    span the longest chain of zeros in a 1D input array.
    Below, it is used to determine whether there is enough 
    good data following the EOF analysis for the PC time 
    series (meant to represent the annular modes) to be
    meaningful.

    Parameters
    ----------
    arr : `np.array`
        A 1D numpy array
    
    Returns
    -------
    (start, end)
        A tuple containing the indices start and end, which
        bracket the longest chain of zeros (Falses) in arr.
        Function will return None,None if there are no 
        zeros in arr.

    """
    
    if len(arr) == 0:
        raise ValueError("Input array is empty")
    
    # Turn input into boolean array
    bool_arr = arr.astype('bool')
    
    # Bracket the beginning and ending with Trues to handle 
    # edge cases in which we have Falses at beginning or end
    # of array, so these get properly bracketed
    bool_arr = np.concatenate(([True], bool_arr, [True]))
    
    # Locate indices where bool_arr switches between True/False
    nonzero_diff_ixs = np.where(np.diff(bool_arr))[0]
    if len(nonzero_diff_ixs) == 0:
        return None,None
    
    # Calculate the lengths of these spans
    lengths = nonzero_diff_ixs[1::2] - nonzero_diff_ixs[:-1:2]
    
    # Get the index of the max length span
    max_len_idx = np.argmax(lengths)
    
    # Compute the start/end indices that bracket these
    start = nonzero_diff_ixs[2*max_len_idx]
    end = nonzero_diff_ixs[2*max_len_idx+1] - 1
    
    return start, end


def detrend_xr(da):
    r"""A small utility function for linearly detrending an xarray
    DataArray across a "GroupBy" dimension. Uses the scipy detrend
    function.

    Parameters
    ----------
    da : `xarray.DataArray`
        The input DataArray

    Returns
    -------
    The detrended data across the 0th axis

    """
    return signal.detrend(da, axis=0)


def gauss_smooth_doy(dat, n=90):
    r"""A small utility function for smoothing a dayofyear
    timeseries with a Gaussian filter. It is generally used
    with xr.apply_ufunc. The function is written to be consistent
    with the Gaussian smoothing approach outlined in
    Simpson et al., 2011 (see references), using sigma = 18.

    Parameters
    ----------
    dat : `np.array` or `xarray.DataArray`
        The input data; function assumes its 0th dimension corresponds
        to dayofyear
    n : int
        The number of days before and after the dayofyear in question
        to include in the smoothing. Defaults to 90 to use approximately
        half a year

    Returns
    -------
    smth : `np.array`
        The smoothed output data.

    References
    ----------
    Simpson, I. R., Hitchcock, P., Shepherd, T. G., and Scinocca, J. F. (2011),
        Stratospheric variability and tropospheric annular-mode timescales,
        Geophys. Res. Lett., 38, L20806, doi:10.1029/2011GL049304.

    """

    smth = np.zeros(dat.shape)
    for i in range(dat.shape[0]):
        rolled = np.roll(dat, -i, axis=0)
        dummy_ts = np.concatenate((rolled[-n:, :], rolled[0 : n + 1, :]))
        tmp = ndimage.gaussian_filter1d(dummy_ts, 18, axis=0)
        smth[i, :] = tmp[n, ...]

    return smth


def smooth_climo(clim, ndays, mode="wrap"):
    r"""Smooths a climatology time series using a centered running mean.

    Parameters
    ----------
    clim : `xarray.DataArray`
        The input DataArray corresponding to the climatology.
        Assumed to have a "dayofyear" dimension.

    ndays : int
        The number of days to use in the running mean.

    mode : str (kwarg)
        How to handle padding the time series. Defaults to "wrap" so that
        values at the beginning are padded from values at the end, and
        vice versa. If the dayofyear dimension does not span a full year,
        a different mode should be used.

    Returns
    -------
    clim_smth : `xarray.DataArray`
        The smoothed version of the input climatology.

    """
    pad_size = ndays // 2
    clim_pad = clim.pad(dayofyear=pad_size, mode=mode)
    clim_smth = (
        clim_pad.rolling(dayofyear=ndays, center=True)
        .mean()
        .isel(dayofyear=slice(pad_size, -1 * pad_size, 1))
    )

    return clim_smth


def remove_global_mean(da):
    r"""Removes the global mean of an input field. Uses a cos(lat) weighted
        average over all latitudes to perform the global mean.

    Parameters
    ----------
    da : `xarray.DataArray`
        The input DataArray for which to remove the global mean.

        Assumed to have a globally spanning "lat" dimension

    Returns
    -------
    anom : `xarray.DataArray`
         da with the corresponding global mean subtracted

    """

    wgts = np.cos(np.deg2rad(da.lat))
    da_global = da.weighted(wgts).mean("lat").astype("float32")
    anom = da - da_global
    return anom


def remove_simple_smoothed_climo(da, ndays=15):
    r"""Removes a smoothed climatology from input data. The smoothed
    climatology is computed by taking a centered running mean of the
    raw "noisy" climatology.

    Parameters
    ----------
    da : `xarray.DataArray`
        The input DataArray for which to compute anomalies.
        Assumed to have a "time" axis corresponding to daily, year-round data.

    ndays : int (kwarg)
        The width of the running mean in number of days. Defaults to 15 days.

    Returns
    -------
    anom : `xarray.DataArray`
         da with the corresponding smooth climatology subtracted

    See Also
    --------
    smooth_climo

    """

    climo = smooth_climo(da.groupby("time.dayofyear").mean("time"), ndays)
    anom = da.groupby("time.dayofyear") - climo
    return anom


def remove_trend_climo(da):
    r"""Removes a slowly varying "trend climatology" as discussed
    in Gerber et al., 2010. See references below. This is done by
    applying a 60-day lowpass filter to daily data, and then
    by applying a 30 year lowpass filter to each point across
    the days-of-year in the dataset.

    Parameters
    ----------
    da : `xarray.DataArray`
        The input DataArray or Dataset for which to compute anomalies.
        Assumed to have a "time" axis corresponding to daily, year-round data.

    Returns
    -------
    anom : `xarray.DataArray` or `xarray.Dataset`
        da with the corresponding "trend climatology" subtracted

    References
    ----------
    Gerber, E. P., et al. (2010), Stratosphere-troposphere coupling and annular
        mode variability in chemistry-climate models, J. Geophys. Res., 115,
        D00M06, doi:10.1029/2009JD013770.

    """

    # First apply 60-day lowpass filter across daily timesteps
    order, wn = signal.buttord((1.0 / 60.0) / 0.5, (1.0 / 30.0) / 0.5, 1, 10)
    sos = signal.butter(order, wn, "low", output="sos")
    da_filt = xr.apply_ufunc(
        signal.sosfiltfilt, sos, da, kwargs={"axis": da.get_axis_num("time")}
    )

    # Then apply a 30-year lowpass filter across days of the year
    order, wn = signal.buttord((1.0 / 30.0) / 0.5, (1.0 / 10.0) / 0.5, 1, 10)
    sos = signal.butter(order, wn, "low", output="sos")
    da_filt_doy = xr.apply_ufunc(
        signal.sosfiltfilt, sos, da_filt.groupby("time.dayofyear"), kwargs={"axis": 0}
    )

    anom = da - da_filt_doy
    return anom


def anomalize_geohgt(z, hemi, anom="simple"):
    r"""A utility function for computing zonal mean geopotential height
    in a manner appropriate for using EOF analysis to compute annular
    mode indices.

    Parameters
    ----------
    z : `xarray.DataArray`
        The input geopotential height data. Should be global, but zonal means
        (i.e., having no dimension corresponding to longitude)

    hemi : int
        The hemisphere to "anomalize". Should be -1 for SH or 1 for NH.
        The function will return the data poleward of 20 degrees lat
        for the corresponding data.

    anom : str (kwarg)
        Which recipe to use for computing the anomalies. Valid options
        are "simple" or "gerber". Simple removes a running-mean-smoothed
        climatology and detrends the anomalies across the days-of-year.
        Gerber removes a "trend climatology" as specified in the
        "remove_trend_climo" function.

    Returns
    -------
    z_anom : `xarray.DataArray`
        The geopotential height anomalies poleward of 20 degrees latitude
        for the corresponding hemisphere.

    See also
    --------
    remove_simple_smoothed_climo
    remove_trend_climo

    """
    if hemi not in ["SH", "NH"]:
        msg = "The hemi argument must be either -1 for the SH, or 1 for the NH"
        raise ValueError(msg)
    if anom not in ["simple", "gerber"]:
        msg = 'The anom keyword argument must be one of "simple" or "gerber"'
        raise ValueError(msg)

    # Remove global mean geohgt and then limit to hemisphere of choice
    zp = remove_global_mean(z)
    if hemi == "NH":
        zp = zp.isel(lat=zp.lat >= 20)
    elif hemi == "SH":
        zp = zp.isel(lat=zp.lat <= -20)

    # Find the geohgt anomalies
    if anom == "simple":
        z_anom = remove_simple_smoothed_climo(zp, ndays=15)
        z_anom = z_anom.groupby("time.dayofyear").apply(detrend_xr)
        z_anom = z_anom.drop("dayofyear")
    elif anom == "gerber":
        z_anom = remove_trend_climo(zp)
    else:
        z_anom = None  # shouldn't be possible to get here

    return z_anom


def eof_annular_mode(z_anom):
    r"""Computes annular mode indices of zonal mean geopotential height
    anomlies. These are assumed to be based off of EOF1, but users should
    verify that the latitudinal structures for each pressure level match
    closely with known patterns.

    Parameters
    ----------
    z_anom : `xarray.DataArray`
        The input zonal mean geopotential height anomaly data. Should
        contain only the latitudes for a single hemisphere that span at
        least 60 degrees, with a max latitude that's at least 85 degrees.

    Returns
    -------
    (am, eof1) : tuple
        Tuple containing the annular mode (principal component) time series
        and EOF1 latitude profiles as a function of pressure level.

    """

    def _rebuild(solvers):
        r"""An internal nested function to rebuild the output from
        dictionaries of Eof solvers into xarray DataArrays for the
        principal component time series, and EOF latitude profiles.
        
        This function will also flag bad data if the latitudinal 
        span of the output EOF data doesn't cover enough (this 
        can sometimes be the case for pressure levels that intersect
        the surface in the polar regions).

        """
        pc1 = []
        eof1 = []

        # Iterate over the pressure levels
        plevs = sorted(list(solvers.keys()))[::-1]
        for i, p in enumerate(plevs):
            # Get EOF1 structure for pressure level
            eof1_struc = solvers[p].eofs(neofs=1, eofscaling=2).sel(mode=0)
            
            # Require there be a continuous span of good data (isnan -> False)
            # spanning at least 52.5 degrees with a high latitude boundary of 82.5.
            # In other words, we need enough good data spanning enough latitudes
            # for the EOF analysis/annular modes to be meaningful
            start,end = longest_chain_zeros(np.isnan(eof1_struc.values))
            if (start is None) and (end is None):
                start_lat = 0
                end_lat = 0
            else:
                start_lat = eof1_struc.lat.isel(lat=start)
                end_lat = eof1_struc.lat.isel(lat=end)

            if (np.abs(end_lat-start_lat) < 52.5) or (np.maximum(np.abs(start_lat), np.abs(end_lat)) < 82.5):
                flag = np.nan
            else:
                flag = 1
            
            # Append the EOF1 structure multiplied by the flag 
            eof1.append(eof1_struc.assign_coords({"lev": float(p)})*flag)
            
            # Get PC1 time series for pressure level, multiplied by the flag
            pc1.append(
                solvers[p]
                .pcs(npcs=1, pcscaling=1)
                .sel(mode=0)
                .assign_coords({"lev": float(p)}) * flag
            )

        # concat these across the pressure levels and return them
        return (xr.concat(pc1, dim="lev"), xr.concat(eof1, dim="lev"))

    # Do we have enough latitudes to work with this data?
    lats = z_anom.lat.values
    if ~(np.all(lats < 0) or np.all(lats > 0)):
        msg = "Latitudes must all be contained within one hemisphere (i.e., must all be positive or negative)"
        raise ValueError(msg)

    if (lats.ptp() < 60) or (np.abs(lats).max() < 85):
        msg = "Latitudes must span at least 60 degrees and include sufficient data in the polar region (up to at least 85 degrees)"
        raise ValueError(msg)

    # Do the EOF analysis with sqrt(cos(lat)) weighting
    wgts = np.sqrt(np.cos(np.deg2rad(lats)).clip(0.0, 1.0))[np.newaxis, ...]

    # Iterate over pressure levels
    solvers = {}
    for p in z_anom.lev:
        solver = Eof(z_anom.sel(lev=p), weights=wgts)
        # Since the sign of the eigenvectors in the EOF analysis are arbitrary,
        # the signs of the EOF1/PC1-timeseries for each pressure level may be
        # inconsistent from one another. We try to correct this by using the
        # EOF1 pattern -- if the max of the EOF1 pattern occurs at a latitude
        # poleward of 45 degrees, and the min of the EOF1 pattern occurs EQward
        # of 45 degrees, then we need to multiply internal matrices by -1
        # *** This strategy is specific to the annular modes! ***
        eof_1lev = solver.eofs(neofs=1, eofscaling=2).isel(mode=0)
        lat_max = eof_1lev.idxmax()
        lat_min = eof_1lev.idxmin()
        if (np.abs(lat_max) >= 55.0) and (np.abs(lat_min) <= 55.0):
            solver._solver._P *= -1
            solver._solver._flatE *= -1
        solvers[int(p.values)] = solver

    # Build the output into xarray DataArrays and return
    pc1, eof1 = _rebuild(solvers)
    pc1 = pc1.transpose("time", "lev")
    eof1 = eof1.transpose("lev", "lat")

    return (pc1, eof1)


def acf(ts, max_lag=50):
    r"""Compute the autocorrelation function of a time series
    as a function of day of year and lag. Considers only
    positive lags for estimating persistence.

    Parameters
    ----------
    ts : `xarray.DataArray`
        The input time series. Assumed to have only the dimensions
        of time and lev.

    max_lag : int
        The maximum lag for computing the ACF. Defaults to 50 days.

    Returns
    -------
    autocorr : `xarray.DataArray`
        The autocorrelation function with dimensions of (time, lev, lag)

    """
    # Get the max day of year. If we have leap
    # days, we will ignore them.
    doy_max = ts["time.dayofyear"].values.max()
    if doy_max == 366:
        doy_max = 365

    # Size of output array will be dayofyear x lev x lag
    nlevs = ts["lev"].size
    doys = ts["time.dayofyear"]
    lags = np.arange(0, max_lag + 1)

    # Prepare the arrays we will be using
    dat = ts.values
    autocorr = np.zeros((doy_max, nlevs, lags.size))

    # Make a "lookup" table for the indices for each dayofyear.
    # We do this first because in the below double-for loop,
    # we need the values for the future too (positive lags),
    # so we can do this just once
    doy_ixs = {}
    for j in range(doy_max):
        doy_ixs[j + 1] = np.where(doys == j + 1)[0]

    for j in range(doy_max):
        for k, lag in enumerate(lags):
            lag_doy = ((j + 1) + lag) % doy_max

            if lag_doy == 0:
                lag_doy = doy_max

            # The following bit of code does some weird indexing
            # to assure the sample sizes for every lag are equal
            # and that year-crossovers are handled correctly
            #
            # Assuming you have a set of data starting from
            # 1 Jan 0001 to 31 Dec 0010 -- you have N=10 years,
            # but the year 0010 can't be lagged ahead in time.
            # Thus, in the below we consider only N-1 years.
            #
            # Our data has dimensions (time, lev); we find the
            # indices of the specific days of year we want,
            # which should give N data points per lev.
            # Therefore, we keep the years from 0 to N-1 if we
            # are not crossing the year boundary with our lags,
            # or 1 to N if we are.
            now_ixs = doy_ixs[j + 1][0:-1]  # the [0:-1] indexing keeps 0 to N-1
            if ((j + 1) + lag) > doy_max:
                later_ixs = doy_ixs[lag_doy][1:]  # the [1:] indexing keeps 1 to N
            else:
                later_ixs = doy_ixs[lag_doy][0:-1]

            now = dat[now_ixs, :]
            later = dat[later_ixs, :]

            autocorr[j, :, k] = np.sum(now * later, axis=0) / np.sqrt(
                np.sum(now * now, axis=0) * np.sum(later * later, axis=0)
            )

    autocorr = xr.DataArray(
        autocorr,
        dims=["dayofyear", "lev", "lag"],
        coords=[np.arange(1, doy_max + 1), ts.lev, lags],
    )

    return autocorr


def efolding_tscales(acf):
    r"""Compute the e-folding timescale estimated from an
    autocorrelation function (ACF). The function fits an exponential
    to the ACF to determine the time "tau" at which the ACF drops to 1/e.

    Parameters
    ----------
    acf : `xarray.DataArray`
        The input autocorrelation function. Assumed to have
        dimensions of (dayofyear,lev)

    Returns
    -------
    tscales : `xarray.DataArray`
        The e-folding timescales.

    """

    tscales = np.zeros((acf.dayofyear.size, acf.lev.size))
    lags = np.arange(acf.lag.size)
    for i, doy in enumerate(acf.dayofyear):
        for j, lev in enumerate(acf.lev):
            
            if np.any(np.isnan(acf.sel(dayofyear=doy, lev=lev))):
                tscales[i,j] = np.nan
                continue

            # Use the scipy optimize.curve_fit function to
            # fit an exponential and find the
            vals = optimize.curve_fit(
                lambda t, a: np.exp(-1 * t / a),
                lags,
                acf.sel(dayofyear=doy, lev=lev),
                p0=(3),
            )
            tscales[i, j] = vals[0][0]

    tscales = xr.DataArray(
        tscales, dims=["dayofyear", "lev"], coords=[acf.dayofyear, acf.lev]
    )

    return tscales


def annmode_predictability(am, pred_lev=850):
    r"""Computes the annular mode predictability of a given pressure level
    as a function of day of year and other pressure levels. The predictability
    is the fraction of the variance of the 30 day mean annular mode index at
    a given level, lagged by 10 days, that can be “predicted” from a persistence
    forecast based on today's instantaneous annular mode index (at other pressure
    levels); see Gerber et al., 2010 (section 4.2, graf 29)

    Parameters
    ----------
    am : `xarray.DataArray`
        The annular mode time series with dimensions (time, lev).

    pred_lev : numeric
        The level of the data to use as the predictand. Defaults to 850 for
        the 850mb pressure level in the troposphere.

    Returns
    -------
    pred_all_levs : `xarray.DataArray`
        The e-folding timescales.

    References
    ----------
    Gerber, E. P., et al. (2010), Stratosphere-troposphere coupling and annular
        mode variability in chemistry-climate models, J. Geophys. Res., 115,
        D00M06, doi:10.1029/2009JD013770.

    """
    
    if pred_lev not in am.lev:
        msg = f"The lev dimension of input does not contain {pred_lev}"
        raise ValueError(msg)

    years = am["time.year"]
    yr_range = np.arange(years.min(), years.max() + 1)

    num_doy = am.time.size / yr_range.size
    if num_doy.is_integer() is False:
        msg = "Time dimension must be reshapeable into (num_years, dayofyear)"
        raise ValueError(msg)

    doys = np.arange(1, num_doy + 1)

    # "Brute-force and ignorance" algorithm
    samples_lag = {}
    samples_lead = {}
    for i, time in enumerate(am.time):
        # walk along each timestep and collect the NAM "now"
        # and the future NAM time averaged at the level we're
        # trying to predict (determined by pred_lev kwarg)
        doy = int(time.dt.dayofyear)
        raw_inds = np.arange(i + 10, i + 41)

        # Do not use samples that go across the max time in
        # the input DataArray
        if np.any(raw_inds >= am.time.size):
            continue

        # Compute the samples; instantaneous values at
        # all levels, and the time-averaged data at the
        # given level.
        inst_lag = am.isel(time=i)
        tavg_lead = am.sel(lev=pred_lev).isel(time=raw_inds).mean("time")

        # Store the samples in the dictionary with keys
        # that are days of year
        if doy not in samples_lag:
            samples_lag[doy] = []
            samples_lead[doy] = []
        samples_lag[doy].append(inst_lag.values[np.newaxis, ...])
        samples_lead[doy].append(float(tavg_lead.values))

    # Now go through every day of year and pressure level
    # and find the correlation between the predictand and
    # the instantaneous NAM at every other pressure level
    pred_all_levs = []
    for doy in doys:
        samples_lag[doy] = np.concatenate(samples_lag[doy])
        samples_lead[doy] = np.array(samples_lead[doy])

        pred = []
        for j, lev in enumerate(am.lev):
            r = np.corrcoef(samples_lag[doy][:, j], samples_lead[doy])[0, 1]
            pred.append(r**2)
        pred_all_levs.append(np.array(pred)[np.newaxis, :])

    # Collect the results into a DataArray
    pred_all_levs = np.concatenate(pred_all_levs, axis=0)
    pred_all_levs = xr.DataArray(
        pred_all_levs, dims=["dayofyear", "lev"], coords=[doys, am.lev]
    )

    return pred_all_levs
