# ==============================================================================
# MDTF Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# ==============================================================================
#
# This file is part of the Strat-Trop Coupling: Stratospheric Polar Vortex Extremes
# POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# STC Stratospheric Polar Vortex Extremes
# Last update: 2023-07-19
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
#   - Version/revision information: v1.0 (2023-07-19)
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
import numpy.ma as ma
import xarray as xr
import matplotlib as mpl
from matplotlib import pyplot as plt
from datetime import datetime,timedelta

from stc_spv_extremes_defs import lat_avg
import stc_spv_extremes_defs

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = 'Roboto'
mpl.rcParams['font.size'] = 12
mpl.rcParams['hatch.color']='gray'


#*********** Plotting Functions ***************************************

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
    ADD HERE

    """
    
    year = uzm_10.time.dt.year.values 
    yr = np.arange(year[0],year[-1]+1,1)

    if (hemi == 'NH'):
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi)
        
        # Determine SSW frequency (in NH, the total years are one less than in 
        # the full uzm_10 data, because each winter straddles two years)
        tot_freq_ssw = len(ssw)/(len(yr)-1)
        
        with open(filepath_ssw, 'w') as file_handler:
            for item in ssw:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR+1}-{LASTYR}: {tot_freq_ssw:.2f}")
        
        #Determine seasonality of frequency
        nov_freq = len([i for i in ssw if i.split("-")[1]=='11'])/(len(yr)-1)
        dec_freq = len([i for i in ssw if i.split("-")[1]=='12'])/(len(yr)-1)
        jan_freq = len([i for i in ssw if i.split("-")[1]=='01'])/(len(yr)-1)
        feb_freq = len([i for i in ssw if i.split("-")[1]=='02'])/(len(yr)-1)
        mar_freq = len([i for i in ssw if i.split("-")[1]=='03'])/(len(yr)-1)
        seas_ssw = np.array([nov_freq, dec_freq, jan_freq, feb_freq, mar_freq])
        
        # Need VI central dates
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        # Determine VI frequency (in NH, the total years are one less than in 
        # the full uzm_10 data, because each winter straddles two years)
        tot_freq_vi = len(vi)/(len(yr)-1)
        
        with open(filepath_vi, 'w') as file_handler:
            for item in vi:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR+1}-{LASTYR}: {tot_freq_vi:.2f}")
        
        #Determine seasonality of frequency
        nov_freq = len([i for i in vi if i.split("-")[1]=='11'])/(len(yr)-1)
        dec_freq = len([i for i in vi if i.split("-")[1]=='12'])/(len(yr)-1)
        jan_freq = len([i for i in vi if i.split("-")[1]=='01'])/(len(yr)-1)
        feb_freq = len([i for i in vi if i.split("-")[1]=='02'])/(len(yr)-1)
        mar_freq = len([i for i in vi if i.split("-")[1]=='03'])/(len(yr)-1)
        seas_vi = np.array([nov_freq, dec_freq, jan_freq, feb_freq, mar_freq])
        
    if (hemi == 'SH'):
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=-60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi)
        
        # Determine SSW frequency
        tot_freq_ssw = len(ssw)/len(yr)
        
        with open(filepath_ssw, 'w') as file_handler:
            for item in ssw:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR}-{LASTYR}: {tot_freq_ssw:.2f}")
        
        #Determine seasonality of frequency
        jun_freq = len([i for i in ssw if i.split("-")[1]=='06'])/(len(yr))
        jul_freq = len([i for i in ssw if i.split("-")[1]=='07'])/(len(yr))
        aug_freq = len([i for i in ssw if i.split("-")[1]=='08'])/(len(yr))
        sep_freq = len([i for i in ssw if i.split("-")[1]=='09'])/(len(yr))
        oct_freq = len([i for i in ssw if i.split("-")[1]=='10'])/(len(yr))
        seas_ssw = np.array([jun_freq, jul_freq, aug_freq, sep_freq, oct_freq])
        
         # Need VI central dates
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        # Determine VI frequency
        tot_freq_vi = len(vi)/len(yr)
        
        with open(filepath_vi, 'w') as file_handler:
            for item in vi:
                file_handler.write(f"{item}\n")
            file_handler.write(f"Frequency for {FIRSTYR}-{LASTYR}: {tot_freq_vi:.2f}")
        
        #Determine seasonality of frequency
        jun_freq = len([i for i in vi if i.split("-")[1]=='06'])/(len(yr))
        jul_freq = len([i for i in vi if i.split("-")[1]=='07'])/(len(yr))
        aug_freq = len([i for i in vi if i.split("-")[1]=='08'])/(len(yr))
        sep_freq = len([i for i in vi if i.split("-")[1]=='09'])/(len(yr))
        oct_freq = len([i for i in vi if i.split("-")[1]=='10'])/(len(yr))
        seas_vi = np.array([jun_freq, jul_freq, aug_freq, sep_freq, oct_freq])
        
            
    fig, ax = plt.subplots(1,2, figsize=(10, 5))
    
    xlab_str = f"Month"
    ylab_str1 = f"SSW frequency per year"
    # Set plot limits, add labels, and make axis square
    ylims = (0, np.around(seas_ssw.max(),decimals=2)+0.05)
    ax[0].set_xlim(0,6)
    ax[0].set_ylim(ylims)
    ax[0].set_xlabel(xlab_str, fontsize=14)
    ax[0].set_ylabel(ylab_str1, fontsize=14)
    ax[0].set_xticks([1,2,3,4,5])
    
    if (hemi == 'NH'):
        ax[0].set_xticklabels(['Nov','Dec','Jan','Feb','Mar'])
    elif (hemi == 'SH'):
        ax[0].set_xticklabels(['Jun','Jul','Aug','Sep','Oct'])
    
    ax[0].bar([1,2,3,4,5],seas_ssw,color='k',edgecolor='k')
    ax[0].set_title(f'Frequency of {hemi} SSWs by month',fontsize=16)
    
    ylab_str2 = f"VI frequency per year"
    # Set plot limits, add labels, and make axis square
    ylims = (0, np.around(seas_vi.max(),decimals=2)+0.05)
    ax[1].set_xlim(0,6)
    ax[1].set_ylim(ylims)
    ax[1].set_xlabel(xlab_str, fontsize=14)
    ax[1].set_ylabel(ylab_str2, fontsize=14)
    ax[1].set_xticks([1,2,3,4,5])
    
    if (hemi == 'NH'):
        ax[1].set_xticklabels(['Nov','Dec','Jan','Feb','Mar'])
    elif (hemi == 'SH'):
        ax[1].set_xticklabels(['Jun','Jul','Aug','Sep','Oct'])
    
    ax[1].bar([1,2,3,4,5],seas_vi,color='k',edgecolor='k')
    ax[1].set_title(f'Frequency of {hemi} VIs by month',fontsize=16)
    
    fig.tight_layout()
        
    return (fig,ax)

def plot_dripping_paint(uzm_10, zg_pcap, hemi):
    
    r""" Plot so-called ``dripping paint" plots that illustrate stratosphere-troposphere
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
    ADD HERE

    """
    
    year = uzm_10.time.dt.year.values 
    yr = np.arange(year[0],year[-1]+1,1)
    
    #This function standardizes the polar cap geopotential heights by the daily 
    #climatology
    std_anom = zg_pcap.groupby("time.dayofyear").map(stc_spv_extremes_defs.standardize)

    if (hemi == 'NH'):
        
        # Need SSW and VI central dates
        uzm_spec = uzm_10.interp(lat=60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi) 
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
        mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
        dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
        #composite across events
        avgssw = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
        
        yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
        mns = np.array([i.split("-")[1] for i in vi]).astype(int)
        dys = np.array([i.split("-")[2] for i in vi]).astype(int)
        
        avgvi = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
        
    if (hemi == 'SH'):
        
        # Need SSW central dates
        uzm_spec = uzm_10.interp(lat=-60)
        ssw = stc_spv_extremes_defs.ssw_cp07(uzm_spec,hem=hemi)  
        vi = stc_spv_extremes_defs.spv_vi(uzm_spec,hem=hemi)
        
        yrs = np.array([i.split("-")[0] for i in ssw]).astype(int)
        mns = np.array([i.split("-")[1] for i in ssw]).astype(int)
        dys = np.array([i.split("-")[2] for i in ssw]).astype(int)
        
        #composite across events
        avgssw = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
        
        yrs = np.array([i.split("-")[0] for i in vi]).astype(int)
        mns = np.array([i.split("-")[1] for i in vi]).astype(int)
        dys = np.array([i.split("-")[2] for i in vi]).astype(int)
        
        avgvi = stc_spv_extremes_defs.composite(std_anom, yrs, mns, dys)
    
    import matplotlib.colors as colors
    fig, ax = plt.subplots(2,1, figsize=(10, 8))
    press = avgssw.lev.values
    lag = avgssw.time.values
    
    #is there a way to get white at/near zero?
    lev = np.linspace(-2.2, 2.2, 23)
    cmap ='RdBu_r'

    xlab_str = f"Lag [days]"
    ylab_str = f"Pressure [hPa]"
    # Set plot limits, add labels, and make axis square
    ax[0].set_xlim(-20,60-1)
    ax[0].set_yscale('log')
    ax[0].invert_yaxis()
    ax[0].set_xlabel(xlab_str, fontsize=14)
    ax[0].set_ylabel(ylab_str, fontsize=14)
    
    m=ax[0].contourf(lag, press, avgssw.mean("event").transpose(), levels=lev, cmap=cmap,
                     norm=colors.CenteredNorm(),extend='both')
    ax[0].vlines(x=0,ymin=np.min(press),ymax=np.max(press),color='gray')
    ax[0].set_title(f'Composite polar cap geopotential height anomalies for {hemi} SSWs',fontsize=16)
    
    ax[1].set_xlim(-20,60-1)
    ax[1].set_yscale('log')
    ax[1].invert_yaxis()
    ax[1].set_xlabel(xlab_str, fontsize=14)
    ax[1].set_ylabel(ylab_str, fontsize=14)
    
    m2=ax[1].contourf(lag, press, avgvi.mean("event").transpose(), levels=lev, cmap=cmap, 
                      norm=colors.CenteredNorm(),extend='both')
    ax[1].vlines(x=0,ymin=np.min(press),ymax=np.max(press),color='gray')
    ax[1].set_title(f'Composite polar cap geopotential height anomalies for {hemi} VIs',fontsize=16)
    
    fig.tight_layout()
    
    fig.colorbar(m, ax=ax, ticks=lev[::2], orientation='vertical')
    
    #is there a way to get white at/near zero?
    #add units to colorbar
    #add significance (not sure best way to do this)
    #only make the plot if there is a certain number of events? 
    
        
    return (fig,ax)

##########################################################################
# --- BEGIN SCRIPT --- #
##########################################################################
print('\n=======================================')
print('BEGIN stc_spv_extremes.py ')
print('=======================================\n')

##### Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = int(os.environ['FIRSTYR'])
LASTYR = int(os.environ['LASTYR'])
WK_DIR = os.environ['WK_DIR']
OBS_DIR = os.environ['OBS_DATA']

tfi = os.environ['TA_FILE']
ufi = os.environ['UA_FILE']

# Parse POD-specific environment variables
print('*** Parse POD-specific environment variables ...')
PCAP_LO_LAT = int(os.environ['PCAP_LO_LAT'])

# Do error-checking on these environment variables. Rather than trying to
# correct the values, we throw errors so that users can adjust their config
# files in the appropriate manner, and obtain expected results.
if (PCAP_LO_LAT < 30):
    msg = 'PCAP_LO_LAT must be >= 30'
    raise ValueError(msg)
    
# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading variables ...')
print('    ua')
ua = xr.open_dataset(ufi)['ua']

# Compute the diagnostics (note, here we assume that all model variables are the same length in time)
mod_firstyr = ua.time.dt.year.values[0]
mod_lastyr = ua.time.dt.year.values[-1]
print(mod_firstyr,mod_lastyr)

print(f'***Limiting model data to {FIRSTYR} to {LASTYR}***')
if (FIRSTYR < mod_firstyr):
    msg = 'FIRSTYR must be >= model first year'
    raise ValueError(msg)
if (LASTYR > mod_lastyr):
    msg = 'LASTYR must be <= model last year'
    raise ValueError(msg)

uas = ua.sel(time=slice(str(FIRSTYR),str(LASTYR)))

print(f'*** Computing zonal-means')
uzm = uas.mean(dim="lon")

print(f'***Determine whether model pressure levels are in Pa or hPa, convert to hPa')
if getattr(uzm.lev,'units') == 'Pa':
    print(f'**Converting pressure levels to hPa')
    uzm = uzm.assign_coords({"lev": (uzm.lev/100.)})
    uzm.lev.attrs['units'] = 'hPa'

# At this point, no longer need the raw data
ua = ua.close()

# Create the POD figures for both NH and SH cases
plot_dir = f'{WK_DIR}/model/PS'
for hemi in ['NH','SH']:
    print(f'*** Calculating {hemi} SPV extremes and plotting seasonality')
    freq_plot = f'{plot_dir}/{CASENAME}_{hemi}_Freq_SPV_BarPlot.eps'
    filepath_ssw = f'{WK_DIR}/model/netCDF/{CASENAME}_{hemi}_ssw.txt'
    filepath_vi = f'{WK_DIR}/model/netCDF/{CASENAME}_{hemi}_vi.txt'
    fig,ax = plot_spv_hist(uzm_10, hemi, filepath_ssw, filepath_vi)
    fig.savefig(freq_plot)
        
    print(f'*** Creating {hemi} downward coupling composites')
    drip_plot = f'{plot_dir}/{CASENAME}_{hemi}_SPV_Drip_Plot.eps'
    fig,ax = plot_dripping_paint(uzm_10, zg_pcap[hemi], hemi)
    fig.savefig(drip_plot)

## Loading obs data files & plotting obs figures: ##########################

print(f'*** Now working on obs data\n------------------------------')
obs_file = OBS_DIR + '/stc_spv_extremes_obs-data.nc'

try:
    print(f'*** Reading reanalysis data from {obs_file}')
    obs = xr.open_dataset(obs_file)
    rean = obs.reanalysis
    obs_firstyr = obs.time.dt.year.values[0]
    obs_lastyr = obs.time.dt.year.values[-1]
    
    #NOTE FOR UPDATE: could pull only 10 mb uwnds in make_era5 code, to make file smaller
    # (but may want to keep option open to select other levels)
    print(f'*** Selecting zonal-mean zonal winds at 10 hPa')
    uzm_10 = obs.uwnd_zm.sel(lev=10)
    
    print('*** Computing polar cap averages of zonal-mean geopotential height')    
    zg_pcap = {}
    zg_pcap['NH'] = lat_avg(obs.zg_zm,  PCAP_LO_LAT,  90)
    zg_pcap['SH'] = lat_avg(obs.zg_zm, -90, -PCAP_LO_LAT)
    
    #plot_dir = f'{WK_DIR}/obs/PS'
    plot_dir = f'{WK_DIR}'
    for hemi in ['NH','SH']:
        print(f'*** Calculating {hemi} SPV extremes and plotting seasonality')
        freq_plot = f'{plot_dir}/obs_{hemi}_Freq_SPV_BarPlot.eps'
        #filepath = f'{WK_DIR}/obs/netCDF/{rean}_{hemi}_fsw.txt'
        filepath_ssw = f'/{OBS_DIR}/{rean}_{hemi}_ssw.txt'
        filepath_vi = f'/{OBS_DIR}/{rean}_{hemi}_vi.txt'
        fig,ax = plot_spv_hist(uzm_10, hemi, filepath_ssw, filepath_vi)
        fig.savefig(freq_plot)
        
        print(f'*** Creating {hemi} downward coupling composites')
        drip_plot = f'{plot_dir}/obs_{hemi}_SPV_Drip_Plot.eps'
        fig,ax = plot_dripping_paint(uzm_10, zg_pcap[hemi], hemi)
        fig.savefig(drip_plot)

except:
    print('*** Unable to create plots from the observational data: ')
    print(traceback.format_exc())
    
print('\n=====================================')
print('END stc_spv_extremes.py ')
print('=====================================\n')
