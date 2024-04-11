# ==============================================================================
# MDTF Strat-Trop Coupling: Stratospheric Ozone and Circulation POD
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Stratospheric Ozone and Circulation
# POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC Stratospheric Ozone and Circulation
# Last update: 2023-01-24
#
# This script performs calculations to assess relationships between stratospheric
# ozone and the large-scale circulation. This POD uses monthly-mean zonal mean 
# winds, temperatures, and ozone. Ozone-circulation coupling occurs during spring
# when sunlight returns to the polar region and the radiative influence of ozone
# anomalies drives changes to meridional temperature gradients and thus zonal winds, 
# which can then dynamically drive temperatures changes, which feedback onto 
# ozone chemistry. For example, in years when the Antarctic ozone hole is larger
# (more ozone loss) in early spring, the polar vortex stays stronger and persists
# later, leading to a later transition of the vortex at 50mb to its summertime state, 
# here defined as less than 5 (15) m/s in the NH (SH). This seasonal transition of 
# the polar vortex is called the "final stratospheric warming". Because 
# the Arctic rarely gets cold enough for severe chemical ozone loss, 
# ozone-circulation coupling is primarily observed in the Southern Hemisphere,
# but this POD allows application to both hemispheres, as similar
# relationships may still occur in the Northern Hemisphere during extreme polar
# conditions.
# Please see the references for the scientific foundations of this POD.
#
# ==============================================================================
#   Version, Contact Info, and License
# ==============================================================================
#   - Version/revision information: v1.0 (2023-01-24)
#   - PI: Amy H. Butler, NOAA CSL
#   - Developer/point of contact: Amy H. Butler, amy.butler@noaa.gov
#   - Other contributors: Zachary D. Lawrence, CIRES + CU Boulder / NOAA PSL, 
#     zachary.lawrence@noaa.gov; Dillon Elsbury, CIRES + CU Boulder / NOAA CSL,
#     dillon.elsbury@noaa.gov
#
#  The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
# ==============================================================================
#   Functionality
# ==============================================================================
#   This POD contains two scripts. The primary script is stc_ozone.py. There
#   is a helper script with functions used by the primary script called 
#   stc_ozone_defs.py.
#   The primary script stc_ozone_pod.py goes through these basic steps:
#   (1) Loads in the data and restricts the time period to 1979-2014 for comparison
#       of the ozone depletion period with reanalysis. The 1979-2014 period is the 
#       default period, but the FIRSTYR and LASTYR are all able to be specified in 
#       the settings.jsonc.
#   (2) Computes the zonal-means of the data for specific latitude bands, depending
#       on the variable. These latitude bands be specified in the settings.jsonc.
#   (3) Creates four types of plots. The first is a scatter plot of
#       seasonally-averaged early spring polar cap ozone at 50 mb versus 
#       seasonally-averaged late spring zonal-mean zonal winds at 50 mb. The second 
#       is a scatter plot of seasonally-averaged early spring polar-cap ozone at 
#       50 mb versus the final stratospheric warming day of year (DOY), calculated
#       using monthly-mean zonal winds at 50 mb (function is in stc_ozone_defs.py). 
#       The third plot is lag correlations of the Oct (Apr) polar-cap ozone at 50 mb
#       with zonal-mean zonal winds over the specified latitude band in the SH (NH)
#       for all pressure levels and for the two months before and after the spring 
#       ozone anomaly (stippling shows non-significance at the 0.05 level). The 
#       fourth plot shows linear trends as a function of pressure and month for 
#       polar cap temperatures, extratropical zonal-mean zonal winds, and polar
#       cap ozone for the (top row) ozone depletion period (by default defined here as 
#       1979-1999) and (bottom row) ozone recovery period (by default defined
#       here as 2000-2014). These specific time intervals are able to be adjusted but
#       only by changing the values in the function "plot_o3_seas_trends" found 
#       within the primary script.
#   (4) Outputs the three diagnostics (lat-band averaged eddy heat fluxes,
#       polar cap temperatures, and polar cap geopotential heights)
#
# ==============================================================================
#   Required programming language and libraries
# ==============================================================================
#   This POD is done fully in python, and primarily makes use of numpy and
#   xarray to read, subset, and transform the data. It also makes use of scipy to
#   calculate the fast fourier transform (FFT) of the annual cycle of zonal winds
#   in order to estimate the timing of the seasonal transition of the stratospheric
#   polar vortex, and to calculate linear trends.
#
# ==============================================================================
#   Required model input variables
# ==============================================================================
#   This POD requires monthly-mean fields of
#   - zonal wind velocity (ua)
#   - mole fraction of ozone (o3)
#   - air temperature (ta)
#   which should all be provided with dimensions of (time, lev, lat, lon)
#
# ==============================================================================
#   References
# ==============================================================================
#   Hardiman, S. C., et al. (2011), Improved predictability of the troposphere 
#       using stratospheric final warmings, J. Geophys. Res., 116, D18113, 
#       doi:10.1029/2011JD015914. 
#   Butler, A. H. and Domeisen, D. I. V. (2021): The wave geometry of final 
#       stratospheric warming events, Weather Clim. Dynam., 2, 453–474, 
#       https://doi.org/10.5194/wcd-2-453-2021.
#   Son, S.-W., et al. (2010), Impact of stratospheric ozone on Southern Hemisphere
#       circulation change: A multimodel assessment, J. Geophys. Res., 115, D00M07, 
#       doi:10.1029/2010JD014271. 
#   Son, S.-W., et al. (2018). Tropospheric jet response to Antarctic ozone 
#       depletion: An update with Chemistry-Climate Model Initiative (CCMI) models. 
#       Environmental Research Letters, 13(5), 54024.
#   Banerjee, A., Fyfe, J.C., Polvani, L.M., Waugh, D. & Chang, K.-L., 2020. 
#       A pause in Southern Hemisphere circulation trends due to the Montreal Protocol.
#       Nature, 579(7800), 544–548. doi: 10.1038/s41586-020-2120-4.

