# ==============================================================================
# MDTF Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC Stratospheric Polar Vortex Extremes
# Last update: 2023-08-22
#
# This script performs calculations to detect stratospheric polar vortex extremes. 
# Extremes in the stratospheric polar vortex are closely linked to the tropospheric
# circulation and surface climate both before and after the event. The occurrence of 
# polar stratospheric circulation extremes in the Northern Hemisphere (NH), such
# as sudden stratospheric warmings (SSWs) and polar vortex intensifications (VIs), are 
# important aspects of stratospheric variability that rely on realistic representations
# of the stratosphere and the troposphere. Extremes in the strength of the Arctic polar 
# stratospheric circulation are often preceded by known near-surface circulation 
# patterns, and then subsequently followed by shifts in weather patterns (sometimes
# for weeks).
# Please see the references for the scientific foundations of this POD.
#
# ==============================================================================
#   Version, Contact Info, and License
# ==============================================================================
#   - Version/revision information: v1.0 (2023-08-22)
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
#   This POD contains two scripts. The primary script is stc_spv_extremes.py. There
#   is a helper script with functions used by the primary script called 
#   stc_spv_extremes_defs.py.
#   The primary script stc_spv_extremes.py goes through these basic steps:
#  
#   (1) reads in the model fields, performs a few preparatory actions such as 
#       averaging the geopotential heights over the polar cap and removing
#       the daily climatology to obtain anomalies, and selecting
#       the 10 hPa zonal-mean zonal winds. 
#   (2) creates three plots (in both hemispheres, so 6 plots in total) 
#   (3) outputs to text files the SSW and VI dates for both hemispheres.
#
# ==============================================================================
#   Required programming language and libraries
# ==============================================================================
#   This POD is done fully in python, and primarily makes use of numpy and
#   xarray to read, subset, and transform the data. 
#
# ==============================================================================
#   Required model input variables
# ==============================================================================
#   This POD requires daily-mean fields of
#   - zonal-man zonal wind velocity (ua) with dimensions of (time,lev,lat)
#   - zonal-mean geopotential heights (zg) with dimensions of (time,lev,lat)
#   - geopotential heights (zg) at 500 hPa with dimensions of (time,lat,lon)
#   - surface air temperature (tas) with dimensions of (time,lat,lon)
#
# ==============================================================================
#   References
# ==============================================================================


import os
import traceback

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib as mpl
import matplotlib.path as mpath
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from matplotlib import pyplot as plt
import statsmodels.api as sm
from stc_spv_extremes_defs import lat_avg
import stc_spv_extremes_defs

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12
mpl.rcParams['hatch.color']='gray'

# Plotting Functions ***************************************


