# ==============================================================================
# MDTF Strat-Trop Coupling: Vertical Planetary Wave Coupling POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Vertical Wave Coupling POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt). It defines
# the diagnostic computation functions used by the main driver script.


import scipy
import numpy as np
import xarray as xr


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
    ds_wgt_avg = ds_tmp.weighted(wgts).mean('lat', keep_attrs=True)
    return ds_wgt_avg


def zonal_wave_coeffs(dat, keep_waves=None):
    r""" Perform a FFT on a global (lat/lon) gridded dataset to
    compute Fourier coefficients as a function of zonal wavenumber.

    Parameters
    ----------
    dat : `xarray.DataArray`
        The input DataArray to take the FFT on.

    keep_waves : list of ints (optional) or None
        The zonal wavenumbers to keep in the return DataArray. Defaults to None
        to keep all zonal wavenumbers.

    Returns
    -------
    fc : `xarray.DataArray`
         The complex Fourier coefficients representative of the Fourier transform
         around latitude circles.

    Notes
    -----
    The input xarray variable dat is assumed to have a dimension named "lon".
    E.g., if your data has a dimension named "longitude", use the rename method:
        dat.rename({'longitude':'lon'})

    May consider updating function to use the xrft package to better leverage the
    lazy evaluation and chunking capabilities of dask and xarray. The scipy fft
    functions have the advantage that they keep the floating point precision of
    the input data. I.e., if given float32, the return data will be complex64
    (whereas with many other FFT libraries, the data is often returned as
    complex128 regardless)

    """

    nlons = dat.lon.size
    lon_ax = dat.get_axis_num('lon')

    new_dims = list(dat.dims)
    new_dims[lon_ax] = "zonal_wavenum"

    new_coords = dict(dat.coords)
    new_coords.pop('lon')
    new_coords["zonal_wavenum"] = np.arange(0, nlons//2 + 1)

    fc = scipy.fft.rfft(dat.values, axis=lon_ax)
    fc = xr.DataArray(fc, coords=new_coords, dims=new_dims)
    fc.attrs['nlons'] = nlons

    if keep_waves is not None:
        fc = fc.sel(zonal_wavenum=keep_waves)

    return fc


def zonal_wave_covariance(x, y, keep_waves=None):
    r""" Compute the covariance of two fields x and y as a function of
    zonal wavenumber.

    Parameters
    ----------
    x : `xarray.DataArray`
        A global gridded (lat/lon) field. Must be fully consistent with y.
        In other words, the coordinates of both fields must match exactly
        such that xr.align(..., join='exact') can be done successfully.

    y : `xarray.DataArray`
        A global gridded (lat/lon) field. Must be fully consistent with x.
        In other words, the coordinates of both fields must match exactly
        such that xr.align(..., join='exact') can be done successfully.

    keep_waves : list of ints (optional) or None
        The zonal wavenumbers to keep in the return DataArray. Defaults to None
        to keep all zonal wavenumbers.

    Returns
    -------
    cov : `xarray.DataArray`
         The covariance of x and y as a function of zonal wavenumber.

    Notes
    -----
    Both input DataArrays are assumed to have a dimension named 'lon'.

    See also
    --------
    zonal_wave_coeffs

    """

    # Ensure that both DataArrays are fully consistent
    xr.align(x, y, join="exact", copy=False)

    # Compute the Fourier coefficients
    fcx = zonal_wave_coeffs(x, keep_waves=keep_waves)
    fcy = zonal_wave_coeffs(y, keep_waves=keep_waves)

    # Because zonal_wave_coeffs uses rFFT with real inputs and
    # returns coefficients with a symmetric spectrum, we create a mask
    # that is equal to 2 everywhere with nonzero wavenumber to correctly
    # compute the covariance.
    nlons = x.lon.size
    mult_mask = np.isfinite(fcx.where(fcx.zonal_wavenum != 0)) + 1
    cov = mult_mask*np.real(fcx * fcy.conj())/(nlons**2)

    return cov


def cross_spectral_corr(Z_fc, nlons, months, src_lev, des_lev, lags):
    r""" Compute the lagged cross-spectral correlation of a field between two
    different vertical levels for a given zonal wavenumber. The following code
    is a fairly literal/direct translation of the methods described in
    Randel 1987 (see References below). The code below could probably be
    better generalized and/or vectorized.

    Parameters
    ----------
    Z_fc : `xarray.DataArray`
        The complex Fourier coefficients for a given zonal wavenumber
        as a function of time.

    nlons : int
        The number of longitudes of the discretized field for which Z_fc corresponds.

    months : list/array of ints
        The months to consider for the time series of Z_fc. The computations
        will only take timesteps in these months into consideration.

    src_lev : float/int
        The source level for determining lead vs lag.

    des_lev : float/int
        The destination level for determining lead vs lag.

    lags : list/array of ints
        The time lags to consider between the source and destination levels.

    Returns
    -------
    cov : (coh, phas)
        A tuple containing the correlation coherence and phase for the given lags.

    Notes
    -----
    The input DataArray Z_fc is assumed to have a dimension named 'lev' containing
    both src_lev and des_lev, as well as a time dimension containing dates that
    fall within the given months.

    References
    ----------
    Randel, W. J. (1987). A Study of Planetary Waves in the Southern Winter Troposphere
        and Stratosphere. Part I: Wave Structure and Vertical Propagation,
        Journal of Atmospheric Sciences, 44(6), 917-935.
        https://journals.ametsoc.org/view/journals/atsc/44/6/1520-0469_1987_044_0917_asopwi_2_0_co_2.xml

    """

    def _sigma(s, c):
        r""" A nested function to compute the square root of the variance
        of a time series given its sine and cosine coefficients. A direct
        translation of equation 1a.2 in Randel 1987.

        Parameters
        ----------
        s : 1D array-like
            The sine coefficients as a function of time.

        c : 1D array-like
            The cosine coefficients as a function of time.

        Returns
        -------
        sigma : float
            The square root of the variance.

        Notes
        -----
        s and c are assumed to have had their time-mean values removed.

        """

        if s.ndim > 1 or c.ndim > 1:
            msg = 'cross_spectral_corr._sigma: s an c must both be 1-D'
            raise ValueError(msg)
        if s.size != c.size:
            msg = 'cross_spectral_corr._sigma: s and c must have the same size'
            raise ValueError(msg)

        n = np.isfinite(s).sum()
        sigma = np.sqrt((1 / (n-1)) * np.nansum(s**2 + c**2))
        return sigma

    def _lin_corr_times(x, y, lags, sigma_x, sigma_y, times):
        r""" A nested function to compute the laggged linear correlations
        between two time series x and y. A direct translation of
        Randel 1987 1a.1.

        Parameters
        ----------
        x : 1D array-like
            A time series. Must have the same size as y.

        y : 1D array-like
            A time series. Must have the same size as x.

        lags : list/array of ints
            The lags to consider in the correlation computations.

        sigma_x : float
            The square root of the variance of x.

        sigma_y : float
            The square root of the variance of y.

        times : np.array of datetime64
            The times of the samples in both x and y.

        Returns
        -------
        corr : np.array of floats
            The lagged correlations between x and y.

        Notes
        -----
        x and y are assumed to have had their time-mean values removed.

        """

        if x.size != y.size:
            msg = 'cross_spectral_corr._lin_corr_times: x and y must have the same size'
            raise ValueError(msg)

        lag_corr = np.zeros(lags.size)
        n = x.size  # length of array -- used for indexing
        ns = np.isfinite(x).sum()  # total number of samples

        for i, tau in enumerate(lags):
            # We want to put together lagged correlations by correctly constructing pairs of
            # data points that are lagged by the given tau (if tau > 0, y leads x in time;
            # if tau <= 0, x leads y in time). However, our time series are 1D and will
            # consist of points from *only specific months* across some number of years.
            # This means that we can't just simply index the arrays offset to each other,
            # because some elements will sit next to elements that are from the next year.
            # The trick here is to use an array of times that match the data, and to select
            # only the pairs that have the given lag equal to tau.
            if tau > 0:
                times_x = times[0:n-tau]
                times_y = times[tau:n+1]
                good_pairs = np.where(times_y-times_x == np.timedelta64(tau, 'D'))
                x_good = x[0:n-tau][good_pairs].values
                y_good = y[tau:n+1][good_pairs].values
            else:
                times_x = times[np.abs(tau):n+1]
                times_y = times[0:n-np.abs(tau)]
                good_pairs = np.where(times_y-times_x == np.timedelta64(tau, 'D'))
                x_good = x[np.abs(tau):n+1][good_pairs].values
                y_good = y[0:n-np.abs(tau)][good_pairs].values
            lag_corr[i] = (1 / (ns - np.abs(tau))) * np.nansum(x_good * y_good)

        corr = lag_corr/(sigma_x * sigma_y)
        return corr

    # Get the times that only fall within the given months
    times = Z_fc.where(Z_fc['time.month'].isin(months), drop=True).time.values

    # in the below, "src" refers to data at the source level, while "des" refers
    # to data at the destination level. these designations affect how the lagged
    # pairs are determined for the correlation coherence analysis

    # set the source cosine/sine coefficients, remove their time mean values,
    # and get their standard deviation
    c_src = (2./nlons)*np.real(Z_fc.sel(lev=src_lev).where(Z_fc['time.month'].isin(months), drop=True))
    c_src = c_src - c_src.mean()
    s_src = (-2./nlons)*np.imag(Z_fc.sel(lev=src_lev).where(Z_fc['time.month'].isin(months), drop=True))
    s_src = s_src - s_src.mean()
    sigma_src = _sigma(s_src, c_src).data

    # set the destination cosine/sine coefficients, remove their time mean values,
    # and get their standard deviation
    c_des = (2./nlons)*np.real(Z_fc.sel(lev=des_lev).where(Z_fc['time.month'].isin(months), drop=True))
    c_des = c_des - c_des.mean()
    s_des = (-2./nlons)*np.imag(Z_fc.sel(lev=des_lev).where(Z_fc['time.month'].isin(months), drop=True))
    s_des = s_des - s_des.mean()
    sigma_des = _sigma(s_des, c_des).data

    # obtain the linear correlation between the different combinations of
    # source/destination cosine/sine coefficients
    s1s2 = _lin_corr_times(s_src, s_des, lags, sigma_src, sigma_des, times)
    c1c2 = _lin_corr_times(c_src, c_des, lags, sigma_src, sigma_des, times)
    s1c2 = _lin_corr_times(s_src, c_des, lags, sigma_src, sigma_des, times)
    c1s2 = _lin_corr_times(c_src, s_des, lags, sigma_src, sigma_des, times)

    # the in-phase correlation (Randel 1987, eq. 1a)
    co = s1s2 + c1c2

    # the out-of-phase correlation (Randel 1987, eq. 1b)
    qd = s1c2 - c1s2

    # Turn these into correlation coherence and phases, and
    # rebuild them into DataArrays with dimensions equal to the
    # time lags
    coh = np.sqrt(co*co + qd*qd)
    coh = xr.DataArray(coh, dims=['lag'], coords=[lags])
    phas = np.arctan2(-qd, co)
    phas = xr.DataArray(phas, dims=['lag'], coords=[lags])

    return coh, phas