import os
import traceback

import numpy as np
import numpy.ma as ma
import xarray as xr
import matplotlib as mpl
from matplotlib import pyplot as plt
from scipy.stats import linregress
import datetime

from stc_ozone_defs import lat_avg
from stc_ozone_defs import calc_fsw
from stc_ozone_defs import l_trend
from stc_ozone_defs import t_test_corr

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12
mpl.rcParams['hatch.color']='gray'


#*********** Plotting Functions ***************************************

def plot_o3_ustrat_corr(uzm_bnd, o3_pcap, hemi):
    r""" Create a scatterplot showing the relationship between 50 mb
    seasonal-mean ozone and polar vortex winds in the stratosphere. 

    Parameters
    ----------
    uzm_bnd : `xarray.DataArray` 
        The zonal-mean u-wind component with units in m s**-1,
        averaged with cosine weighting over a given latitude band

    o3_pcap : `xarray.DataArray`
        The ozone concentration with units in ppmv,
        averaged with cosine weighting over the polar cap

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 

    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    Notes
    -----
    Both o3_pcap and uzm_bnd are assumed to have dimensions of time and pressure.
    If NH is given for hemi, this will do the correlation between FMA polar cap ozone 
    concentration and MAM zonal-mean zonal winds averaged over a latitude 
    band at 50 hPa. If SH is given, this will do it for SON ozone and OND zonal winds.

    """
    
    fig, ax = plt.subplots()

    if hemi == 'NH':
        # Need FMA polar cap ozone at 50 hPa
        xlab_str = f"50 hPa FMA O3" + \
                   f"({PCAP_LO_LAT}-90N), [ppmv]"
        o3_seas = o3_pcap.sel(lev=50).resample(time='QS-FEB').mean('time')
        o3_seas = o3_seas.where(o3_seas.time.dt.month == 2, drop=True)

        # Need MAM polar vortex winds at 50 hPa
        ylab_str = f"50 hPa MAM ({UZM_LO_LAT}-{UZM_HI_LAT}N) U [m s**-1]"
        uzm_seas = uzm_bnd.sel(lev=50).resample(time='QS-MAR').mean('time')
        uzm_seas = uzm_seas.where(uzm_seas.time.dt.month == 3, drop=True)

    elif hemi == 'SH':
        # Need SON polar cap ozone at 50 hPa
        xlab_str = f"50 hPa SON O3 "+\
                   f"({PCAP_LO_LAT}-90S), [ppmv]"
        o3_seas = o3_pcap.sel(lev=50).resample(time='QS-SEP').mean('time')
        o3_seas = o3_seas.where(o3_seas.time.dt.month == 9, drop=True)

        # Need OND polar vortex winds at 50 hPa
        ylab_str = f"50 hPa OND ({UZM_LO_LAT}-{UZM_HI_LAT}S) U [m s**-1]"
        uzm_seas = uzm_bnd.sel(lev=50).resample(time='QS-OCT').mean('time')
        uzm_seas = uzm_seas.where(uzm_seas.time.dt.month == 10, drop=True)

    else:
        msg = f'hemi must be one of NH or SH; entered {hemi}'
        raise ValueError(msg)

    # Determine plot axes from the data
    xlims = (np.round(o3_seas.min())-1, np.round(o3_seas.max())+1)
    ylims = (np.round(uzm_seas.min())-2.5, np.round(uzm_seas.max())+2.5)
    
    # Plot ranges of +/- 1 std and mean
    plt.vlines(o3_seas.mean(),ylims[0],ylims[1],color='gainsboro',linewidth=0.66)
    plt.hlines(uzm_seas.mean(),xlims[0],xlims[1],color='gainsboro',linewidth=0.66)
    plt.axvspan(o3_seas.mean()-o3_seas.std(), o3_seas.mean()+o3_seas.std(),color='whitesmoke')
    plt.axhspan(uzm_seas.mean()-uzm_seas.std(), uzm_seas.mean()+uzm_seas.std(),color='whitesmoke')
    ax.scatter(o3_seas.values, uzm_seas.values, c='dimgrey', s=16,zorder=100)

    # Get the best-fit line and plot it
    m,b,r,p,std_err = linregress(o3_seas.values, uzm_seas.values)
    x = np.linspace(xlims[0],xlims[1])
    plt.plot(x,m*x+b, color='black', linestyle='--', linewidth=0.66,zorder=101)

    # Set plot limits, add labels, and make axis square
    plt.xlim(xlims)
    plt.ylim(ylims)
    plt.xlabel(xlab_str, fontsize=18)
    plt.ylabel(ylab_str, fontsize=18)
    ax.set_aspect(1.0/ax.get_data_ratio(), adjustable='box')

    # Get the correlation and do bootstrapping to determine its 95% CI
    corr = np.corrcoef(o3_seas.values, uzm_seas.values)[0,1]
    nbs = 1000
    corr_bs = []
    for n in range(nbs):
        ixs = np.random.choice(o3_seas.size, size=o3_seas.size)
        r = np.corrcoef(o3_seas.isel(time=ixs).values,
                        uzm_seas.isel(time=ixs).values)[0,1]
        corr_bs.append(r)
    bs_lo, bs_hi = np.percentile(corr_bs, [2.5, 97.5])

    # display the correlation and 95% bootstrap CI
    plt.text(0.45,0.88, f'r={corr:.3f} ({bs_lo:.3f}, {bs_hi:.3f})',
             transform=ax.transAxes, fontsize=16, color='red',
             fontweight='semibold')

    fig.subplots_adjust(left=0.1, right=0.98)
    fig.set_size_inches(6.5, 6.5)

    return fig, ax