def plot_spv_hist(uzm_10, hemi, filepath_ssw, filepath_vi):
    r""" Calculate SSW and VI central dates, save them to a text file, and plot
    a histogram of their seasonality. 

    Parameters
    ----------
    uzm_10 : `xarray.DataArray` 
        The daily-mean 10 hPa zonal-mean u-wind component with 
        units in m s**-1, as a function of time

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 
    
    filepath_ssw : string
        The file path where the .txt file of central dates of stratospheric
        sudden warmings (and their mean frequency) will be saved.
        
    filepath_vi : string
        The file path where the .txt file of central dates of stratospheric
        vortex intensifications (and their mean frequency) will be saved.

    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    Notes
    -----
    This code uses the python module statsmodels to determine the 95% confidence
    intervals on the frequency of occurrence of SSWs and VIs (binomial distributions),
    using the Wilson score interval.

    """
    
    year = uzm_10.time.dt.year.values 
    yr = np.arange(year[0],year[-1]+1,1)
    
    ssw = None
    vi = None
    if hemi == 'NH':
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec, hem=hemi)
        
        # Determine SSW frequency (in NH, the total years are one less than in 
        # the full uzm_10 data, because each winter straddles two years)
        tot_freq_ssw = len(ssw)/(len(yr)-1)
        
        with open(filepath_ssw, 'w') as file_handler:
            for item in ssw:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR+1}-{LASTYR}: {tot_freq_ssw:.2f}")

        # Determine seasonality of frequency

        seas_ssw = None
        if ssw:
            nov_freq = len([i for i in ssw if i.split("-")[1] == '11'])/(len(ssw))
            dec_freq = len([i for i in ssw if i.split("-")[1 ]== '12'])/(len(ssw))
            jan_freq = len([i for i in ssw if i.split("-")[1] == '01'])/(len(ssw))
            feb_freq = len([i for i in ssw if i.split("-")[1] == '02'])/(len(ssw))
            mar_freq = len([i for i in ssw if i.split("-")[1] == '03'])/(len(ssw))
            seas_ssw = np.array([nov_freq, dec_freq, jan_freq, feb_freq, mar_freq])
            
            ci_snov_lo, ci_snov_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '11']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_sdec_lo, ci_sdec_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '12']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_sjan_lo, ci_sjan_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '01']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_sfeb_lo, ci_sfeb_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '02']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_smar_lo, ci_smar_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '03']),
                                                                 len(ssw), alpha=0.05, method='wilson')

            ci_ssw = [(seas_ssw[0]-ci_snov_lo, ci_snov_up-seas_ssw[0]), (seas_ssw[1]-ci_sdec_lo,
                                                                         ci_sdec_up-seas_ssw[1]),
                      (seas_ssw[2]-ci_sjan_lo, ci_sjan_up-seas_ssw[2]), (seas_ssw[3]-ci_sfeb_lo,
                                                                         ci_sfeb_up-seas_ssw[3]),
                      (seas_ssw[4]-ci_smar_lo, ci_smar_up-seas_ssw[4])]
        
        # Need VI central dates
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        # Determine VI frequency (in NH, the total years are one less than in 
        # the full uzm_10 data, because each winter straddles two years)
        tot_freq_vi = len(vi)/(len(yr)-1)
        
        with open(filepath_vi, 'w') as file_handler:
            for item in vi:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR+1}-{LASTYR}: {tot_freq_vi:.2f}")
        
        # Determine seasonality of frequency
        seas_vi = None
        if vi:
            nov_freq = len([i for i in vi if i.split("-")[1] == '11'])/(len(vi))
            dec_freq = len([i for i in vi if i.split("-")[1] == '12'])/(len(vi))
            jan_freq = len([i for i in vi if i.split("-")[1] == '01'])/(len(vi))
            feb_freq = len([i for i in vi if i.split("-")[1] == '02'])/(len(vi))
            mar_freq = len([i for i in vi if i.split("-")[1] == '03'])/(len(vi))
            seas_vi = np.array([nov_freq, dec_freq, jan_freq, feb_freq, mar_freq])
            
            ci_vnov_lo, ci_vnov_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '11']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vdec_lo, ci_vdec_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '12']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vjan_lo, ci_vjan_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '01']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vfeb_lo, ci_vfeb_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '02']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vmar_lo, ci_vmar_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '03']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vi = [(seas_vi[0]-ci_vnov_lo, ci_vnov_up-seas_vi[0]), (seas_vi[1]-ci_vdec_lo, ci_vdec_up-seas_vi[1]), 
                      (seas_vi[2]-ci_vjan_lo, ci_vjan_up-seas_vi[2]), (seas_vi[3]-ci_vfeb_lo, ci_vfeb_up-seas_vi[3]),
                      (seas_vi[4]-ci_vmar_lo, ci_vmar_up-seas_vi[4])]
        
    if hemi == 'SH':
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=-60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi)
        
        # Determine SSW frequency
        tot_freq_ssw = len(ssw)/len(yr)
        
        with open(filepath_ssw, 'w') as file_handler:
            for item in ssw:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR}-{LASTYR}: {tot_freq_ssw:.2f}")
        
        # Determine seasonality of frequency
        seas_ssw = None
        if ssw:
            jun_freq = len([i for i in ssw if i.split("-")[1] == '06'])/(len(ssw))
            jul_freq = len([i for i in ssw if i.split("-")[1] == '07'])/(len(ssw))
            aug_freq = len([i for i in ssw if i.split("-")[1] == '08'])/(len(ssw))
            sep_freq = len([i for i in ssw if i.split("-")[1] == '09'])/(len(ssw))
            oct_freq = len([i for i in ssw if i.split("-")[1] == '10'])/(len(ssw))
            seas_ssw = np.array([jun_freq, jul_freq, aug_freq, sep_freq, oct_freq])
            
            ci_sjun_lo, ci_sjun_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '06']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_sjul_lo, ci_sjul_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '07']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_saug_lo, ci_saug_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '08']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_ssep_lo, ci_ssep_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '09']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_soct_lo, ci_soct_up = sm.stats.proportion_confint(len([i for i in ssw if i.split("-")[1] == '10']),
                                                                 len(ssw), alpha=0.05, method='wilson')
            ci_ssw = [(seas_ssw[0]-ci_sjun_lo, ci_sjun_up-seas_ssw[0]), (seas_ssw[1]-ci_sjul_lo,
                                                                         ci_sjul_up-seas_ssw[1]),
                      (seas_ssw[2]-ci_saug_lo, ci_saug_up-seas_ssw[2]), (seas_ssw[3]-ci_ssep_lo,
                                                                         ci_ssep_up-seas_ssw[3]),
                      (seas_ssw[4]-ci_soct_lo, ci_soct_up-seas_ssw[4])]
        
        # Need VI central dates
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec, hem=hemi)
        
        # Determine VI frequency
        tot_freq_vi = len(vi)/len(yr)
        
        with open(filepath_vi, 'w') as file_handler:
            for item in vi:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR}-{LASTYR}: {tot_freq_vi:.2f}")
        
        # Determine seasonality of frequency
        seas_vi = None
        if vi:
            jun_freq = len([i for i in vi if i.split("-")[1] == '06'])/(len(vi))
            jul_freq = len([i for i in vi if i.split("-")[1] == '07'])/(len(vi))
            aug_freq = len([i for i in vi if i.split("-")[1] == '08'])/(len(vi))
            sep_freq = len([i for i in vi if i.split("-")[1] == '09'])/(len(vi))
            oct_freq = len([i for i in vi if i.split("-")[1] == '10'])/(len(vi))
            seas_vi = np.array([jun_freq, jul_freq, aug_freq, sep_freq, oct_freq])
            
            ci_vjun_lo, ci_vjun_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '06']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vjul_lo, ci_vjul_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '07']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vaug_lo, ci_vaug_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '08']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vsep_lo, ci_vsep_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '09']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_voct_lo, ci_voct_up = sm.stats.proportion_confint(len([i for i in vi if i.split("-")[1] == '10']),
                                                                 len(vi), alpha=0.05, method='wilson')
            ci_vi = [(seas_vi[0]-ci_vjun_lo, ci_vjun_up-seas_vi[0]), (seas_vi[1]-ci_vjul_lo, ci_vjul_up-seas_vi[1]), 
                      (seas_vi[2]-ci_vaug_lo, ci_vaug_up-seas_vi[2]), (seas_vi[3]-ci_vsep_lo, ci_vsep_up-seas_vi[3]),
                      (seas_vi[4]-ci_voct_lo, ci_voct_up-seas_vi[4])]  
            
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    
    xlab_str = f"Month"
    ylab_str1 = f"Fractional occurrence per month"
    # Set plot limits, add labels, and make axis square
    ax[0].set_xlim(0, 6)
    ax[0].set_ylim(0, 1)
    ax[0].set_xlabel(xlab_str, fontsize=14)
    ax[0].set_ylabel(ylab_str1, fontsize=14)
    ax[0].set_xticks([1, 2, 3, 4, 5])
    
    if hemi == 'NH':
        ax[0].set_xticklabels(['Nov', 'Dec', 'Jan', 'Feb', 'Mar'])
    elif hemi == 'SH':
        ax[0].set_xticklabels(['Jun', 'Jul', 'Aug', 'Sep', 'Oct'])
    
    if ssw:
        ax[0].bar([1, 2, 3, 4, 5], seas_ssw, color='k', edgecolor='k', yerr=np.array(ci_ssw).T, ecolor='grey')
        ax[0].text(.5, .9, f'Total SSW Freq/yr = {tot_freq_ssw:.2f}')
    else:
        ax[0].text(2, .5, 'No SSWs detected')
    
    ax[0].set_title(f'Fraction of {hemi} SSW occurrence by month', fontsize=16)
    
    # Set plot limits, add labels, and make axis square
    ax[1].set_xlim(0, 6)
    ax[1].set_ylim(0, 1)
    ax[1].set_xlabel(xlab_str, fontsize=14)
    ax[1].set_ylabel(ylab_str1, fontsize=14)
    ax[1].set_xticks([1, 2, 3, 4, 5])
    
    if hemi == 'NH':
        ax[1].set_xticklabels(['Nov', 'Dec', 'Jan', 'Feb', 'Mar'])
    elif hemi == 'SH':
        ax[1].set_xticklabels(['Jun', 'Jul', 'Aug', 'Sep', 'Oct'])
    
    if vi:
        ax[1].bar([1, 2, 3, 4, 5], seas_vi, color='k', edgecolor='k', yerr=np.array(ci_vi).T, ecolor='grey')
        ax[1].text(.5, .9, f'Total VI Freq/yr = {tot_freq_vi:.2f}')
    else:
        ax[1].text(2,.5,'No VIs detected')
        
    ax[1].set_title(f'Fraction of {hemi} VI occurrence by month', fontsize=16)
    
    fig.tight_layout()
        
    return fig, ax


