"""
This module contains functions used in the Stratospheric QBO and ENSO POD.

Contains:
	qbo_slp: plots sea level pressure response to QBO as a function of month and QBO phase
	qbo_uzm: plots the zonal-mean zonal wind response to QBO as a function of month and QBO phase
	qbo_vt: plots the zonally averaged eddy heat flux response to the QBO as a function of month and QBO phase
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.path as mpath
from cartopy.util import add_cyclic_point

from scipy import stats


##################################################################################################
##################################################################################################
##################################################################################################


def qbo_uzm(uzm, negative_indices, positive_indices, QBOisobar, titles, plot_months, axes):
    r""" Compute the zonal mean zonal wind response to the QBO. Anomalies are defined as
    deviations from the seasonal cycle and composites of anomalies are made during easterly QBO,
    westerly QBO, and then their difference is shown. Stippling is used to denote statistical
    significance on the EQBO minus WQBO composites.

    Parameters
    ----------
    uzm : xarray.DataArray
        The zonal mean zonal wind.

    negative_indices : list
        A list of easterly QBO years.

    positive_indices : list
        A list of westerly QBO years.

    QBOisobar : int
        An integer defined by the user in the config.jsonc file specifying what isobar
        is used to index the QBO

    titles : list of strings
        A list of month names that will be used as the titles for each column of subplots

    plot_months : list
        A list of numbers corresponding to each month (e.g., 10 = october)

    axes : A list of numbers used to set the pressure and latitude limits of the subplots.
        [0,90,1000,1] are used for the N. hemisphere and [-90,0,1000,1] for S. hemisphere

    Returns
    -------
    3 row by 6 column plot of easterly QBO uzm anomalies (top row), westerly QBO uzm
    anomalies (middle), and their difference (bottom row) with stippling highlighting differences
    between EQBO and WQBO winds statistically significant at the 95% level using a two-sided t-test.

    Notes
    -----
    The input field uzm is assumed to have dimensions named "lat" and "lev".
    E.g., if your data has dimensions "latitude" and/or "level",
    use the rename method:
        ds.rename({'latitude':'lat','level':'lev'})
    """

    eqbo_out = []
    wqbo_out = []
    diff_out = []
    sigs_out = []
    clim_out = []

    for mon in plot_months:

        clim = uzm.sel(time=uzm.time.dt.month.isin([mon]))
        clim_out.append(clim.mean('time').values)

        anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")

        if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
            tmp_negative_indices = np.add(negative_indices, 0)
            tmp_positive_indices = np.add(positive_indices, 0)
        if mon == 1 or mon == 2 or mon == 3:
            tmp_negative_indices = np.add(negative_indices, 1)
            tmp_positive_indices = np.add(positive_indices, 1)

        eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
        wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

        t, p = stats.ttest_ind(eqbo_tmp.values, wqbo_tmp.values, axis=0, nan_policy='omit')

        sigs_out.append(np.subtract(1, p))
        diff_out.append(np.subtract(eqbo_tmp.mean('time').values, wqbo_tmp.mean('time').values))
        eqbo_out.append(eqbo_tmp.mean('time').values)
        wqbo_out.append(wqbo_tmp.mean('time').values)

        clim.close()
        anom.close()
        eqbo_tmp.close()
        wqbo_tmp.close()
    uzm.close()

    eqbo_out = np.array(eqbo_out)
    wqbo_out = np.array(wqbo_out)
    diff_out = np.array(diff_out)
    sigs_out = np.array(sigs_out)
    clim_out = np.array(clim_out)

    # ############ Begin the plotting ############

    fig, ax = plt.subplots()

    mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

    vmin = -10
    vmax = 10
    vlevs = np.linspace(vmin, vmax, num=21)
    vlevs = [v for v in vlevs if v != 0]
    ticks = [vmin, vmin / 2, 0, vmax / 2, vmax]

    cmin = -200
    cmax = 200
    clevs = np.linspace(cmin, cmax, num=41)
    clevs = [v for v in clevs if v != 0]

    plt.suptitle('QBO (5S-5N index @ %s hPa) zonal-mean zonal wind (m/s)' % int(QBOisobar), fontsize=12,
                 fontweight='normal')

    # Add colormap #
    from palettable.colorbrewer.diverging import RdBu_11
    cmap1 = RdBu_11.mpl_colormap.reversed()

    x, y = np.meshgrid(uzm.lat.values, uzm.lev.values)

    cols = [0, 1, 2, 3, 4]

    for i in cols:

        # eqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(0, cols[i]))
        plt.title('%s' % titles[i], fontsize=10, y=0.93, fontweight='normal')

        cs = plt.contourf(x, y, eqbo_out[i], cmap=cmap1, levels=vlevs, extend="both", vmin=vmin, vmax=vmax,
                          zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)), fontsize=10)

        # wqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(1, cols[i]))

        cs = plt.contourf(x, y, wqbo_out[i], cmap=cmap1, levels=vlevs, extend="both", vmin=vmin, vmax=vmax,
                          zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')
        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)), fontsize=10)

        # Diff: eqbo minus wqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(2, cols[i]))

        cs = plt.contourf(x, y, diff_out[i], cmap=cmap1, levels=vlevs, extend="both", vmin=vmin, vmax=vmax,
                          zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')
        plt.xlabel('Latitude', fontsize=8, fontweight='normal')

        sig_levs = [0.95, 1]
        mpl.rcParams['hatch.linewidth'] = 0.2
        plt.contourf(x, y, sigs_out[i], colors='black', vmin=0.95, vmax=1, levels=sig_levs,
                     hatches=['......', '......'], alpha=0.0)

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo - wqbo', fontsize=10)

    # Add colorbar #

    cb_ax = fig.add_axes([0.365, 0.04, 0.30, 0.015])
    cbar = fig.colorbar(cs, cax=cb_ax, ticks=ticks, orientation='horizontal')
    cbar.ax.tick_params(labelsize=8, width=1)
    cbar.ax.set_xticklabels(ticks, weight='normal')

    plt.subplots_adjust(top=0.86, bottom=0.16, hspace=0.5, wspace=0.55, left=0.08, right=0.95)
    return fig, ax


##################################################################################################
##################################################################################################
##################################################################################################

def qbo_vt(vt, negative_indices, positive_indices, QBOisobar, titles, plot_months, axes):
    r""" Compute the zonal mean eddy heat flux response to the QBO. Anomalies are defined as
    deviations from the seasonal cycle and composites of anomalies are made during easterly QBO,
    westerly QBO, and then their difference is shown. Stippling is used to denote statistical
    significance on the EQBO minus WQBO composites.

    Parameters
    ----------
    vt : xarray.DataArray
        The zonal mean eddy heat flux. This quantity is calculated using the
        compute_total_eddy_heat_flux function given in the driver script stc_qbo_enso.py

    negative_indices : list
        A list of easterly QBO years.

    positive_indices : list
        A list of westerly QBO years.

    QBOisobar : int
        An integer defined by the user in the config.jsonc file specifying what isobar
        is used to index the QBO

    titles : list of strings
        A list of month names that will be used as the titles for each column of subplots

    plot_months : list
        A list of numbers corresponding to each month (e.g., 10 = october)

    axes : A list of numbers used to set the pressure and latitude limits of the subplots.
         [0,90,1000,1] are used for the N. hemisphere and [-90,0,1000,1] for S. hemisphere

    Returns
    -------
    3 row by 6 column plot of easterly QBO vt anomalies (top row), westerly QBO vt
    anomalies (middle), and their difference (bottom row) with stippling highlighting differences
    between EQBO and WQBO winds statistically significant at the 95% level using a two-sided t-test.

    Notes
    -----
    The input field vt is assumed to have dimensions named "lat" and "lev".
    E.g., if your data has dimensions "latitude" and/or "level",
    use the rename method:
        ds.rename({'latitude':'lat','level':'lev'})
    """

    eqbo_out = []
    wqbo_out = []
    diff_out = []
    sigs_out = []
    clim_out = []

    for mon in plot_months:

        clim = vt.sel(time=vt.time.dt.month.isin([mon]))
        clim_out.append(clim.mean('time').values)

        anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")

        # For NH, QBO index is based on Oct-Nov year. The plot will show Oct-Feb. Note that Jan-Feb are selected
        # using QBO index year + 1
        # For SH, QBO index is based on Jul-Aug year. The plot will show Jul-Nov.

        if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
            tmp_negative_indices = np.add(negative_indices, 0)
            tmp_positive_indices = np.add(positive_indices, 0)
        if mon == 1 or mon == 2 or mon == 3:
            tmp_negative_indices = np.add(negative_indices, 1)
            tmp_positive_indices = np.add(positive_indices, 1)

        eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
        wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

        t, p = stats.ttest_ind(eqbo_tmp.values, wqbo_tmp.values, axis=0, nan_policy='omit')

        sigs_out.append(np.subtract(1, p))
        diff_out.append(np.subtract(eqbo_tmp.mean('time').values, wqbo_tmp.mean('time').values))
        eqbo_out.append(eqbo_tmp.mean('time').values)
        wqbo_out.append(wqbo_tmp.mean('time').values)

        clim.close()
        anom.close()
        eqbo_tmp.close()
        wqbo_tmp.close()
    vt.close()

    eqbo_out = np.array(eqbo_out)
    wqbo_out = np.array(wqbo_out)
    diff_out = np.array(diff_out)
    sigs_out = np.array(sigs_out)
    clim_out = np.array(clim_out)

    # ############ Begin the plotting ############

    fig, ax = plt.subplots()

    mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

    blevs = []

    blevs.append(-2)
    blevs.append(-6)
    blevs.append(-10)
    blevs.append(-25)
    blevs.append(-50)
    blevs.append(-100)

    blevs.append(2)
    blevs.append(6)
    blevs.append(10)
    blevs.append(25)
    blevs.append(50)
    blevs.append(100)

    blevs = np.sort(blevs)
    print(blevs)

    cmin = -200
    cmax = 200
    clevs = np.linspace(cmin, cmax, num=41)
    clevs = [v for v in clevs if v != 0]

    plt.suptitle('QBO (5S-5N index @ %s hPa) zonal-mean eddy heat flux (Km/s)' % int(QBOisobar), fontsize=12,
                 fontweight='normal')

    # Add colormap #
    from palettable.colorbrewer.diverging import RdBu_11
    cmap1 = RdBu_11.mpl_colormap.reversed()

    x, y = np.meshgrid(vt.lat.values, vt.lev.values)

    cols = [0, 1, 2, 3, 4]

    for i in cols:

        print(i)

        # eqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(0, cols[i]))
        plt.title('%s' % titles[i], fontsize=10, y=0.93, fontweight='normal')

        cs = plt.contourf(x, y, eqbo_out[i], blevs,
                          norm=mpl.colors.SymLogNorm(linthresh=2, linscale=1, vmin=-100, vmax=100), cmap=cmap1,
                          extend="both", zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)), fontsize=10)

        # wqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(1, cols[i]))

        cs = plt.contourf(x, y, wqbo_out[i], blevs,
                          norm=mpl.colors.SymLogNorm(linthresh=2, linscale=1, vmin=-100, vmax=100), cmap=cmap1,
                          extend="both", zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')
        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)), fontsize=10)

        # Diff: eqbo minus wqbo #

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(2, cols[i]))

        cs = plt.contourf(x, y, diff_out[i], blevs,
                          norm=mpl.colors.SymLogNorm(linthresh=2, linscale=1, vmin=-100, vmax=100), cmap=cmap1,
                          extend="both", zorder=1)

        mpl.rcParams["lines.linewidth"] = 0.2
        mpl.rcParams["lines.dashed_pattern"] = 10, 3
        black = plt.contour(x, y, clim_out[i], colors='k', levels=clevs, extend="both", vmin=cmin, vmax=cmax,
                            zorder=3)
        plt.clabel(black, black.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)

        plt.semilogy()
        yticks = [1, 5, 10, 100, 1000]
        plt.yticks(yticks, yticks, fontsize=6, fontweight='normal')
        xticks = [-90, -60, -30, 0, 30, 60, 90]
        plt.xticks(xticks, xticks, fontsize=6, fontweight='normal')
        plt.gca().invert_yaxis()
        plt.axis(axes)
        if i == 0:
            plt.ylabel('Pressure (hPa)', fontsize=8, fontweight='normal')
        plt.xlabel('Latitude', fontsize=8, fontweight='normal')

        sig_levs = [0.95, 1]
        mpl.rcParams['hatch.linewidth'] = 0.2
        plt.contourf(x, y, sigs_out[i], colors='black', vmin=0.95, vmax=1, levels=sig_levs,
                     hatches=['......', '......'], alpha=0.0)

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo - wqbo', fontsize=10)

    # Add colorbar #

    oticks = [-100, -50, -25, -10, -6, -2, 2, 6, 10, 25, 50, 100]
    cb_ax = fig.add_axes([0.365, 0.04, 0.30, 0.015])
    cbar = fig.colorbar(cs, cax=cb_ax, ticks=oticks, orientation='horizontal')
    cbar.ax.tick_params(labelsize=8, width=1)
    cbar.ax.set_xticklabels(oticks, weight='normal')

    plt.subplots_adjust(top=0.86, bottom=0.16, hspace=0.5, wspace=0.55, left=0.08, right=0.95)

    return fig, ax


##################################################################################################
##################################################################################################
##################################################################################################

def qbo_slp(ps, negative_indices, positive_indices, QBOisobar, titles, plot_months, projection, axes):
    r""" Compute the sea level pressure response to QBO. Anomalies are defined as
    deviations from the seasonal cycle and composites of anomalies are made during easterly QBO years,
    westerly QBO years, and then their difference is shown. Stippling is used to denote statistical
    significance on the EQBO minus WQBO composites.

    Parameters
    ----------
    ps : xarray.DataArray
        The sea level pressure.

    negative_indices : list
        A list of easterly QBO years.

    positive_indices : list
        A list of westerly QBO years.

    QBOisobar : int
        An integer defined by the user in the config.jsonc file specifying what isobar
        is used to index the QBO

    titles : list of strings
        A list of month names that will be used as the titles for each column of subplots

    plot_months : list
        A list of numbers corresponding to each month (e.g., 10 = october)

    projection : ccrs.NorthPolarStereo() or ccrs.SouthPolarStereo()

    axes : A list of numbers used to set the longitude and latitude bounds of the subplots.
         [-180, 180, 20, 90] are used for the N. hemisphere and [-180, 180, -90, -20] for S. hemisphere

    Returns
    -------
    3 row by 6 column plot of easterly QBO ps anomalies (top row), westerly QBO ps anomalies (middle),
    and their difference (bottom row) with stippling highlighting differences between EQBO
    and WQBO winds statistically significant at the 95% level using a two-sided t-test.

    Notes
    -----
    The input field ps is assumed to have dimensions named "lat" and "lon".
    E.g., if your data has dimensions "latitude" and/or "level",
    use the rename method:
    ds.rename({'latitude':'lat','longitude':'lon'})

    The input field ps is expected to have units of hPa. Directly below, the code
    will check to see if the units are Pa instead, and if they are, convert them to hPa.
    """

    if getattr(ps, 'units') == 'Pa':
        print(f'**Converting pressure levels to hPa')
        ps.attrs['units'] = 'hPa'
        ps.values[:] = ps.values / 100.

    print(np.nanmin(ps.values))
    print(np.nanmedian(ps.values))
    print(np.nanmean(ps.values))
    print(np.nanmax(ps.values))

    eqbo_out = []
    wqbo_out = []
    diff_out = []
    sigs_out = []
    clim_out = []

    for mon in plot_months:

        clim = ps.sel(time=ps.time.dt.month.isin([mon]))
        clim_out.append(clim.mean('time').values)

        anom = clim.groupby("time.month") - clim.groupby("time.month").mean("time")

        if mon == 7 or mon == 8 or mon == 9 or mon == 10 or mon == 11 or mon == 12:
            tmp_negative_indices = np.add(negative_indices, 0)
            tmp_positive_indices = np.add(positive_indices, 0)
        if mon == 1 or mon == 2 or mon == 3:
            tmp_negative_indices = np.add(negative_indices, 1)
            tmp_positive_indices = np.add(positive_indices, 1)

        eqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_negative_indices]))
        wqbo_tmp = anom.sel(time=anom.time.dt.year.isin([tmp_positive_indices]))

        t, p = stats.ttest_ind(eqbo_tmp.values, wqbo_tmp.values, axis=0, nan_policy='omit')

        sigs_out.append(np.subtract(1, p))
        diff_out.append(np.subtract(eqbo_tmp.mean('time').values, wqbo_tmp.mean('time').values))
        eqbo_out.append(eqbo_tmp.mean('time').values)
        wqbo_out.append(wqbo_tmp.mean('time').values)

        clim.close()
        anom.close()
        eqbo_tmp.close()
        wqbo_tmp.close()
    ps.close()

    eqbo_out = np.array(eqbo_out)
    wqbo_out = np.array(wqbo_out)
    diff_out = np.array(diff_out)
    sigs_out = np.array(sigs_out)
    clim_out = np.array(clim_out)

    # ############ Begin the plotting ############

    fig, ax = plt.subplots()

    mpl.rcParams['font.sans-serif'].insert(0, 'Arial')

    vmin = -10
    vmax = 10
    vlevs = np.linspace(vmin, vmax, num=21)
    vlevs = [v for v in vlevs if v != 0]
    ticks = [vmin, vmin / 2, 0, vmax / 2, vmax]

    cmin = 900
    cmax = 1100
    clevs = np.linspace(cmin, cmax, num=21)

    plt.suptitle('QBO (5S-5N index @ %s hPa) sea level pressure (hPa)' % QBOisobar, fontsize=12, fontweight='normal')

    # Add colormap #

    from palettable.colorbrewer.diverging import RdBu_11
    cmap1 = RdBu_11.mpl_colormap.reversed()

    lons = ps.lon.values
    lats = ps.lat.values

    cols = [0, 1, 2, 3, 4]

    for i in cols:

        print(i)

        ########
        # eqbo #
        ########

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(0, cols[i]), projection=projection)
        ax1.set_extent(axes, ccrs.PlateCarree())
        plt.title('%s' % titles[i], fontsize=10, y=0.93, fontweight='normal')

        # Plot style features #

        ax1.coastlines(linewidth=0.25)
        theta = np.linspace(0, 2 * np.pi, 100)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax1.set_boundary(circle, transform=ax1.transAxes)
        pos1 = ax1.get_position()
        plt.title("%s" % titles[i], fontsize=10, fontweight='normal', y=0.98)
        cyclic_z, cyclic_lon = add_cyclic_point(eqbo_out[i], coord=lons)

        # Plot anomalies #

        contourf = ax1.contourf(cyclic_lon, lats, cyclic_z, transform=ccrs.PlateCarree(), cmap=cmap1, vmin=vmin,
                                vmax=vmax, levels=vlevs, extend='both', zorder=1)

        # Overlay the climatology #

        cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
        cs = ax1.contour(cyclic_lon, lats, cyclic_clim, transform=ccrs.PlateCarree(), colors='k', linewidths=0.5,
                         vmin=cmin, vmax=cmax, levels=clevs, extend='both', zorder=3)

        plt.rc('font', weight='normal')
        plt.clabel(cs, cs.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)
        plt.rc('font', weight='normal')

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo (%s seasons)' % int(len(negative_indices)), fontsize=10)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.get_yaxis().set_ticks([])

        ########
        # wqbo #
        ########

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(1, cols[i]), projection=projection)
        ax1.set_extent(axes, ccrs.PlateCarree())

        # Plot style features #

        ax1.coastlines(linewidth=0.25)
        theta = np.linspace(0, 2 * np.pi, 100)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax1.set_boundary(circle, transform=ax1.transAxes)
        pos1 = ax1.get_position()
        plt.title("%s" % titles[i], fontsize=10, fontweight='normal', y=0.98)
        cyclic_z, cyclic_lon = add_cyclic_point(wqbo_out[i], coord=lons)

        # Plot anomalies #

        contourf = ax1.contourf(cyclic_lon, lats, cyclic_z, transform=ccrs.PlateCarree(), cmap=cmap1, vmin=vmin,
                                vmax=vmax, levels=vlevs, extend='both', zorder=1)

        # Overlay the climatology #

        cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
        cs = ax1.contour(cyclic_lon, lats, cyclic_clim, transform=ccrs.PlateCarree(), colors='k', linewidths=0.5,
                         vmin=cmin, vmax=cmax, levels=clevs, extend='both', zorder=3)

        plt.rc('font', weight='normal')
        plt.clabel(cs, cs.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)
        plt.rc('font', weight='normal')

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('wqbo (%s seasons)' % int(len(positive_indices)), fontsize=10)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.get_yaxis().set_ticks([])

        ##############
        # Difference #
        ##############

        ax1 = plt.subplot2grid(shape=(3, 5), loc=(2, cols[i]), projection=projection)
        ax1.set_extent(axes, ccrs.PlateCarree())

        # Plot style features #

        ax1.coastlines(linewidth=0.25)
        theta = np.linspace(0, 2 * np.pi, 100)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax1.set_boundary(circle, transform=ax1.transAxes)
        pos1 = ax1.get_position()
        plt.title("%s" % titles[i], fontsize=10, fontweight='normal', y=0.98)
        cyclic_z, cyclic_lon = add_cyclic_point(diff_out[i], coord=lons)

        # Plot anomalies #

        contourf = ax1.contourf(cyclic_lon, lats, cyclic_z, transform=ccrs.PlateCarree(), cmap=cmap1, vmin=vmin,
                                vmax=vmax, levels=vlevs, extend='both', zorder=1)

        # Statistical significance #

        sig_levs = [0.95, 1]
        mpl.rcParams['hatch.linewidth'] = 0.2
        cyclic_sig, cyclic_lontmp = add_cyclic_point(sigs_out[i], coord=lons)
        ax1.contourf(cyclic_lon, lats, cyclic_sig, transform=ccrs.PlateCarree(), colors='black', vmin=0.95, vmax=1,
                     levels=sig_levs, hatches=['......', '......'], alpha=0.0, zorder=2)

        # Overlay the climatology #

        cyclic_clim, cyclic_lon = add_cyclic_point(clim_out[i], coord=lons)
        cs = ax1.contour(cyclic_lon, lats, cyclic_clim, transform=ccrs.PlateCarree(), colors='k', linewidths=0.5,
                         vmin=cmin, vmax=cmax, levels=clevs, extend='both', zorder=3)

        plt.rc('font', weight='normal')
        plt.clabel(cs, cs.levels[:], inline=1, fmt='%1.0f', fontsize=4, colors='k', inline_spacing=1)
        plt.rc('font', weight='normal')

        if i == 4:
            ax2 = ax1.twinx()
            yticks = [0, 0.5, 1.0]
            ylabels = ['', '', '']
            ax2.set_yticks(yticks)
            ax2.set_yticklabels(ylabels, fontsize=8, fontweight='normal')
            ax2.set_ylabel('eqbo - wqbo', fontsize=10)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.get_yaxis().set_ticks([])

    # Add colorbar #

    cb_ax = fig.add_axes([0.35, 0.05, 0.30, 0.015])
    cbar = fig.colorbar(contourf, cax=cb_ax, ticks=ticks, orientation='horizontal')
    cbar.ax.tick_params(labelsize=8, width=1)
    cbar.ax.set_xticklabels(ticks, weight='normal')

    plt.subplots_adjust(top=0.86, bottom=0.09, hspace=0.3, wspace=0.0, left=0.02, right=0.94)

    return fig, ax