def plot_o3_fsw_corr(uzm_50, o3_pcap, hemi, filepath):
    r""" Create a scatterplot showing the relationship between 50 mb
    seasonal-mean ozone and the final stratospheric warming date. 

    Parameters
    ----------
    uzm_50 : `xarray.DataArray` 
        The 50 hPa zonal-mean u-wind component with units in m s**-1,
        as a function of latitude

    o3_pcap : `xarray.DataArray`
        The ozone concentration with units in ppmv,
        averaged with cosine weighting over the polar cap

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 
    
    filepath : string
        The file path where the .txt file of final stratospheric
        warming dates will be saved.

    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    Notes
    -----
    o3_pcap is assumed to have dimensions of time and pressure, uzm_50 to have dimensions
    of time and latitude. The final stratospheric warming (FSW) date is found by interpolating 
    monthly-mean zonal winds at 50 hPa and 60 deg Latitude to daily timescales and 
    determining when the wind falls below 5 (15) m/s in NH (SH) spring. If NH is given
    for hemi, this will do the correlation between FMA polar cap ozone at 50 hPa and FSW
    day of year (DOY). If SH is given, this will do it for SON ozone and FSW DOY.

    """
    fig, ax = plt.subplots()

    if hemi == 'NH':
        # Need FMA polar cap ozone at 50 hPa
        xlab_str = f"50 hPa FMA O3" + \
                   f"({PCAP_LO_LAT}-90N), [ppmv]"
        o3_seas = o3_pcap.sel(lev=50).resample(time='QS-FEB').mean('time')
        o3_seas = o3_seas.where(o3_seas.time.dt.month == 2, drop=True)

        # Need FSW date
        ylab_str = f"50 hPa Final Stratospheric Warming DOY"
        uzm_spec = uzm_50.interp(lat=60)
        fsw = calc_fsw(uzm_spec, hemi=hemi)
        print(fsw)
        doyn = []
        for n in fsw:
            if n == 'NaN':
                aDate = float("NaN")
            else:
                 aDate = datetime.date.fromisoformat(n).timetuple().tm_yday
            doyn.append(aDate)
        doy = np.array(doyn, dtype='float')
        
        with open(filepath, 'w') as file_handler:
            for item in fsw:
                file_handler.write(f"{item}\n")

    elif hemi == 'SH':
        # Need SON polar cap ozone at 50 hPa
        xlab_str = f"50 hPa SON O3" + \
                   f"({PCAP_LO_LAT}-90S), [ppmv]"
        o3_seas = o3_pcap.sel(lev=50).resample(time='QS-SEP').mean('time')
        o3_seas = o3_seas.where(o3_seas.time.dt.month == 9, drop=True)

        # Need FSW date
        ylab_str = f"50 hPa Final Stratospheric Warming DOY"
        uzm_spec = uzm_50.interp(lat=-60)
        fsw = calc_fsw(uzm_spec, hemi=hemi)
        print(fsw)
        doyn = []
        for n in fsw:
            if n == 'NaN':
                aDate = float("NaN")
            else:
                aDate = datetime.date.fromisoformat(n).timetuple().tm_yday
            doyn.append(aDate)
        doy = np.array(doyn, dtype='float')
        
        with open(filepath, 'w') as file_handler:
            for item in fsw:
                file_handler.write(f"{item}\n")

    else:
        msg = f'hemi must be one of NH or SH; entered {hemi}'
        raise ValueError(msg)
     
    # Determine plot axes from the data
    xlims = (np.round(o3_seas.min())-1, np.round(o3_seas.max())+1)
    if hemi == 'NH':
        ylims = (np.nanmin(doy)-3, np.nanmax(doy).max()+3)
    elif hemi == 'SH':
        for i, n in enumerate(doy):
            if n < 180:
                doy[i] = doy[i] + 365  # note, this doesn't account for leap-years
        ylims = (np.round(np.nanmin(doy)-3), np.round(np.nanmax(doy).max()+3))

    # Set plot limits, add labels, and make axis square
    plt.xlim(xlims)
    plt.ylim(ylims)
    plt.xlabel(xlab_str, fontsize=18)
    plt.ylabel(ylab_str, fontsize=18)
    ax.set_aspect(1.0/ax.get_data_ratio(), adjustable='box')
    if hemi == 'SH':
        y_pos = np.arange(np.round(ylims[0]), np.round(ylims[1])+10, 10)
        ax.set_yticks(y_pos)
        y_pos2 = np.where(y_pos <= 365, y_pos, y_pos-365)
        ax.set_yticklabels(y_pos2)
    
    # Plot ranges of +/- 1 std and mean
    plt.vlines(o3_seas.mean(), ylims[0], ylims[1], color='gainsboro', linewidth=0.66)
    plt.hlines(np.nanmean(doy), xlims[0], xlims[1], color='gainsboro', linewidth=0.66)
    plt.axvspan(o3_seas.mean()-o3_seas.std(), o3_seas.mean()+o3_seas.std(), color='whitesmoke')
    plt.axhspan(np.nanmean(doy)-np.nanstd(doy), np.nanmean(doy) + np.nanstd(doy), color='whitesmoke')
    ax.scatter(o3_seas.values, doy, c='dimgrey', s=16, zorder=100)
            
    # Get the correlation and do bootstrapping to determine its 95% CI
    a=ma.masked_invalid(o3_seas.values)
    b=ma.masked_invalid(doy)
    msk = (~a.mask & ~b.mask)
    corr = ma.corrcoef(a[msk], b[msk])[0, 1]
    
    # Get the best-fit line and plot it
    m, yo, r, p, std_err = linregress(a[msk], b[msk])
    x = np.linspace(xlims[0], xlims[1])
    plt.plot(x, m*x+yo, color='black', linestyle='--', linewidth=0.66)

    nbs = 1000
    corr_bs = []
    for n in range(nbs):
        ixs = np.random.choice(o3_seas.size, size=o3_seas.size)
        a = ma.masked_invalid(o3_seas.isel(time=ixs).values)
        b = ma.masked_invalid(doy[ixs])
        msk = (~a.mask & ~b.mask)
        r = ma.corrcoef(a[msk], b[msk])[0, 1]
        corr_bs.append(r)
    bs_lo, bs_hi = np.nanpercentile(corr_bs, [2.5, 97.5])

    # display the correlation and 95% bootstrap CI
    plt.text(0.05,0.08, f'r={corr:.3f} ({bs_lo:.3f}, {bs_hi:.3f})',
             transform=ax.transAxes, fontsize=16, color='red',
             fontweight='semibold')

    fig.subplots_adjust(left=0.1,right=0.98)
    fig.set_size_inches(6.5,6.5)

    return fig, ax