def plot_dripping_paint(uzm_10, zg_pcap, hemi):
    
    r""" Plot so-called "dripping paint" plots that illustrate stratosphere-troposphere
    coupling, by compositing polar cap-averaged geopotential heights as a function of 
    pressure level and days around the central dates of SSW and VI events (default is 20 days
    before event to 60 days after). 

    Parameters
    ----------
    uzm_10 : `xarray.DataArray` 
        The daily-mean 10 hPa zonal-mean u-wind component with 
        units in m s**-1, as a function of time

    zg_pcap : `xarray.DataArray` 
        The daily-mean polar cap-averaged geopotential height with 
        units in m, as a function of time and pressure level

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 
    
    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    Notes
    -----
    In these figures, significance is evaluated at the 95% level using a one-sample
    t-test, and assumes that the population mean has an anomaly value of 0 and that
    the sample mean comes from a normally distributed population. This may not be a 
    robust assumption, but here this test is chosen for a computationally inexpensive
    estimate of significance. In these plots, values that are *insignificant* by this
    test are stippled. 

    """
    
    # This function standardizes the polar cap geopotential heights at each pressure
    # level by the daily climatology
    std_anom = zg_pcap.groupby("time.dayofyear").map(stc_spv_extremes_defs.standardize)

    ssw = None
    vi = None
    avgssw = None
    avgvi = None
    if hemi == 'NH':
        
        # Need SSW and VI central dates
        uzm_spec = uzm_10.interp(lat=60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec, hem=hemi)
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec, hem=hemi)
        
        if ssw: 
            yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
            mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
            dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
            # composite across events
            avgssw = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
            [a_mean, prob_ssw] = stc_spv_extremes_defs.ttest_1samp(avgssw, 0., dim="event")

        else:
            print('No SSWs detected')
        
        if vi:
            yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
            mns = np.array([i.split("-")[1] for i in vi]).astype(int)
            dys = np.array([i.split("-")[2] for i in vi]).astype(int)
        
            avgvi = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
            [a_mean, prob_vi] = stc_spv_extremes_defs.ttest_1samp(avgvi,0., dim="event")
        
        else:
            print('No VIs detected')
        
    if hemi == 'SH':
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=-60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec, hem=hemi)
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec, hem=hemi)
        
        if ssw:
            yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
            mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
            dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
            # composite across events
            avgssw = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
            [a_mean, prob_ssw] = stc_spv_extremes_defs.ttest_1samp(avgssw, 0., dim="event")

        else:
            print('No SSWs detected')
        
        if vi:
            yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
            mns = np.array([i.split("-")[1] for i in vi]).astype(int)
            dys = np.array([i.split("-")[2] for i in vi]).astype(int)
        
            avgvi = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
            [a_mean, prob_vi]=stc_spv_extremes_defs.ttest_1samp(avgvi, 0., dim="event")
            
        else:
            print('No VIs detected')

    import matplotlib.colors as colors

    fig, ax = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)
    
    lev = np.linspace(-2, 2, 21)
    cmap = 'RdBu_r'
    
    press = zg_pcap.plev.values
    lag = np.arange(-20, 60, 1)  # lags are hard-coded here (and within stc_spv_extremes_defs.py)
    
    xlab_str = f"Lag [days]"
    ylab_str = f"Pressure [hPa]"
    # Set plot limits, add labels
    ax[0].set_xlim(-20, 60-1)
    ax[0].set_ylim(10, 1000)
    ax[0].set_yscale('log')
    ax[0].invert_yaxis()
    ax[0].set_xlabel(xlab_str, fontsize=14)
    ax[0].set_ylabel(ylab_str, fontsize=14)
        
    if ssw:
    
        ct_ssw = len(ssw)
        
        mask = np.logical_and(prob_ssw > 0.05, prob_ssw < 0.95)
        ax[0].contourf(lag, press, avgssw.mean("event").transpose(), levels=lev, cmap=cmap,
                       norm=colors.CenteredNorm(), extend='both')
        ax[0].contourf(lag,press, mask.transpose(), levels=[.1, 1], hatches=['..'], colors='none')
        ax[0].vlines(x=0, ymin=np.min(press), ymax=np.max(press),color='gray')
        ax[0].set_title(f'Standardized polar cap geopotential height anomalies \n composited for {hemi} SSWs'
                        f'({ct_ssw} events)', fontsize=16)

    else:
        ax[0].text(0,100, 'No SSWs detected') 
    
    ax[1].set_xlim(-20, 60-1)
    ax[1].set_ylim(10, 1000)
    ax[1].set_yscale('log')
    ax[1].invert_yaxis()
    ax[1].set_xlabel(xlab_str, fontsize=14)
    ax[1].set_ylabel(ylab_str, fontsize=14)
    
    if vi:
        
        ct_vi = len(vi)
        
        mask = np.logical_and(prob_vi > 0.05, prob_vi < 0.95)
        m2=ax[1].contourf(lag, press, avgvi.mean("event").transpose(), levels=lev, cmap=cmap, 
                          norm=colors.CenteredNorm(),extend='both')
        ax[1].contourf(lag, press, mask.transpose(), levels=[.1, 1], hatches=['..'], colors='none')
        ax[1].vlines(x=0, ymin=np.min(press), ymax=np.max(press), color='gray')
        ax[1].set_title(f'Composite polar cap geopotential height anomalies \n for {hemi} VIs ({ct_vi} events)',
                        fontsize=16)
        fig.colorbar(m2, ax=ax[:], ticks=lev[::2], orientation='vertical',label='[Std Dev]')
    
    else:
        ax[1].text(0, 100, 'No VIs detected')
         
    return fig, ax


