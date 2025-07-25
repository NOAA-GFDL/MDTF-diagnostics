# ==============================================================================
# MDTF Strat-Trop Coupling: Annular Modes POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Annular Modes POD of the MDTF 
# code package (see mdtf/MDTF-diagnostics/LICENSE.txt). It defines the plotting 
# functions used by the main driver script.

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = "Roboto"
mpl.rcParams["font.size"] = 12


def plot_doy_timeseries(dat, diag, title=''):
    r""" Plot time series of dayofyear quantities for specific
    annular mode diagnostics.

    Parameters
    ----------
    dat : `xarray.DataArray`
        The input annular mode diagnostic data. Should have only dimensions
        of (dayofyear, lev), with the max dayofyear being either 360 or 365.

    diag : str
        The string specifying the annular mode diagnostic in question.
        Used to determine plot characteristics such as color levels, contour
        lines, and labels.

    title: str
        The string specifying the title to use for the plot.  Defaults to
        an empty string.

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    def _doy_fig_params(diag):
        r""" Nested function for setting the plot parameters.

        Parameters
        ----------
        diag : str
            The string specifying the diagnostic to be plotted.

        Returns
        -------
        params : dict
            The plot parameters for the given diagnostic.

        """

        if diag == 'eftscale':
            clevs = [5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20,
                     24, 28, 32, 36, 40, 48, 56, 64, 72, 80, 88]
            clines = clevs+[96, 104, 112, 120, 130, 140, 150]
            cbar_label = 'e-folding timescale [days]'
            csfmt = '%d'
        elif diag == 'interannstdv':
            clevs = np.linspace(0, 2, 21)
            clines = list(clevs)+[2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0]
            cbar_label = 'Interannual Std. Deviation'
            csfmt = '%0.1f'
        elif diag == 'predictability':
            clevs = np.linspace(0, 0.4, 21)
            clines = list(clevs)+[0.42, 0.44, 0.46, 0.48,
                                  0.5, 0.55, 0.6, 0.65, 0.70]
            cbar_label = 'Predictability (Fraction of Variance explainable)'
            csfmt = '%0.2f'
        else:
            msg = f'Diagnostic {diag} not supported!'
            raise ValueError(msg)

        params = {
            'clevs': clevs,
            'clines': clines,
            'cblabel': cbar_label,
            'csfmt': csfmt
        }
        return params

    # make sure user inputs a valid diagnostic
    diag_options = ['eftscale', 'interannstdv', 'predictability']
    if diag not in diag_options:
        msg = f'diag must be one of {diag_options}'
        raise ValueError(msg)

    # get our figure params
    fig_params = _doy_fig_params(diag)

    # Figure out how we're handling the time axis. We will plot with Jan 1
    # centered in the middle of the plot, but the position of Jan 1 and other
    # months varies based on the underlying calendar of the data
    max_doy = int(dat.dayofyear.max())
    if max_doy == 365:
        # July 1 falls on DOY 182
        roll_to = -181
        xticks = np.array([1, 32, 63, 93, 124, 154, 185,
                          213, 244, 274, 305, 335, 365])
    elif max_doy == 360:
        # July 1 falls on DOY 181
        roll_to = -180
        xticks = np.array([1, 31, 61, 91, 121, 151, 181,
                          211, 241, 271, 301, 331, 360])
    else:
        msg = "The maximum dayofyear in the input data should only be 360 or 365"
        raise ValueError(msg)

    # Set the xtick positions and labels
    xlab_pos = (np.diff(xticks)*0.5)+xticks[0:-1]
    xlabels = ['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J']

    # Plot the color/line contours
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    cbp = ax.contourf(dat.dayofyear, dat.lev.values, dat.roll(dayofyear=roll_to).T,
                      levels=fig_params['clevs'], extend='both', cmap='Spectral_r')
    cs = ax.contour(dat.dayofyear, dat.lev.values, dat.roll(dayofyear=roll_to).T,
                    levels=fig_params['clines'], colors='black', linewidths=0.7)
    plt.clabel(cs, fmt=fig_params['csfmt'], inline=True, inline_spacing=0)

    # Set plot params for y-axis
    ax.set_yscale('log')
    ax.invert_yaxis()
    ax.set_ylim((1000, 1))
    ax.set_ylabel('Pressure [hPa]', fontsize=16)
    plt.yticks([1000, 300, 100, 30, 10, 3, 1], [
               1000, 300, 100, 30, 10, 3, 1], fontsize=14)

    # Set plot params for x-axis
    plt.xticks(xticks, ['']*xticks.size)
    for i, xlabel in enumerate(xlabels):
        plt.text(xlab_pos[i], 1600, xlabel, fontsize=16, ha='center')
    ax.tick_params(axis='both', which='major', length=7, width=1.2)

    # Set up colorbar
    cb = plt.colorbar(cbp, orientation='horizontal', fraction=0.05,
                      location='bottom', aspect=40, pad=0.1, drawedges=True)
    cb.set_label(fig_params['cblabel'], fontsize=18)
    cb.set_ticks(fig_params['clevs'])
    cb.ax.tick_params(which='both', labelsize=13)

    # Set title and return
    plt.title(title, fontsize=20, fontweight='semibold')
    fig.set_size_inches(12, 6)
    return fig


def plot_annmode_eof_structure(sam_struc, nam_struc, title=''):
    r""" Plot the latitudinal structure of the annular modes
    as a function of pressure. Uses a set of standard pressure
    which may not necessarily correspond to those in the input
    data. If a level is not in the data, it will be skipped;
    similarly, if a level is contained in the data that's not
    in the standard set, it will be skipped (this helps to keep
    the visibility nice).

    Parameters
    ----------
    sam_struc : `xarray.DataArray`
        The latitudinal structure of the Southern Annular Mode. Assumed
        to have dimensions (lev, lat), with latitudes spanning -90 to -20

    nam_struc : `xarray.DataArray`
        The latitudinal structure of the Northern Annular Mode. Assumed to
        have dimensions (lev, lat), with latitudes spanning 20 to 90.

    Returns
    -------
    fig : `matplotlib.pyplot.figure`
        The matplotlib figure instance for the plot.

    """

    def _p_to_z(p):
        r""" Nested function for tranforming a pressure level to
        an approximate altitude.

        Parameters
        ----------
        p : numeric or array-like
            The pressure(s) to convert to altitude

        """
        return -7000*np.log(p/1000)

    def _plot_to_ax(ax, am_struc, plevs):
        r""" Nested function for plotting the annular
        mode structures to a given axis

        """
        for i, plev in enumerate(plevs):
            if (plev not in am_struc.lev):
                continue

            z0 = _p_to_z(plev)

            zprof = z0 + am_struc.sel(lev=plev).values*scaling[i]
            ax.plot(am_struc.lat.values, zprof, color='black', linewidth=0.75)
            ax.axhline(z0, color='grey', linewidth=0.5)
        return ax

    # The set of standard pressure levels we will plot from
    std_p = np.array([1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 150, 200,
                      250, 300, 400, 500, 600, 700, 850, 925, 1000])

    # The yticks that will be shown
    yticks = np.array([1, 3, 10, 30, 100, 300, 1000])

    # Generally the EOF Annular Mode structures need some scaling
    # to make them more/less prominent. The structures in the stratosphere
    # need to be scaled down, whereas those in the troposphere need to
    # be scaled up. This is purely for the sake of qualitative appearance.
    scaling = 10*np.exp(np.linspace(-0.2, np.log(6), len(std_p)))

    # Plot the SH annular mode structures
    fig = plt.figure()
    ax = _plot_to_ax(fig.add_subplot(1, 2, 1), sam_struc, std_p)
    plt.xlim((-90, -20))
    plt.ylim((-3000, 53000))
    plt.yticks(_p_to_z(yticks), yticks)
    plt.xticks(np.arange(-90, -19, 10))
    ax.tick_params(labelsize=15)
    plt.ylabel('Pressure [hPa]', fontsize=17)
    plt.title("SH", fontsize=20)

    # Plot the NH annular mode structures
    ax = _plot_to_ax(fig.add_subplot(1, 2, 2), nam_struc, std_p)
    plt.xlim((20, 90))
    plt.ylim((-3000, 53000))
    plt.yticks(_p_to_z(yticks), yticks)
    plt.xticks(np.arange(20, 91, 10))
    ax.tick_params(labelsize=15)
    plt.title("NH", fontsize=20)

    plt.text(0.51, 0.05, "Latitude", fontsize=17,
             transform=fig.transFigure, ha='center')

    fig.subplots_adjust(bottom=0.1, top=0.85)
    fig.set_size_inches(12, 10)

    plt.suptitle(title, fontsize=22, fontweight='semibold')

    return fig