def plot_o3_uwnd_lev_lags(uzm_bnd, o3_pcap, hemi):
    r""" Creates a lag-correlation contour plot assessing the relationship 
    between 50 hPa polar cap ozone and zonal winds averaged over a latitude 
    band for different levels and latitudes when ozone-circulation coupling
    is most active. 

    Parameters
    -----------
    uzm_bnd : `xarray.DataArray` 
        The zonal-mean u-wind component with units in m s**-1,
        averaged with cosine weighting over a given latitude band
        
    o3_pcap : `xarray.DataArray`
        The ozone concentration with units in ppmv,
        averaged with cosine weighting over the polar cap

    hemi : string 
        Should be either 'NH' or 'SH' for northern/southern hemisphere, 
        respectively

    Returns
    -------
    (fig, ax) : tuple
        A tuple containing the matplotlib figure and axis handles 
 
    Notes
    -----
    Assumes that both o3_pcap and uzm_bnd dimensions of time and pressure. 

    If NH is chosen, this function will create a plot correlating the 
    April 50 hPa polar cap ozone with zonal winds aross pressure levels
    between February to June. If SH is chosen, it will instead do it for 
    October 50 hPa polar cap ozone with zonal winds for lags between 
    August and December.   

    """
    
    if hemi == 'NH':
        # Need April 50 mb polar cap ozone
        mon_origin = 'Apr'
        o3_early = o3_pcap.sel(lev=50).where(o3_pcap.time.dt.month == 4, drop=True)
        months = [2, 3, 4, 5, 6]
    elif hemi == 'SH':
        # Need October 50 mb polar cap ozone
        mon_origin = 'Oct'
        o3_early = o3_pcap.sel(lev=50).where(o3_pcap.time.dt.month == 10, drop=True)
        months = [8, 9, 10, 11, 12]
    else:
        msg = f'hemi must be one of NH or SH; entered {hemi}'
        raise ValueError(msg)
    
    # Find the correlations of 50 hPa polar cap ozone with uzm at
    # all pressure levels, for each lag
    lag_corrs = []
    for mon in months:
        uzm_mon = uzm_bnd.where(uzm_bnd.time.dt.month == mon, drop=True)
        data_mat = np.concatenate([o3_early.values[:, np.newaxis],
                                  uzm_mon.values], axis=1)
        corrs = np.corrcoef(data_mat.T)[0, 1:]
        lag_corrs.append(corrs[np.newaxis, ...])
    lag_corrs = np.concatenate(lag_corrs, axis=0)
    
    # Evaluate significance using 2-tailed t-test
    ttests = np.zeros_like(lag_corrs)

    alpha = 0.05 #significance level
    for i in range(len(months)):
        for j in range(len(uzm_bnd.lev.values)):
            ttests[i,j] = t_test_corr(alpha, lag_corrs[i,j], len(o3_early.values))
    fig, ax = plt.subplots()

    xlab_str = "Month"
    ylab_str = "Pressure [hPa]"
    cbp = ax.contourf(np.arange(5), uzm_bnd.lev.values, lag_corrs.T,
                      levels=np.linspace(-1, 1, 21), cmap='RdBu_r', extend='both')
    ax.contourf(np.arange(5), uzm_bnd.lev.values, ttests.T, levels=[-1, 0, 1], hatches=[None, '..'], colors='none')
    ax.set_yscale('log')
    ax.invert_yaxis()
    plt.xticks(np.arange(5), months)
    plt.xlabel(xlab_str, fontsize=18)
    plt.ylabel(ylab_str, fontsize=18)
    plt.title(f'Lag correlation of Zonal-mean Zonal Wind with {mon_origin} 50 hPa polar cap ozone')
    plt.colorbar(cbp, format='%.1f', label='Correlation', ax=[ax], location='bottom')

    fig.set_size_inches(10, 6)
    
    return fig, ax