def plot_composite_maps(uzm_10, zg_500, tas, hemi):
    
    r""" Composite 500 hPa geopotential height and near-surface temperature anomalies for a number of days
    before and after the central dates of SSW and VI events (default is 0-30 days
    before event and 0-30 days after). 

    Parameters
    ----------
    uzm_10 : `xarray.DataArray` 
        The daily-mean 10 hPa zonal-mean u-wind component with 
        units in m s**-1, as a function of time

    zg_500 : `xarray.DataArray` 
        The daily-mean 500 mb geopotential height anomalies with 
        units in m, as a function of time, latitude, and longitude
    
    tas : `xarray.DataArray` 
        The daily-mean 2m air temperature anomalies with 
        units in m, as a function of time, latitude, and longitude

    hemi : string 
        Should be either 'NH' or 'SH' for the northern/southern 
        hemisphere, respectively. 
    
    Returns
    -------
    (fig, ax) : tuple
        The tuple containing the matplotlib figure and axis handles 

    """
    
    ssw = None
    vi = None
    zg_ssw = None
    ts_ssw = None
    zg_vi = None
    ts_vi = None
    if hemi == 'NH':
        
        # Need SSW and VI central dates
        uzm_spec = uzm_10.interp(lat=60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec, hem=hemi)
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec, hem=hemi)
        
        if ssw: 
            yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
            mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
            dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
            # composite across events
            zg_ssw = stc_spv_extremes_defs.composite(zg_500, yrs, mns, dys, 30, 30)
            ts_ssw = stc_spv_extremes_defs.composite(tas, yrs, mns, dys, 30, 30)

        else:
            print('No SSWs detected')
        
        if vi:
            yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
            mns = np.array([i.split("-")[1] for i in vi]).astype(int)
            dys = np.array([i.split("-")[2] for i in vi]).astype(int)
         
            zg_vi = stc_spv_extremes_defs.composite(zg_500, yrs, mns, dys, 30, 30)
            ts_vi = stc_spv_extremes_defs.composite(tas, yrs, mns, dys, 30, 30)
        
        else:
            print('No VIs detected')
        
    if hemi == 'SH':
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=-60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi)  
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        if ssw:
            
            yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
            mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
            dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
            # composite across events
            zg_ssw = stc_spv_extremes_defs.composite(zg_500, yrs, mns, dys, 30, 30)
            ts_ssw = stc_spv_extremes_defs.composite(tas, yrs, mns, dys, 30, 30)
            
        else:
            print('No SSWs detected')
        
        if vi:
            
            yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
            mns = np.array([i.split("-")[1] for i in vi]).astype(int)
            dys = np.array([i.split("-")[2] for i in vi]).astype(int)
        
            zg_vi = stc_spv_extremes_defs.composite(zg_500, yrs, mns, dys, 30, 30)
            ts_vi = stc_spv_extremes_defs.composite(tas, yrs, mns, dys, 30, 30)
            
        else:
            print('No VIs detected')
    
    minlat = []
    maxlat = []
    fig = []
    ax = []
    if hemi == 'NH':
        fig, ax = plt.subplots(2, 2, figsize=(10, 10), subplot_kw={'projection': ccrs.NorthPolarStereo()})
        minlat = 30
        maxlat = 90
        
    if hemi == 'SH':
        fig, ax = plt.subplots(2, 2, figsize=(10, 10), subplot_kw={'projection': ccrs.SouthPolarStereo()})
        minlat = -90
        maxlat = -30
    
    lev1 = np.linspace(-80, 80, 21)
    lev1 = np.delete(lev1, [10]) # delete zero level
    lev2 = np.linspace(-2, 2, 21)
    cmap = 'RdBu_r'
    
    m = ax[0, 0].coastlines(linewidth=0.2)
    ax[0, 0].set_extent([-180, 180, minlat, maxlat], ccrs.PlateCarree())
    theta = np.linspace(0, 2*np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    ax[0, 0].set_boundary(circle, transform=ax[0, 0].transAxes)
    
    ax[0, 1].coastlines(linewidth=0.2)
    ax[0, 1].set_extent([-180, 180, minlat, maxlat], ccrs.PlateCarree())
    ax[0, 1].set_boundary(circle, transform=ax[0, 1].transAxes)
    
    ax[1, 0].set_extent([-180, 180, minlat, maxlat], ccrs.PlateCarree())
    ax[1, 0].set_boundary(circle, transform=ax[1, 0].transAxes)
    
    ax[1, 1].coastlines(linewidth=0.2)
    ax[1, 1].set_extent([-180, 180, minlat, maxlat], ccrs.PlateCarree())
    ax[1, 1].set_boundary(circle, transform=ax[1, 1].transAxes)

    if ssw:
        
        ct_ssw = len(ssw)
        lat = zg_ssw.lat.values
        lon = zg_ssw.lon.values
        
        ssw_z_before = zg_ssw.sel(time=slice(-30,-1)).mean(["event","time"])
        ssw_t_before = ts_ssw.sel(time=slice(-30,-1)).mean(["event","time"])
    
        ssw_z_after = zg_ssw.sel(time=slice(0,29)).mean(["event","time"])
        ssw_t_after = ts_ssw.sel(time=slice(0,29)).mean(["event","time"])
    
        cyclic_z, cyclic_lon = add_cyclic_point(ssw_z_before, coord=lon)
        cyclic_t, cyclic_lon = add_cyclic_point(ssw_t_before, coord=lon)
        m = ax[0, 0].contourf(cyclic_lon, lat, cyclic_t, transform=ccrs.PlateCarree(), levels=lev2, cmap=cmap,
                              extend='both')
        m1 = ax[0, 0].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=lev1, colors='k',
                              extend='both')
        ax[0, 0].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=[0], colors='k',
                         linewidths=0.3, extend='both')
        ax[0, 0].set_title(f'30-day average prior to {hemi} SSWs \n ({ct_ssw} events)', fontsize=14)
        ax[0, 0].clabel(m1,m1.levels[::2],inline=False, inline_spacing=1, fontsize=12)
        
        cyclic_z, cyclic_lon = add_cyclic_point(ssw_z_after, coord=lon)
        cyclic_t, cyclic_lon = add_cyclic_point(ssw_t_after, coord=lon)
        m=ax[0, 1].contourf(cyclic_lon, lat, cyclic_t, transform=ccrs.PlateCarree(), levels=lev2, cmap=cmap,
                            extend='both')
        m1=ax[0, 1].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=lev1, colors='k',
                            extend='both')
        ax[0, 1].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=[0], colors='k',
                         linewidths=0.3, extend='both')
        ax[0, 1].set_title(f'30-day average after {hemi} SSWs \n ({ct_ssw} events)', fontsize=14)
        ax[0, 1].clabel(m1, m1.levels[::2], inline=False, inline_spacing=1, fontsize=12)
    
    else:
        ax[0, 0].text(0, 90, 'No SSWs detected')
        ax[0, 1].text(0, 90, 'No SSWs detected')
    
    if vi:
        
        ct_vi = len(vi)
        lat = zg_vi.lat.values
        lon = zg_vi.lon.values
        
        vi_z_before = zg_vi.sel(time=slice(-30, -1)).mean(["event", "time"])
        vi_t_before = ts_vi.sel(time=slice(-30, -1)).mean(["event" ,"time"])
    
        vi_z_after = zg_vi.sel(time=slice(0, 29)).mean(["event", "time"])
        vi_t_after = ts_vi.sel(time=slice(0, 29)).mean(["event", "time"])
    
        cyclic_z, cyclic_lon = add_cyclic_point(vi_z_before, coord=lon)
        cyclic_t, cyclic_lon = add_cyclic_point(vi_t_before, coord=lon)
        m = ax[1, 0].contourf(cyclic_lon, lat, cyclic_t, transform=ccrs.PlateCarree(), levels=lev2, cmap=cmap,
                              extend='both')
        m1 = ax[1, 0].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=lev1, colors='k',
                              linewidths=2,extend='both')
        ax[1, 0].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=[0], colors='k',
                         linewidths=0.3, extend='both')
        ax[1, 0].set_title(f'30-day average prior to {hemi} VIs \n ({ct_vi} events)', fontsize=14)
        ax[1, 0].clabel(m1, m1.levels[::2], inline=False, inline_spacing=1, fontsize=12)
    
        cyclic_z, cyclic_lon = add_cyclic_point(vi_z_after, coord=lon)
        cyclic_t, cyclic_lon = add_cyclic_point(vi_t_after, coord=lon)
        m = ax[1, 1].contourf(cyclic_lon, lat, cyclic_t, transform=ccrs.PlateCarree(), levels=lev2, cmap=cmap,
                              extend='both')
        m1 = ax[1,1].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=lev1, colors='k',
                             linewidths=2,extend='both')
        ax[1, 1].contour(cyclic_lon, lat, cyclic_z, transform=ccrs.PlateCarree(), levels=[0], colors='k',
                         linewidths=0.3, extend='both')
        ax[1, 1].set_title(f'30-day average after {hemi} VIs \n ({ct_vi} events)',fontsize=14)
        ax[1, 1].clabel(m1, m1.levels[::2], inline=False, inline_spacing=1, fontsize=12)
    
    else:
        ax[1, 0].text(0, 90, 'No VIs detected')
        ax[1, 1].text(0, 90, 'No VIs detected')
        
    plt.suptitle("Near-surface air temperature (shading)\n and 500 hPa geopotential height anomalies (contours)",
                 fontsize=16)
    fig.tight_layout()
    
    fig.subplots_adjust(right=0.8)
    cb_ax = fig.add_axes([0.85, 0.25, 0.03, 0.5])
    cbar = fig.colorbar(m, cax=cb_ax, ticks=lev2[::2], orientation='vertical', label='[degK]')
    cbar.ax.tick_params(labelsize=12, width=1)
     
    return fig, ax

