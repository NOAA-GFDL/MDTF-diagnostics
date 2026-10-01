# ==============================================================================
# MDTF Strat-Trop Coupling: Vertical Planetary Wave Coupling POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Vertical Wave Coupling POD
# of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt). It defines
# the plotting functions used by the main driver script.


import numpy as np
import matplotlib as mpl
import cartopy.crs as ccrs
import matplotlib.ticker as ticker

from cartopy.util import add_cyclic_point
from matplotlib import pyplot as plt

from stc_vert_wave_coupling_calc import cross_spectral_corr

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12


def wave_ampl_climo_plot(z_k, lat, obs=None):
    r""" Plot climatologies of geopotential height wave amplitudes
    for zonal wavenumbers 1-3 at the given latitude, comparing the
    10 and 500 hPa pressure levels.

    Parameters
    ----------
    z_k : `xarray.DataArray`
        The geopotential height fourier coefficients for zonal waves
        1-3, with dimensions of latitude and time. Must contain an
        attribute called "nlons" which contains the number of longitudes
        of the original gridded dataset for which the FFT was taken.

    lat : int/float
        The latitude for which the climatologies will be plotted.

    obs : (optional) `xarray.DataArray` or None
        If given a DataArray, it is assumed to be observations that
        can be plotted for comparison with the given z_k. Should
        contain consistent dimensions, latitudes, and times.
        If None, this function will ignore "obs" and plot only
        from the z_k.

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    # Calculate the wave amplitudes
    ampls = 2*np.abs(z_k.interp(lat=lat))/z_k.nlons

    # Calculate the relevant climatological quantities:
    #     * Climatology
    #     * All time min/max
    #     * 1st/3rd quartile across the days of year
    climo = ampls.groupby('time.dayofyear').mean('time')
    amp_max = ampls.groupby('time.dayofyear').max('time')
    amp_min = ampls.groupby('time.dayofyear').min('time')
    amp_25 = ampls.groupby('time.dayofyear').quantile(0.25, 'time')
    amp_75 = ampls.groupby('time.dayofyear').quantile(0.75, 'time')

    # Figure out relevant plot aspects based on the max day of year
    max_doy = int(climo.dayofyear.max())
    if (lat > 0) and (max_doy == 365):
        # July 1 falls on DOY 182
        roll_to = -181
        xticks = np.array([1, 32, 63, 93, 124, 154, 185, 213, 244, 274, 305, 335, 365])
        xlabels = ['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J']
    elif (lat > 0) and (max_doy == 360):
        # July 1 falls on DOY 181
        roll_to = -180
        xticks = np.array([1, 31, 61, 91, 121, 151, 181, 211, 241, 271, 301, 331, 360])
        xlabels = ['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J']
    elif (lat < 0) and (max_doy == 365):
        roll_to = 0
        xticks = np.array([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 365])
        xlabels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    elif (lat < 0) and (max_doy == 360):
        roll_to = 0
        xticks = np.array([1, 31, 61, 91, 121, 151, 181, 211, 241, 271, 301, 331, 360])
        xlabels = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    else: 
        msg = "Unable to determine plot params from given input data"
        raise ValueError(msg)
    xlab_pos = (np.diff(xticks)*0.5)+xticks[0:-1]

    # Handle the obs if given. Compute amplitudes and climo line.
    if obs is not None:
        obs_ampls = 2*np.abs(obs.interp(lat=lat))/obs.nlons
        obs_climo = obs_ampls.groupby('time.dayofyear').mean('time')
        obs_max_doy = int(obs_climo.dayofyear.max())

        # Some models use different calendars (e.g., noleap, 360day).
        # For comparison, we will interpolate the obs to the same time
        # range as the input model dataset
        if obs_max_doy != max_doy:
            obs_climo = obs_climo.assign_coords({'dayofyear': np.linspace(1, max_doy, obs_max_doy)})
            obs_climo = obs_climo.interp(dayofyear=climo.dayofyear)

    # The y-limit for the different pressure/wavenum combos
    ylims = {'10_1': (0, 2000),
             '10_2': (0, 1400),
             '10_3': (0, 800),
             '500_1': (0, 350),
             '500_2': (0, 350),
             '500_3': (0, 350)}

    # Begin plotting
    fig = plt.figure()
    for i, lev in enumerate([10, 500]):
        for j, wavenum in enumerate([1, 2, 3]):
            ax = fig.add_subplot(2, 3, 3*i + j + 1)
            # plot the 1st/3rd quartile with grey envelope
            ax.fill_between(climo.dayofyear,
                            amp_25.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                            amp_75.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                            color='#c0c0c0', label='IQR')
            # plot the absolute min/max in black dashed lines
            ax.plot(climo.dayofyear, amp_min.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                    color='black', linestyle='--', linewidth=0.66, label='Min/Max')
            ax.plot(climo.dayofyear, amp_max.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                    color='black', linestyle='--', linewidth=0.66)
            # plot the climo in a thicker black line
            ax.plot(climo.dayofyear, climo.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                    color='black', linewidth=3.0, label='Climatology')
            if obs is not None:
                # plot the obs climo in an orange line for comparison
                ax.plot(climo.dayofyear, obs_climo.sel(lev=lev, zonal_wavenum=wavenum).roll(dayofyear=roll_to),
                        color='#ff8c00', linewidth=1.0, label='Obs Climatology')

            plt.xlim((1, max_doy))
            plt.ylim(ylims[f'{lev}_{wavenum}'])
            plt.xticks(xticks, ['']*xticks.size)
            for ix, xlabel in enumerate(xlabels):
                plt.text(xlab_pos[ix]/max_doy, -0.1, xlabel, fontsize=16, ha='center', transform=ax.transAxes)
            ax.tick_params(axis='both', which='major', length=7, width=1.2, labelsize=14)

            if lev == 10:
                plt.title(f'Wave {wavenum}', fontsize=18)

            if lev == 10 and wavenum == 3:
                plt.legend(frameon=False, fontsize=13, loc='upper left')

            if wavenum == 1:
                plt.text(0.05, 0.90, f'{lev} hPa', color='red',
                         fontsize=16, transform=ax.transAxes, fontweight='semibold')

    plt.text(0.0075, 0.5, 'Wave Amplitude [gpm]',
             rotation=90, fontsize=18, transform=fig.transFigure, va='center')

    fig.subplots_adjust(hspace=0.15, left=0.075, right=0.99)
    fig.set_size_inches(14, 8.)

    return fig


def heatflux_histo_plot(vt_k, months, hemi, obs=None):
    r""" Plot 50 hPa heatflux histograms for the given set of months
    and hemisphere.

    Parameters
    ----------
    vt_k : `xarray.DataArray`
        The eddy heat flux as a function of zonal wavenumber as a
        function of time only. (No latitude dimension!) Assumed
        to be heat fluxes for the 50 hPa pressure level

    months : list of ints
        The months of data to include in the histograms

    obs : (optional) `xarray.DataArray` or None
        If given a DataArray, it is assumed to be observations that
        can be plotted for comparison with the given vt_k. Should
        contain consistent wavenumbers and times.
        If None, this function will ignore "obs" and plot only
        from the vt_k.

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    # limit the input data and obs to the specific months
    vt_to_plot = vt_k.where(vt_k['time.month'].isin(months), drop=True)
    if obs is not None:
        obs_to_plot = obs.where(obs['time.month'].isin(months), drop=True)

    # The histogram bins we'll plot as a function
    # of the hemisphere and wavenumber
    if hemi == 1:
        bins = {1: np.linspace(-80, 140, 25),
                2: np.linspace(-50, 100, 25),
                3: np.linspace(-30, 30, 25)}
    elif hemi == -1:
        bins = {1: np.linspace(-140, 80, 25),
                2: np.linspace(-100, 50, 25),
                3: np.linspace(-30, 30, 25)}
    else:
        msg = "hemi must be -1 or 1!"
        raise ValueError(msg)

    # Begin plotting
    fig = plt.figure()
    for i, wavenum in enumerate([1, 2, 3]):
        ax = fig.add_subplot(1, 3, i+1)

        # plot vertical lines at the 10th and 90th percentiles
        percs = np.percentile(vt_to_plot.sel(zonal_wavenum=wavenum), [10, 90])
        percstring = f'{percs[0]:0.1f}, {percs[1]:0.1f}'
        plt.axvline(percs[0], color='grey')
        plt.axvline(percs[1], color='grey')
        ax.hist(vt_to_plot.sel(zonal_wavenum=wavenum), bins=bins[wavenum], density=True,
                histtype='step', color='black', linewidth=2, label='Input')
        plt.text(0.85, 0.93, percstring, transform=ax.transAxes, fontsize=12, ha='center', va='center')

        # handle the obs if given; overplot similar step-histos and percentile vertical lines
        if obs is not None:
            obs_percs = np.percentile(obs_to_plot.sel(zonal_wavenum=wavenum), [10, 90])
            percstring = f'{obs_percs[0]:0.1f}, {obs_percs[1]:0.1f}'

            ax.hist(obs_to_plot.sel(zonal_wavenum=wavenum), bins=bins[wavenum], density=True,
                    histtype='step', color='#FF8C00', linewidth=1, label='Obs')
            plt.axvline(obs_percs[0], color='#FF8C00', linestyle='--', linewidth=0.7)
            plt.axvline(obs_percs[1], color='#FF8C00', linestyle='--', linewidth=0.7)
            plt.text(0.85, 0.85, percstring, transform=ax.transAxes, color='#FF8C00', fontsize=12, ha='center',
                     va='center')

        plt.xlim((bins[wavenum].min(), bins[wavenum].max()))
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        ax.tick_params(axis='both', which='major', length=7, width=1.2, labelsize=14)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(6))
        plt.title(f'Wave {wavenum}', fontsize=18)

        if wavenum == 1:
            ax.legend(loc='center right', frameon=False)
            plt.ylabel('Normalized Frequency', fontsize=16)
        if wavenum == 2:
            plt.xlabel('Eddy Heat Flux due to wave-k [K m/s]', fontsize=16)

    fig.subplots_adjust(top=0.95, wspace=0.35, left=0.10, bottom=0.05, right=0.99)
    fig.set_size_inches(12, 6)
    return fig