def plot_o3_seas_trends(uzm_bnd, o3_pcap, t_pcap, start_year1='1979', 
                        end_year1='1999', start_year2='2000', end_year2='2014'):
    r""" Creates a plot similar to Son et al. (2018) Figure 2,
    comparing the linear trends of polar cap ozone and temperatures,
    and polar vortex winds as a function of pressure level and month, for 
    both the (default) 1979-1999 and the 2000-2014 periods. These are 
    essentially periods of stratospheric ozone depletion and recovery.

    Parameters
    -----------
    uzm_bnd : `xarray.DataArray` 
        The zonal-mean u-wind component with units in m s**-1,
        averaged with cosine weighting over a given latitude band,
        as a function of time and pressure level
        
    o3_pcap : `xarray.DataArray`
        The ozone concentration with units in ppmv,
        averaged with cosine weighting over the polar cap,
        as a function of time and pressure level
        
    t_pcap : `xarray.DataArray`
        Air temperatures with units in degK,
        averaged with cosine weighting over the polar cap,
        as a function of time and pressure level
        
    start_year1 : `string' of year value
        Starting year of first period for which trends will be 
        calculated. Default is '1979'

    end_year1 : `string' of year value
        Ending year of first period for which trends will be 
        calculated. Default is '1999'
        
    start_year2 : `string' of year value
        Starting year of second period for which trends will be 
        calculated. Default is '2000'
    
    end_year2 : `string' of year value
        Ending year of second period for which trends will be 
        calculated. Default is '1999'

    Returns
    -------
    (fig, axs) : tuple
        A tuple containing the matplotlib figure and axis handles 
 
    Notes
    -----
    Assumes that o3_pcap, t_pcap and uzm_bnd have time and pressure
    dimensions.  

    """
    o3_tr_early, o3_p_early = l_trend(o3_pcap,start_year1, end_year1)
    t_tr_early, t_p_early = l_trend(t_pcap,start_year1, end_year1)
    u_tr_early, u_p_early = l_trend(uzm_bnd,start_year1, end_year1)
        
    o3_tr_late, o3_p_late = l_trend(o3_pcap,start_year2, end_year2)
    t_tr_late, t_p_late = l_trend(t_pcap,start_year2, end_year2)
    u_tr_late, u_p_late = l_trend(uzm_bnd,start_year2, end_year2)
        
    # Shift around so that it goes JASONDJFMAMJ instead
    t_tr_shift_early = xr.concat([t_tr_early[6:, :], t_tr_early[0:6, :]], dim="month")
    u_tr_shift_early = xr.concat([u_tr_early[6:, :], u_tr_early[0:6, :]], dim="month")
    o3_tr_shift_early = xr.concat([o3_tr_early[6:, :], o3_tr_early[0:6, :]], dim="month")
    o3_p_shift_early = xr.concat([o3_p_early[6:, :], o3_p_early[0:6, :]], dim="month")
    t_p_shift_early = xr.concat([t_p_early[6:, :], t_p_early[0:6, :]], dim="month")
    u_p_shift_early = xr.concat([u_p_early[6:, :], u_p_early[0:6, :]], dim="month")
    
    t_tr_shift_late = xr.concat([t_tr_late[6:, :], t_tr_late[0:6, :]], dim="month")
    u_tr_shift_late = xr.concat([u_tr_late[6:, :], u_tr_late[0:6, :]], dim="month")
    o3_tr_shift_late = xr.concat([o3_tr_late[6:, :], o3_tr_late[0:6, :]], dim="month")
    o3_p_shift_late = xr.concat([o3_p_late[6:, :], o3_p_late[0:6, :]], dim="month")
    t_p_shift_late = xr.concat([t_p_late[6:, :], t_p_late[0:6, :]], dim="month")
    u_p_shift_late = xr.concat([u_p_late[6:, :], u_p_late[0:6, :]], dim="month")
    
    fig, axs = plt.subplots(2, 3, figsize=(12, 10))

    xlab_str = "Month"
    ylab_str = "Pressure (hPa)"

    # Top row shows trends from period of ozone depletion
    cbp = axs[0, 0].contourf(np.arange(12), t_tr_shift_early.lev, t_tr_shift_early.transpose(),
                             levels=np.linspace(-5, 5,  11), cmap='RdBu_r', extend='both')
    axs[0, 0].contourf(np.arange(12), t_p_shift_early.lev, t_p_shift_early.transpose(),
                       levels=[0.05, 0.95], hatches=['..'], colors='none')
    axs[0, 0].set_yscale('log')
    axs[0, 0].invert_yaxis()
    axs[0, 0].set_ylim([1000, 10])
    
    axs[0, 0].set_xticks(np.arange(12))
    axs[0, 0].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J'])
    axs[0, 0].set(xlabel=xlab_str, ylabel=ylab_str, title=f'Polar cap Temperature Trends \n'+start_year1+'-'+end_year1)
    plt.colorbar(cbp, format='%.1f', label='[K/decade]', ax=[axs[0, 0]], location='bottom')
    
    cbp2 = axs[0, 1].contourf(np.arange(12), u_tr_shift_early.lev, u_tr_shift_early.transpose(),
                              levels=np.linspace(-5, 5, 11), cmap='RdBu_r', extend='both')
    axs[0, 1].contourf(np.arange(12), u_p_shift_early.lev, u_p_shift_early.transpose(),
                       levels=[0.05, 0.95], hatches=['..'], colors='none')
    axs[0, 1].set_yscale('log')
    axs[0, 1].invert_yaxis()
    axs[0, 1].set_ylim([1000, 10])
    
    axs[0, 1].set_xticks(np.arange(12))
    axs[0, 1].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J'])
    axs[0, 1].set(xlabel=xlab_str, title=f'Zonal-mean Zonal Wind Trends \n'+start_year1+'-'+end_year1)
    plt.colorbar(cbp2, format='%.1f', label='[m/s per decade]', ax=[axs[0, 1]], location='bottom')
    
    cbp3 = axs[0, 2].contourf(np.arange(12), o3_tr_shift_early.lev, o3_tr_shift_early.transpose(),
                              levels=np.linspace(-1, 1, 11), cmap='RdBu_r', extend='both')
    axs[0, 2].contourf(np.arange(12), o3_p_shift_early.lev, o3_p_shift_early.transpose(),
                       levels=[0.05, 0.95], hatches=['..'], colors='none')
    axs[0, 2].set_yscale('log')
    axs[0, 2].invert_yaxis()
    axs[0, 2].set_ylim([1000, 10])
    
    axs[0, 2].set_xticks(np.arange(12))
    axs[0, 2].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J'])
    axs[0, 2].set(xlabel=xlab_str, title=f'Polar Cap Ozone Trends \n'+start_year1+'-'+end_year1)
    plt.colorbar(cbp3, format='%.1f', label='[ppmv/decade]', ax=[axs[0, 2]], location='bottom')
    
    # Bottom row shows trends from period of ozone recovery
    cbp = axs[1, 0].contourf(np.arange(12), t_tr_shift_late.lev, t_tr_shift_late.transpose(),
                             levels=np.linspace(-5, 5, 11), cmap='RdBu_r', extend='both')
    axs[1, 0].contourf(np.arange(12), t_p_shift_late.lev, t_p_shift_late.transpose(),
                       levels=[0.05, 0.95] ,hatches=['..'], colors='none')
    axs[1, 0].set_yscale('log')
    axs[1, 0].invert_yaxis()
    axs[1, 0].set_ylim([1000, 10])
    
    axs[1, 0].set_xticks(np.arange(12))
    axs[1, 0].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M',' J'])
    axs[1, 0].set(xlabel=xlab_str, ylabel=ylab_str, title=start_year2+'-'+end_year2)
    plt.colorbar(cbp, format='%.1f', label='[K/decade]', ax=[axs[1,0]], location='bottom')

    cbp2 = axs[1, 1].contourf(np.arange(12), u_tr_shift_late.lev, u_tr_shift_late.transpose(),
                              levels=np.linspace(-5, 5, 11), cmap='RdBu_r', extend='both')
    axs[1, 1].contourf(np.arange(12), u_p_shift_late.lev, u_p_shift_late.transpose(),
                       levels=[0.05, 0.95], hatches=['..'], colors='none')
    axs[1, 1].set_yscale('log')
    axs[1, 1].invert_yaxis()
    axs[1, 1].set_ylim([1000, 10])
    
    axs[1, 1].set_xticks(np.arange(12))
    axs[1, 1].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J'])
    axs[1, 1].set(xlabel=xlab_str, title=start_year2+'-'+end_year2)
    plt.colorbar(cbp2, format='%.1f',label='[m/s per decade]', ax=[axs[1,1]], location='bottom')
    
    cbp3 = axs[1, 2].contourf(np.arange(12), o3_tr_shift_late.lev, o3_tr_shift_late.transpose(),
                              levels=np.linspace(-1, 1, 11), cmap='RdBu_r', extend='both')
    axs[1, 2].contourf(np.arange(12), o3_p_shift_late.lev,o3_p_shift_late.transpose(),
                       levels=[0.05, 0.95], hatches=['..'], colors='none')
    axs[1, 2].set_yscale('log')
    axs[1, 2].invert_yaxis()
    axs[1, 2].set_ylim([1000, 10])
    
    axs[1, 2].set_xticks(np.arange(12))
    axs[1, 2].set_xticklabels(['J', 'A', 'S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J'])
    axs[1, 2].set(xlabel=xlab_str, title=start_year2 + '-' + end_year2)
    plt.colorbar(cbp3, format='%.1f', label='[ppmv/decade]', ax=[axs[1, 2]], location='bottom')
    
    return fig, axs