##########################################################################
# --- BEGIN SCRIPT --- #
##########################################################################


print('\n=======================================')
print('BEGIN stc_spv_extremes.py ')
print('=======================================\n')

# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = int(os.environ['startdate'])
LASTYR = int(os.environ['enddate'])
WK_DIR = os.environ['WORK_DIR']
OBS_DIR = os.environ['OBS_DATA']

ufi = os.environ['UA_FILE']
zfi = os.environ['ZG_FILE']
z500fi = os.environ['ZG500_FILE']
tasfi = os.environ['TAS_FILE']

# Parse POD-specific environment variables
print('*** Parse POD-specific environment variables ...')
PCAP_LO_LAT = int(os.environ['PCAP_LO_LAT'])

# Do error-checking on these environment variables. Rather than trying to
# correct the values, we throw errors so that users can adjust their config
# files in the appropriate manner, and obtain expected results.
if PCAP_LO_LAT < 30:
    msg = 'PCAP_LO_LAT must be >= 30'
    raise ValueError(msg)
    
# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading variables ...')
print('    zonal-mean ua')
uazm = xr.open_dataset(ufi)['ua']
print('    zonal-mean zg')
zgzm = xr.open_dataset(zfi)['zg']
print('    zg at 500 hPa')
zg500 = xr.open_dataset(z500fi)['zg500']
print('    tas')
tas = xr.open_dataset(tasfi)['tas']