def eddy_hgt_hfevents(z10_eddy, z500_eddy, pos_dates, neg_dates, hemi):
    r""" Plot composites of eddy height fields and anomalies for
    positive and negative 50 hPa heat flux events, for the given
    hemisphere.

    Parameters
    ----------
    z10_eddy : `xarray.DataArray`
        The 10 hPa eddy geopotential height fields as a
        function of time.

    z500_eddy: `xarray.DataArray`
        The 500 hPa eddy geopotential height fields as a
        function of time.

    pos_dates: arraylike of numpy/pandas datetimes
        The dates of extreme positive heat flux events

    neg_dates: arraylike of numpy/pandas datetimes
        The dates of extreme negative heat flux events

    hemi: int
        Either -1 for the southern hemisphere, or 1 for northern
        hemisphere

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    if hemi not in [-1, 1]:
        msg = 'hemi must be either 1 (for NH) or -1 (for SH)'
        raise ValueError(msg)

    # set the cartopy projections
    map_proj = ccrs.Orthographic(central_longitude=0, central_latitude=90*hemi)
    data_proj = ccrs.PlateCarree()

    # compute eddy height climatologies and anomalies
    z10_clim = z10_eddy.groupby('time.dayofyear').mean('time')
    z10_anom = z10_eddy.groupby('time.dayofyear') - z10_clim
    z500_clim = z500_eddy.groupby('time.dayofyear').mean('time')
    z500_anom = z500_eddy.groupby('time.dayofyear') - z500_clim

    # Begin plotting; we make maps in following order:
    #    * overall eddy height climos
    #    * extreme positive heat flux composite anomalies
    #    * extreme negative heat flux composite anomalies
    fig = plt.figure()
    for i in range(3):
        if i == 0:
            q2p_10 = z10_clim.mean('dayofyear')
            q2p_500 = z500_clim.mean('dayofyear')
            clevs10 = (np.arange(-800, 0, 100),
                       np.arange(100, 801, 100))
            clevs500 = (np.arange(-500, 0, 20),
                        np.arange(20, 501, 20))
            title = 'Eddy Height Climo'
        elif i == 1:
            q2p_10 = z10_anom.sel(time=pos_dates).mean('time')
            q2p_500 = z500_anom.sel(time=pos_dates).mean('time')

            clevs10 = (np.arange(-500, 0, 50),
                       np.arange(50, 501, 50))
            clevs500 = (np.arange(-500, 0, 10),
                        np.arange(10, 501, 10))
            title = f'+EHF50 Days ({len(pos_dates)})'
        elif i == 2:
            q2p_10 = z10_anom.sel(time=neg_dates).mean('time')
            q2p_500 = z500_anom.sel(time=neg_dates).mean('time')

            clevs10 = (np.arange(-500, 0, 50),
                       np.arange(50, 501, 50))
            clevs500 = (np.arange(-500, 0, 10),
                        np.arange(10, 501, 10))
            title = f'-EHF50 Days ({len(neg_dates)})'

        # Get coordinates that we'll use for the maps
        lats = q2p_10.lat
        lons = q2p_10.lon
        lonidx = q2p_10.get_axis_num('lon')

        # Add a cyclic longitude point
        q2p_10, wrap_lon = add_cyclic_point(q2p_10.values, coord=lons, axis=lonidx)
        q2p_500, wrap_lon = add_cyclic_point(q2p_500.values, coord=lons, axis=lonidx)

        # plot the maps
        ax = fig.add_subplot(1, 3, i+1, projection=map_proj)
        ax.set_global()
        ax.coastlines('110m', color='grey', linewidth=0.75)
        ax.contourf(wrap_lon, lats, q2p_10,
                    transform=data_proj, levels=clevs10[0], cmap='Purples_r', extend='min')
        ax.contourf(wrap_lon, lats, q2p_10,
                    transform=data_proj, levels=clevs10[1], cmap='Oranges', extend='max')
        ax.contour(wrap_lon, lats, q2p_500,
                   transform=data_proj, levels=clevs500[0], colors='black', linestyles='--')
        ax.contour(wrap_lon, lats, q2p_500,
                   transform=data_proj, levels=clevs500[1], colors='black', linestyles='-')
        plt.title(title, fontsize=18)

    fig.set_size_inches(15, 6)
    fig.subplots_adjust(top=0.85, left=0.02, right=0.98, bottom=0.02)
    return fig


def corrcoh_seasons(z_fc, hemi):
    r""" Plot bimonthly composites of zonal wave 1 and 2
    correlation coherence between 10 and 500 hPa.

    Parameters
    ----------
    z_fc: `xarray.DataArray`
        The Fourier coefficients of geopotential height for
        zonal waves 1 and 2, and the 10 & 500 hPa prs levels

    hemi: int
        Either -1 for the southern hemisphere, or 1 for northern
        hemisphere

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    # The bimonthly composites for the different
    # extended winter seasons of each hemisphere
    if hemi == 1:
        months = [(11, 12), (12, 1), (1, 2), (2, 3), (3, 4)]
        labels = ['ND', 'DJ', 'JF', 'FM', 'MA']
    elif hemi == -1:
        months = [(7, 8), (8, 9), (9, 10), (10, 11), (11, 12)]
        labels = ['JA', 'AS', 'SO', 'ON', 'ND']
    else:
        msg = 'hemi must be one of 1 (for NH) or -1 (for SH)'
        raise ValueError(msg)

    # Begin plotting
    fig = plt.figure()
    for i, wavenum in enumerate([1, 2]):
        ax = fig.add_subplot(1, 2, i+1)

        # Do the correlation coherence computations and plot the lines
        for j, mos in enumerate(months):
            coh, phas = cross_spectral_corr(z_fc.sel(zonal_wavenum=wavenum), z_fc.nlons,
                                            mos, 500, 10, np.arange(-10, 11))
            ax.plot(coh.lag, coh.values, linewidth=1.5, label=labels[j])

        # Customize the plots
        ax.set_title(f'Wave {wavenum}', fontsize=20)
        if wavenum == 1:
            ax.set_ylabel('Correlation Coherence (500 hPa vs 10 hPa)', fontsize=17)
            ax.legend(frameon=False, loc='upper left', fontsize=13)
        ax.set_xlabel('<- strat leads trop | Lag [days] | trop leads strat ->', fontsize=16)
        plt.axvline(0, color='black', linewidth=0.5)
        ax.set_ylim((0, 0.5))
        ax.set_xlim((-10, 10))
        ax.set_xticks(np.arange(-10, 11, 2))
        ax.tick_params(axis='both', which='major', length=7, width=1.2, labelsize=14)

    fig.subplots_adjust(wspace=0.1, left=0.075, bottom=0.1, right=0.99, top=0.85)
    fig.set_size_inches(14, 6)

    return fig