# #########################################################################
# --- BEGIN SCRIPT --- #
# #########################################################################


print('\n=======================================')
print('BEGIN stc_ozone.py ')
print('=======================================\n')

# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = int(os.environ['startdate'])
LASTYR = int(os.environ['enddate'])
WK_DIR = os.environ['WORK_DIR']
OBS_DIR = os.environ['OBS_DATA']

o3fi = os.environ['O3_FILE']
tfi = os.environ['TA_FILE']
ufi = os.environ['UA_FILE']

# Parse POD-specific environment variables
print('*** Parse POD-specific environment variables ...')
UZM_LO_LAT = int(os.environ['UZM_LO_LAT'])
UZM_HI_LAT = int(os.environ['UZM_HI_LAT'])
PCAP_LO_LAT = int(os.environ['PCAP_LO_LAT'])

# Do error-checking on these environment variables. Rather than trying to
# correct the values, we throw errors so that users can adjust their config
# files in the appropriate manner, and obtain expected results.
if UZM_LO_LAT >= UZM_HI_LAT:
    msg = 'UZM_LO_LAT must be less than UZM_HI_LAT, and both must be >= 30'
    raise ValueError(msg)

if UZM_LO_LAT < 30:
    msg = 'UZM_LO_LAT must be >= 30'
    raise ValueError(msg)

if PCAP_LO_LAT < 30:
    msg = 'PCAP_LO_LAT must be >= 30'
    raise ValueError(msg)
    
# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading variables ...')
print('    o3')
o3 = xr.open_dataset(o3fi, decode_cf=True)['o3']
print('    ta')
ta = xr.open_dataset(tfi)['ta']
print('    ua')
ua = xr.open_dataset(ufi)['ua']