# Restrict to common time period (note, here we assume that all model variables are the same length in time)
mod_firstyr = uazm.time.dt.year.values[0]
mod_lastyr = uazm.time.dt.year.values[-1]
print(mod_firstyr, mod_lastyr)

print(f'***Limiting model data to {FIRSTYR} to {LASTYR}***')
if FIRSTYR < mod_firstyr:
    msg = 'startdate must be >= model first year'
    raise ValueError(msg)
if LASTYR > mod_lastyr:
    msg = 'enddate must be <= model last year'
    raise ValueError(msg)

uazms = uazm.sel(time=slice(str(FIRSTYR), str(LASTYR)))
zgzms = zgzm.sel(time=slice(str(FIRSTYR), str(LASTYR)))
zg500s = zg500.sel(time=slice(str(FIRSTYR), str(LASTYR)))
tass = tas.sel(time=slice(str(FIRSTYR), str(LASTYR)))

# Calendar types may vary across models. To address this, we convert the calendar to "standard"
print(f' *** Calendar type of model is: '+uazms.time.attrs['calendar_type'])

standard_time = pd.date_range(str(FIRSTYR)+"-01-01", str(LASTYR)+"-12-31",freq="D")

if (uazms.time.attrs['calendar_type'] == 'noleap') or (uazms.time.attrs['calendar_type'] == '365_day'):
    print(f' *** Converting to standard calendar ')
    uazms = uazms.interp_calendar(target=standard_time)
    zgzms = zgzms.interp_calendar(target=standard_time)
    zg500s = zg500s.interp_calendar(target=standard_time)
    tass = tass.interp_calendar(target=standard_time)

if uazm.time.attrs['calendar_type'] == '360_day':
    print(f' *** Converting to standard calendar ')
    uazms = uazms.convert_calendar('standard', align_on="year")
    zgzms = zgzms.convert_calendar('standard', align_on="year")
    zg500s = zg500s.convert_calendar('standard', align_on="year")
    tass = tass.convert_calendar('standard', align_on="year")
    
print(f'***Determine whether model pressure levels are in Pa or hPa, convert to hPa')
if getattr(uazms.plev, 'units') == 'Pa':
    print(f'**Converting pressure levels to hPa')
    uazms = uazms.assign_coords({"plev": (uazms.plev/100.)})
    uazms.plev.attrs['units'] = 'hPa'
    zgzms = zgzms.assign_coords({"plev": (zgzms.plev/100.)})
    zgzms.plev.attrs['units'] = 'hPa'

print(f'*** Selecting zonal-mean zonal winds at 10 hPa')
uzm_10 = uazms.sel(plev=10)

print('*** Computing polar cap averages of zonal-mean geopotential height')    
zg_pcap = {}
zg_pcap['NH'] = lat_avg(zgzms,  PCAP_LO_LAT,  90)
zg_pcap['SH'] = lat_avg(zgzms, -90, -PCAP_LO_LAT)

# At this point, no longer need the raw data
uazm = uazm.close()
tas = tas.close()
zgzm = zgzm.close()
zg500 = zg500.close()

# This function removes the daily seasonal cycle. This step can take awhile.
print('*** Computing anomalies of 500 hPa geopotential height and surface temperature') 
zg_anom = zg500s.groupby("time.dayofyear").map(stc_spv_extremes_defs.deseasonalize)
ts_anom = tass.groupby("time.dayofyear").map(stc_spv_extremes_defs.deseasonalize)

zg_500 = {}
# Limit the latitude range without assuming the ordering of lats
zg_500['NH'] = zg_anom.isel(lat = np.logical_and(zg_anom.lat >= 30, zg_anom.lat <= 90))
zg_500['SH'] = zg_anom.isel(lat = np.logical_and(zg_anom.lat >= -90, zg_anom.lat <= -30))

tas = {}
# Limit the latitude range without assuming the ordering of lats
tas['NH'] = ts_anom.isel(lat = np.logical_and(ts_anom.lat >= 30, ts_anom.lat <= 90))
tas['SH'] = ts_anom.isel(lat = np.logical_and(ts_anom.lat >= -90, ts_anom.lat <= -30))

# Create the POD figures for both NH and SH cases
plot_dir = f'{WK_DIR}/model/PS'
for hemi in ['NH','SH']:
    print(f'*** Calculating {hemi} SPV extremes and plotting seasonality')
    freq_plot = f'{plot_dir}/{CASENAME}_{hemi}_Freq_SPV_BarPlot.png'
    filepath_ssw = f'{WK_DIR}/model/netCDF/{CASENAME}_{hemi}_ssw.txt'
    filepath_vi = f'{WK_DIR}/model/netCDF/{CASENAME}_{hemi}_vi.txt'
    fig,ax = plot_spv_hist(uzm_10, hemi, filepath_ssw, filepath_vi)
    fig.savefig(freq_plot)
    
    print(f'*** Creating {hemi} downward coupling composites')
    drip_plot = f'{plot_dir}/{CASENAME}_{hemi}_SPV_Drip_Plot.png'
    fig, ax = plot_dripping_paint(uzm_10, zg_pcap[hemi], hemi)
    fig.savefig(drip_plot)
        
    print(f'*** Creating {hemi} Z500 and tas composites')
    map_plot = f'{plot_dir}/{CASENAME}_{hemi}_SPV_Composite_Map.png'
    fig, ax = plot_composite_maps(uzm_10, zg_500[hemi], tas[hemi], hemi)
    fig.savefig(map_plot)
    
# Output data will have dimensions of [hemi, time, lev], where hemi
# corresponds to the Northern/Southern hemispheres
print('*** Preparing to save derived data')
data_dir = f'{WK_DIR}/model/netCDF'
outfile = data_dir+f'/{CASENAME}_SPV-extremes_diagnostics.nc'

# Prepare the output variables and their metadata
zg_pcap = xr.concat([zg_pcap['SH'], zg_pcap['NH']], dim='hemi')
zg_pcap.name = 'zg_pcap'
zg_pcap.attrs['units'] = 'm'
zg_pcap.attrs['long_name'] = f'{PCAP_LO_LAT}-90 polar cap geopotential heights'