# Compute the diagnostics (note, here we assume that all model variables are the same length in time)
mod_firstyr = o3.time.dt.year.values[0]
mod_lastyr = o3.time.dt.year.values[-1]
print(mod_firstyr, mod_lastyr)

print(f'***Limiting model data to {FIRSTYR} to {LASTYR}***')
if FIRSTYR < mod_firstyr:
    msg = 'FIRSTYR must be >= model first year'
    raise ValueError(msg)
if LASTYR > mod_lastyr:
    msg = 'LASTYR must be <= model last year'
    raise ValueError(msg)

o3s = o3.sel(time=slice(str(FIRSTYR), str(LASTYR)))
tas = ta.sel(time=slice(str(FIRSTYR), str(LASTYR)))
uas = ua.sel(time=slice(str(FIRSTYR), str(LASTYR)))

print(f'*** Computing zonal-means')
o3zm = o3s.mean(dim="lon")
uzm = uas.mean(dim="lon")
tzm = tas.mean(dim="lon")

print(f'***Determine whether model pressure levels are in Pa or hPa, convert to hPa')
if getattr(uzm.lev,'units') == 'Pa':
    print(f'**Converting pressure levels to hPa')
    uzm = uzm.assign_coords({"lev": (uzm.lev/100.)})
    uzm.lev.attrs['units'] = 'hPa'
    o3zm = o3zm.assign_coords({"lev": (o3zm.lev/100.)})
    o3zm.lev.attrs['units'] = 'hPa'
    tzm = tzm.assign_coords({"lev": (tzm.lev/100.)})
    tzm.lev.attrs['units'] = 'hPa'

print(f'*** Computing {UZM_LO_LAT}-{UZM_HI_LAT}N and '
      f'{UZM_LO_LAT}-{UZM_HI_LAT}S lat averages of zonal-mean zonal winds')
uzm_50 = uzm.sel(lev=50)
uzm_band = {}
uzm_band['NH'] = lat_avg(uzm,  UZM_LO_LAT,  UZM_HI_LAT)
uzm_band['SH'] = lat_avg(uzm, -UZM_HI_LAT, -UZM_LO_LAT)

print('*** Computing polar cap averages of ozone in ppmv')
# Multiply by 1e6 to get Mole Fraction mol/mol (volume mixing ratio) to ppmv 
o3_new = o3zm * 1e6
    
o3_pcap = {}
o3_pcap['NH'] = lat_avg(o3_new,  PCAP_LO_LAT,  90)
o3_pcap['SH'] = lat_avg(o3_new, -90, -PCAP_LO_LAT)

print('*** Computing polar cap averages of air temperature')
t_pcap = {}
t_pcap['NH'] = lat_avg(tzm,  PCAP_LO_LAT,  90)
t_pcap['SH'] = lat_avg(tzm, -90, -PCAP_LO_LAT)

# At this point, no longer need the raw data
o3 = o3.close()
ta = ta.close()
ua = ua.close()

# Create the POD figures for both NH and SH cases
plot_dir = f'{WK_DIR}/model/PS'
for hemi in ['NH','SH']:
    print(f'*** Plotting {hemi} UZM vs polar cap O3 scatter plot')
    scatter_plot = f'{plot_dir}/{CASENAME}_{hemi}_UZM-O3cap_Scatter.eps'
    fig,ax = plot_o3_ustrat_corr(uzm_band[hemi], o3_pcap[hemi], hemi)
    ax.set_title(f'{CASENAME}\n{hemi}, {FIRSTYR}-{LASTYR}', fontsize=20)
    fig.savefig(scatter_plot)
        
    print(f'*** Plotting {hemi} FSW vs polar cap O3 scatter plot')
    scatter_FSW = f'{plot_dir}/{CASENAME}_{hemi}_FSW-O3cap_Scatter.eps'
    filepath = f'{WK_DIR}/model/netCDF/{CASENAME}_{hemi}_fsw.txt'
    fig, ax = plot_o3_fsw_corr(uzm_50, o3_pcap[hemi], hemi,filepath)
    ax.set_title(f'{CASENAME}\n{hemi}, {FIRSTYR}-{LASTYR}', fontsize=20)
    fig.savefig(scatter_FSW)
        
    print(f'*** Plotting {hemi} UZM vs polar cap O3 lag correlations')
    levcorr_plot = f'{plot_dir}/{CASENAME}_{hemi}_UZM-O3cap_LagCorr_Lev.eps'
    fig, ax = plot_o3_uwnd_lev_lags(uzm_band[hemi], o3_pcap[hemi], hemi)
    plt.suptitle(f'{CASENAME}, {hemi}, {FIRSTYR}-{LASTYR}', fontsize=20)
    fig.savefig(levcorr_plot)
        
    print(f'*** Plotting {hemi} trends in o3, temp, and UZM')
    trends_plot = f'{plot_dir}/{CASENAME}_{hemi}_Trends.eps'
    fig, axs = plot_o3_seas_trends(uzm_band[hemi], o3_pcap[hemi], t_pcap[hemi])
    fig.suptitle(f'{CASENAME}, {hemi}', fontsize=20)
    fig.savefig(trends_plot)
    
# Output data will have dimensions of [hemi, time, lev], where hemi
# corresponds to the Northern/Southern hemispheres
print('*** Preparing to save derived data')
data_dir = f'{WK_DIR}/model/netCDF'
outfile = data_dir+f'/{CASENAME}_ozone-circ_diagnostics.nc'