zg_500 = xr.concat([zg_500['SH'], zg_500['NH']], dim='hemi')
zg_500.name = 'zg_500'
zg_500.attrs['units'] = 'm'
zg_500.attrs['long_name'] = f'Daily geopotential height anomalies at 500 hPa'

tas = xr.concat([tas['SH'], tas['NH']], dim='hemi')
tas.name = 'tas'
tas.attrs['units'] = 'K'
tas.attrs['long_name'] = f'Daily surface air temperature anomalies'

# Create merged dataset containing the individual variables
out_ds = xr.merge([zg_pcap,zg_500,tas])
out_ds = out_ds.assign_coords({'hemi':[-1,1]})
out_ds.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

encoding = {'zg_pcap':  {'dtype':'float32',"scale_factor": 0.1}, 
            'zg_500':   {'dtype':'float32',"scale_factor": 0.1}, 
            'tas':      {'dtype':'float32',"scale_factor": 0.1}}

print(f'*** Saving SPV-extremes diagnostics to {outfile}')
out_ds.to_netcdf(outfile, encoding=encoding)

# Loading obs data files & plotting obs figures: ##########################

print(f'*** Now working on obs data\n------------------------------')
obs_file = OBS_DIR + '/stc_spv_extremes_obs-data.nc'

try:
    print(f'*** Reading reanalysis data from {obs_file}')
    obs = xr.open_dataset(obs_file)
    rean = obs.reanalysis
    obs_firstyr = obs.time.dt.year.values[0]
    obs_lastyr = obs.time.dt.year.values[-1]
    
    print(f'***Limiting obs data to {FIRSTYR} to {LASTYR}***')
    if FIRSTYR < obs_firstyr:
        msg = 'FIRSTYR must be >= obs first year'
        raise ValueError(msg)
    if LASTYR > obs_lastyr:
        msg = 'LASTYR must be <= obs last year'
        raise ValueError(msg)
    
    obs = obs.sel(time=slice(str(FIRSTYR),str(LASTYR)))
    
    print(f'*** Selecting zonal-mean zonal winds at 10 hPa')
    uzm_10 = obs.uwnd_zm.sel(plev=10)
    
    print('*** Computing polar cap averages of zonal-mean geopotential height')    
    zg_pcap = {}
    zg_pcap['NH'] = lat_avg(obs.zg_zm,  PCAP_LO_LAT,  90)
    zg_pcap['SH'] = lat_avg(obs.zg_zm, -90, -PCAP_LO_LAT)
    
    # This function removes the daily seasonal cycle
    print('*** Computing anomalies of 500 hPa geopotential height and surface temperature') 
    zg_anom = obs.zg_500.groupby("time.dayofyear").map(stc_spv_extremes_defs.deseasonalize)
    ts_anom = obs.tas.groupby("time.dayofyear").map(stc_spv_extremes_defs.deseasonalize)
    
    zg_500 = {}
    # Limit the latitude range without assuming the ordering of lats
    zg_500['NH'] = zg_anom.isel(lat = np.logical_and(zg_anom.lat >= 30, zg_anom.lat <= 90))
    zg_500['SH'] = zg_anom.isel(lat = np.logical_and(zg_anom.lat >= -90, zg_anom.lat <= -30))
    
    tas = {}
    # Limit the latitude range without assuming the ordering of lats
    tas['NH'] = ts_anom.isel(lat = np.logical_and(ts_anom.lat >= 30, ts_anom.lat <= 90))
    tas['SH'] = ts_anom.isel(lat = np.logical_and(ts_anom.lat >= -90, ts_anom.lat <= -30))
    
    plot_dir = f'{WK_DIR}/obs/PS'
    for hemi in ['NH','SH']:
        print(f'*** Calculating {hemi} SPV extremes and plotting seasonality')
        freq_plot = f'{plot_dir}/obs_{hemi}_Freq_SPV_BarPlot.png'
        filepath_ssw = f'{WK_DIR}/obs/netCDF/{rean}_{hemi}_ssw.txt'
        filepath_vi = f'{WK_DIR}/obs/netCDF/{rean}_{hemi}_vi.txt'
        fig, ax = plot_spv_hist(uzm_10, hemi, filepath_ssw, filepath_vi)
        fig.savefig(freq_plot)
        
        print(f'*** Creating {hemi} downward coupling composites')
        drip_plot = f'{plot_dir}/obs_{hemi}_SPV_Drip_Plot.png'
        fig, ax = plot_dripping_paint(uzm_10, zg_pcap[hemi], hemi)
        fig.savefig(drip_plot)
        
        print(f'*** Creating {hemi} Z500 and tas composites')
        map_plot = f'{plot_dir}/obs_{hemi}_SPV_Composite_Map.png'
        fig, ax = plot_composite_maps(uzm_10, zg_500[hemi], tas[hemi], hemi)
        fig.savefig(map_plot)

except Exception as exc:
    print('*** Unable to create plots from the observational data: ')
    print(exc)
    print(traceback.format_exc())
    
print('\n=====================================')
print('END stc_spv_extremes.py ')
print('=====================================\n')