# Prepare the output variables and their metadata
ua_band = xr.concat([uzm_band['SH'], uzm_band['NH']], dim='hemi')
ua_band.name = 'ua_band'
ua_band.attrs['units'] = 'm s**-1'
ua_band.attrs['long_name'] = f'{UZM_LO_LAT}-{UZM_HI_LAT} lat band zonal-mean zonal wind'

ta_pcap = xr.concat([t_pcap['SH'], t_pcap['NH']], dim='hemi')
ta_pcap.name = 'ta_pcap'
ta_pcap.attrs['units'] = 'K'
ta_pcap.attrs['long_name'] = f'{PCAP_LO_LAT}-90 polar cap temperature'

oz_pcap = xr.concat([o3_pcap['SH'], o3_pcap['NH']], dim='hemi')
oz_pcap.name = 'oz_pcap'
oz_pcap.attrs['units'] = 'ppmv'
oz_pcap.attrs['long_name'] = f'{PCAP_LO_LAT}-90 polar cap ozone'

# Create merged dataset containing the individual variables
out_ds = xr.merge([ua_band,ta_pcap,oz_pcap])
out_ds = out_ds.assign_coords({'hemi':[-1,1]})
out_ds.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

encoding = {'ua_band':  {'dtype':'float32'},
            'ta_pcap':  {'dtype':'float32'},
            'oz_pcap':  {'dtype':'float32'}}

print(f'*** Saving ozone-circulation diagnostics to {outfile}')
out_ds.to_netcdf(outfile, encoding=encoding)

# Loading obs data files & plotting obs figures: ##########################

print(f'*** Now working on obs data\n------------------------------')
obs_file = OBS_DIR + '/stc_ozone_obs-data.nc'

try:
    print(f'*** Reading reanalysis data from {obs_file}')
    obs = xr.open_dataset(obs_file)
    rean = obs.reanalysis
    obs_firstyr = obs.time.dt.year.values[0]
    obs_lastyr = obs.time.dt.year.values[-1]
    
    print(f'*** Computing {UZM_LO_LAT}-{UZM_HI_LAT}N and '+\
          f'{UZM_LO_LAT}-{UZM_HI_LAT}S lat averages of zonal-mean zonal winds')
    uzm_50 = obs.uwnd_zm.sel(lev=50)
    uzm_band = {}
    uzm_band['NH'] = lat_avg(obs.uwnd_zm,  UZM_LO_LAT,  UZM_HI_LAT)
    uzm_band['SH'] = lat_avg(obs.uwnd_zm, -UZM_HI_LAT, -UZM_LO_LAT)
    
    print('*** Computing polar cap averages of ozone in ppmv')
    # Multiply by 1e6 to get mol/mol (volume mixing ratio) to ppmv 
    o3_new = obs.o3_zm * 1e6
    
    o3_pcap = {}
    o3_pcap['NH'] = lat_avg(o3_new,  PCAP_LO_LAT,  90)
    o3_pcap['SH'] = lat_avg(o3_new, -90, -PCAP_LO_LAT)
    
    print('*** Computing polar cap averages of air temperature')
    t_pcap = {}
    t_pcap['NH'] = lat_avg(obs.temp_zm,  PCAP_LO_LAT,  90)
    t_pcap['SH'] = lat_avg(obs.temp_zm, -90, -PCAP_LO_LAT)

    # Create the POD figures for both NH and SH cases
    plot_dir = f'{WK_DIR}/obs/PS'
    for hemi in ['NH','SH']:
        print(f'*** Plotting {hemi} UZM vs polar cap O3 scatter plot from rean')
        scatter_plot = f'{plot_dir}/obs_{hemi}_UZM-O3cap_Scatter.eps'
        fig, ax = plot_o3_ustrat_corr(uzm_band[hemi], o3_pcap[hemi], hemi)
        ax.set_title(f'{rean}\n{hemi}, {obs_firstyr}-{obs_lastyr}', fontsize=20)
        fig.savefig(scatter_plot)
        
        print(f'*** Plotting {hemi} FSW vs polar cap O3 scatter plot from rean')
        filepath = f'{WK_DIR}/obs/netCDF/{rean}_{hemi}_fsw.txt'
        scatter_FSW = f'{plot_dir}/obs_{hemi}_FSW-O3cap_Scatter.eps'
        fig, ax = plot_o3_fsw_corr(uzm_50, o3_pcap[hemi], hemi,filepath)
        ax.set_title(f'{rean}\n{hemi}, {obs_firstyr}-{obs_lastyr}', fontsize=20)
        fig.savefig(scatter_FSW)
        
        print(f'*** Plotting {hemi} UZM vs polar cap O3 lag correlations from rean')
        levcorr_plot = f'{plot_dir}/obs_{hemi}_UZM-O3cap_LagCorr_Lev.eps'
        fig, ax = plot_o3_uwnd_lev_lags(uzm_band[hemi], o3_pcap[hemi], hemi)
        plt.suptitle(f'{rean}, {hemi}, {obs_firstyr}-{obs_lastyr}', fontsize=20)
        fig.savefig(levcorr_plot)
        
        print(f'*** Plotting {hemi} trends in o3, temp, and UZM from rean')
        trends_plot = f'{plot_dir}/obs_{hemi}_Trends.eps'
        fig, axs = plot_o3_seas_trends(uzm_band[hemi], o3_pcap[hemi], t_pcap[hemi])
        fig.suptitle(f'{rean}, {hemi}', fontsize=20)
        fig.savefig(trends_plot)
        
except Exception as exc:
    print('*** Unable to create plots from the observational data: ')
    print(exc)
    print(traceback.format_exc())
    
print('\n=====================================')
print('END stc_ozone_pod.py ')
print('=====================================\n')
