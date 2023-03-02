import os
import traceback

import pandas as pd 
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt

from stc_vert_wave_coupling_calc import lat_avg, \
    zonal_wave_covariance, zonal_wave_coeffs
from stc_vert_wave_coupling_plot import wave_ampl_climo_plot, \
    heatflux_histo_plot, eddy_hgt_hfevents, corrcoh_seasons


########################
# --- BEGIN SCRIPT --- #
########################
print('\n=======================================')
print('BEGIN stc_vert_wave_coupling.py ')
print('=======================================')

# Parse MDTF-set environment variables
print('*** Parse MDTF-set environment variables ...')
CASENAME = os.environ['CASENAME']
FIRSTYR = int(os.environ['FIRSTYR'])
LASTYR = int(os.environ['LASTYR'])
WK_DIR = os.environ['WK_DIR']
OBS_DATA = os.environ['OBS_DATA']

z10fi = os.environ['ZG10_FILE']
z500fi = os.environ['ZG500_FILE']
v50fi = os.environ['VA50_FILE']
t50fi = os.environ['TA50_FILE']

data_dir = f'{WK_DIR}/model/netCDF'
plot_dir = f'{WK_DIR}/model/PS/'
obs_plot_dir = f'{WK_DIR}/obs/PS/'

# Parse POD-specific environment variables
print('*** Parsing POD-specific environment variables')

SAVE_DERIVED_DATA = bool(int(os.environ['SAVE_DERIVED_DATA']))
USE_MODEL_THRESH = bool(int(os.environ['USE_MODEL_EHF_THRESH']))
USE_CONSISTENT_YEARS = bool(int(os.environ['USE_CONSISTENT_YEARS']))
OBS_FIRSTYR = int(os.environ['OBS_FIRSTYR'])
OBS_LASTYR = int(os.environ['OBS_LASTYR'])

# user wishes to use same years as model inputdata
if USE_CONSISTENT_YEARS is True: 
    OBS_FIRSTYR = FIRSTYR
    OBS_LASTYR = LASTYR

# data provided with POD only spans from 1979-2019
if (OBS_FIRSTYR < 1979) or (OBS_LASTYR > 2019): 
    msg = 'OBS_FIRSTYR and OBS_LASTYR must be between 1979-2019'
    raise ValueError(msg)

print(f'(SETTINGS) Will use {FIRSTYR}-{LASTYR} for {CASENAME}')
print(f'(SETTINGS) Will use {OBS_FIRSTYR}-{OBS_LASTYR} for obs')

# Read the input model data
print(f'*** Now starting work on {CASENAME}\n------------------------------')
print('*** Reading model variables ...')
print('    zg10')
z10 = xr.open_dataset(z10fi)['zg10']
print('    zg500')
z500 = xr.open_dataset(z500fi)['zg500']
print('    va50')
v50 = xr.open_dataset(v50fi)['va50']
print('    ta50')
t50 = xr.open_dataset(t50fi)['ta50']

# Read in the pre-digested obs data and subset the times
print('*** Now reading in pre-digested ERA5 data')
try:
    # geohgt fourier coefficients for +/- 60lat   
    tmp_zk60 = xr.open_dataset(f'{OBS_DATA}/era5_60-lat_hgt-zonal-fourier-coeffs.nc')
    obs_z_k_60 = tmp_zk60.z_k_real + 1j*tmp_zk60.z_k_imag
    obs_z_k_60.attrs['nlons'] = tmp_zk60.nlons
    obs_z_k_60 = obs_z_k_60.sel(time=slice(f'{OBS_FIRSTYR}',f'{OBS_LASTYR}'))

    # geohgt fourier coefficients averaged for 45-80 lat bands
    tmp_zk4580 = xr.open_dataset(f'{OBS_DATA}/era5_45-80-lat_hgt-zonal-fourier-coeffs.nc')
    obs_z_k_4580 = tmp_zk4580.z_k_real + 1j*tmp_zk4580.z_k_imag
    obs_z_k_4580.attrs['nlons'] = tmp_zk4580.nlons
    obs_z_k_4580 = obs_z_k_4580.sel(time=slice(f'{OBS_FIRSTYR}',f'{OBS_LASTYR}'))

    # 50 hPa 60-90 lat polar cap eddy heat flux
    obs_vt50_k_pcap = xr.open_dataarray(f'{OBS_DATA}/era5_50hPa_pcap_eddy-heat-flux.nc')
    obs_vt50_k_pcap = obs_vt50_k_pcap.sel(time=slice(f'{OBS_FIRSTYR}',f'{OBS_LASTYR}'))

    # northern hemisphere eddy geohgts
    obs_nh_zg_eddy = xr.open_dataarray(f'{OBS_DATA}/era5_zg-eddy_NH-JFM-only_2p5.nc')
    obs_nh_zg_eddy = obs_nh_zg_eddy.sel(time=slice(f'{OBS_FIRSTYR}',f'{OBS_LASTYR}'))

    # southern hemisphere eddy geohgts
    obs_sh_zg_eddy = xr.open_dataarray(f'{OBS_DATA}/era5_zg-eddy_SH-SON-only_2p5.nc')
    obs_sh_zg_eddy = obs_sh_zg_eddy.sel(time=slice(f'{OBS_FIRSTYR}',f'{OBS_LASTYR}'))
                                        
    can_plot_obs = True
except:
    msg = f'*** Unable to read all of the pre-digested ERA5 data. ' +\
            'Please check that you have the pre-digested data in {OBS_DATA}'
    print(msg)
    print(traceback.format_exc())
    can_plot_obs = False

# Begin computing the necessary diagnostics
print('*** Computing 10 and 500 hPa zonal Fourier coefficients')
z_k = xr.concat((zonal_wave_coeffs(z10, keep_waves=[1,2,3]).assign_coords({'lev':10}),
                 zonal_wave_coeffs(z500, keep_waves=[1,2,3]).assign_coords({'lev':500})), dim='lev')

print('*** Computing the 45-80 latitude band averages of the Fourier coefficients')
z_k_4580 = xr.concat((lat_avg(z_k, -80, -45).assign_coords({'hemi': -1}),
                     lat_avg(z_k, 45, 80).assign_coords({'hemi': 1})), dim='hemi')

print('*** Computing the 50 hPa eddy heat flux as a function of zonal wavenumber')
vt50_k = zonal_wave_covariance(v50,t50, keep_waves=[1,2,3])

print('*** Computing polar cap averages of eddy heat fluxes')
vt50_k_pcap = xr.concat((lat_avg(vt50_k, -90, -60).assign_coords({'hemi': -1}),
                        lat_avg(vt50_k, 60,   90).assign_coords({'hemi': 1})), dim='hemi')

print('*** Computing the 10 and 500 hPa eddy height fields')
z_eddy_10 = z10 - z10.mean('lon')
z_eddy_500 = z500 - z500.mean('lon')


### BEGIN WAVE AMP CLIMO CODEBLOCK ###
hs = {60: 'N', -60: 'S'}
amp_titles = '{} 60°{} GeoHgt Wave Amplitudes ({}-{})'
amp_finames = '{}-60{}-wave-amps.eps'

for lat in [60, -60]:
    if can_plot_obs is True:
        obs2plot = obs_z_k_60.convert_calendar('noleap', use_cftime=True)

        print(f'*** Plotting the obs {lat}lat wave amplitude climatologies')
        fig = wave_ampl_climo_plot(obs2plot, lat, obs=None)

        title = amp_titles.format('ERA5', hs[lat], OBS_FIRSTYR, OBS_LASTYR)
        plt.suptitle(title, fontweight='semibold', fontsize=20)

        finame = amp_finames.format('ERA5', hs[lat])
        fig.savefig(obs_plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')
    else:
        obs2plot = None

    print(f'*** Plotting the model {lat}lat wave amplitude climatologies')
    fig = wave_ampl_climo_plot(z_k.convert_calendar('noleap', use_cftime=True), lat, obs=obs2plot)

    title = amp_titles.format(CASENAME, hs[lat], FIRSTYR, LASTYR)
    plt.suptitle(title, fontweight='semibold', fontsize=20)

    finame = amp_finames.format(CASENAME, hs[lat])
    fig.savefig(plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')

if SAVE_DERIVED_DATA is True:
    print('*** Saving the model FFT coefficients for +/- 60 lat')
    tmp = z_k.interp(lat=[-60,60])

    z_k_real = np.real(tmp)
    z_k_real.name = 'z_k_real'
    z_k_real.attrs['long_name'] = 'Real part of longitudinal Fourier Transform of Geopot. Height'
    z_k_real.attrs['units'] = 'm'

    z_k_imag = np.imag(tmp)
    z_k_imag.name = 'z_k_imag'
    z_k_imag.attrs['long_name'] = 'Imaginary part of longitudinal Fourier Transform of Geopot. Height'
    z_k_imag.attrs['units'] = 'm'

    outfile = f'{data_dir}/{CASENAME}_60-lat_hgt-zonal-fourier-coeffs.nc'
    encoding = {'z_k_real': {'dtype': 'float32'},
                'z_k_imag': {'dtype': 'float32'}}
    dat2save = xr.merge([z_k_real, z_k_imag])
    dat2save.to_netcdf(outfile, encoding=encoding)
### END WAVE AMP CLIMO CODEBLOCK ### 


### BEGIN EDDY HEAT FLUX HISTO CODEBLOCK ### 
hs = {1: 'NH', -1: 'SH'}
seas = {1: 'JFM', -1: 'SON'}
mons = {1:  [1,2,3], -1: [9,10,11]}

ehf_titles = '{} Eddy Heat Flux Distributions\n50 hPa, 60-90°{} ({}, {}-{})'
ehf_finames = '{}-vt-histos-{}.eps'

for hemi in [1, -1]:
    if can_plot_obs is True:
        obs2plot = obs_vt50_k_pcap.sel(hemi=hemi)

        print(f'*** Plotting the obs {hs[hemi]} heat flux histos for {seas[hemi]}')
        fig = heatflux_histo_plot(obs2plot, mons[hemi], hemi, obs=None)

        title = ehf_titles.format('ERA5', hs[hemi][0], seas[hemi], OBS_FIRSTYR, OBS_LASTYR)
        plt.suptitle(title, fontweight='semibold', fontsize=21, y=0.93)

        finame = ehf_finames.format('ERA5', hs[hemi])
        fig.savefig(obs_plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')
    else:
        obs2plot = None
    print(f'*** Plotting the model {hs[hemi]} heat flux histos for {seas[hemi]}')
    fig = heatflux_histo_plot(vt50_k_pcap.sel(hemi=hemi), mons[hemi], hemi, obs=obs2plot)

    title = ehf_titles.format(CASENAME, hs[hemi][0], seas[hemi], FIRSTYR, LASTYR)
    plt.suptitle(title, fontweight='semibold', fontsize=21, y=0.93)

    finame = ehf_finames.format(CASENAME, hs[hemi])
    fig.savefig(plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')

if SAVE_DERIVED_DATA is True:
    print('*** Saving the model polar cap eddy heat fluxes')
    vt50_k_pcap.name = 'ehf_pcap_50'
    vt50_k_pcap.attrs['long_name'] = '50 hPa 60-90 lat polar cap eddy heat flux'
    vt50_k_pcap.attrs['units'] = 'K m s-1'
    vt50_k_pcap.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

    outfile = f'{data_dir}/{CASENAME}_50hPa_pcap_eddy-heat-flux.nc'
    encoding = {'ehf_pcap_50': {'dtype': 'float32'}}
    vt50_k_pcap.to_netcdf(outfile, encoding=encoding)
### END EDDY HEAT FLUX HISTO CODEBLOCK ### 


### BEGIN EDDY HEIGHT COMPOSITE CODEBLOCK ###
ehc_titles = '{} Extreme Heat Flux Composites\n' +\
             '{} Eddy Heights & Anomalies ({}, {}-{})'
ehc_finames = '{}-extreme-vt-eddy-heights-{}.eps'
obs_zg_eddy = {
    1: obs_nh_zg_eddy,
    -1: obs_sh_zg_eddy
}
for hemi in [1, -1]:
    if can_plot_obs is True:
        obs_vt = obs_vt50_k_pcap.sel(hemi=hemi, zonal_wavenum=1)
        obs_vt = obs_vt.where(obs_vt['time.month'].isin(mons[hemi]), drop=True)

        print(f'*** Computing 10th/90th percentiles of obs 50 hPa polar '+\
              f'cap heat fluxes for {hs[hemi]} {seas[hemi]}')
        obs_lo_thresh = np.percentile(obs_vt, 10)
        obs_hi_thresh = np.percentile(obs_vt, 90)

        print(f'*** Finding obs dates of extreme pos/neg heat flux events for {hs[hemi]} {seas[hemi]}')
        lo_dates = obs_vt.where(obs_vt < obs_lo_thresh, drop=True).time
        hi_dates = obs_vt.where(obs_vt > obs_hi_thresh, drop=True).time
    
        print(f'*** Making obs heat flux event composite maps for {hs[hemi]} {seas[hemi]}')
        fig = eddy_hgt_hfevents(obs_zg_eddy[hemi].sel(lev=10), 
                                obs_zg_eddy[hemi].sel(lev=500), 
                                hi_dates, lo_dates, hemi)
        
        title = ehc_titles.format('ERA5', hs[hemi], seas[hemi], OBS_FIRSTYR, OBS_LASTYR)
        plt.suptitle(title, fontweight='semibold', fontsize=21)

        finame = ehc_finames.format('ERA5', hs[hemi])
        fig.savefig(obs_plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')

    else:
        obs_lo_thresh = None 
        obs_hi_thresh = None
    
    model_vt = vt50_k_pcap.sel(hemi=hemi, zonal_wavenum=1)
    model_vt = model_vt.where(model_vt['time.month'].isin(mons[hemi]), drop=True)

    if (obs_lo_thresh is None) or (USE_MODEL_THRESH is True):
        print(f'*** Using model derived heat flux thresholds to find event dates')
        lo_thresh = np.percentile(model_vt, 10)
        hi_thresh = np.percentile(model_vt, 90)
    else:
        lo_thresh = obs_lo_thresh
        hi_thresh = obs_hi_thresh

    if (lo_thresh > 0):
        print(f'*** (WARNING) The lower heat flux threshold exceeds 0! Interpret results with caution!')
    print(f'*** Finding model dates of extreme pos/neg heat flux events '+\
          f'for {hs[hemi]} {seas[hemi]}')
    lo_dates = model_vt.where(model_vt < lo_thresh, drop=True).time
    hi_dates = model_vt.where(model_vt > hi_thresh, drop=True).time

    print(f'*** Making model heat flux event composite maps for {hs[hemi]} {seas[hemi]}')
    fig = eddy_hgt_hfevents(z_eddy_10, z_eddy_500, hi_dates, lo_dates, hemi)

    title = ehc_titles.format(CASENAME, hs[hemi], seas[hemi], FIRSTYR, LASTYR)
    plt.suptitle(title, fontweight='semibold', fontsize=21)

    finame = ehc_finames.format(CASENAME, hs[hemi])
    fig.savefig(plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')
### END EDDY HEIGHT COMPOSITE CODEBLOCK ###


### BEGIN CORRELATION COHERENCE CODEBLOCK ### 
hs = {1: 'NH', -1: 'SH'}
cc_titles = '{} {} Winter Seasons ({}-{})'
cc_finames = '{}-corr-coh-{}.eps'
ehf_seas = {
    1:  [1,2,3],
    -1: [9,10,11]
}
for hemi in [1, -1]:
    if can_plot_obs is True:
        print(f'*** Plotting the obs {hs[hemi]} correlation coherence bimonthly composites')
        fig = corrcoh_seasons(obs_z_k_4580.sel(hemi=hemi), hemi)

        title = cc_titles.format('ERA5', hs[hemi], OBS_FIRSTYR, OBS_LASTYR)
        plt.suptitle(title, fontweight='semibold', fontsize=24)

        finame = cc_finames.format('ERA5', hs[hemi])
        fig.savefig(obs_plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')

    print(f'*** Plotting the model {hs[hemi]} correlation coherence bimonthly composites')
    fig = corrcoh_seasons(z_k_4580.sel(hemi=hemi), hemi)

    title = cc_titles.format(CASENAME, hs[hemi], FIRSTYR, LASTYR)
    plt.suptitle(title, fontweight='semibold', fontsize=24)

    finame = cc_finames.format(CASENAME, hs[hemi])
    fig.savefig(plot_dir+finame, facecolor='white', dpi=150, bbox_inches='tight')

if SAVE_DERIVED_DATA is True:
    print('*** Saving the model FFT coefficients for 45-80 lat bands')
    z_k_real = np.real(z_k_4580)
    z_k_real.name = 'z_k_real'
    z_k_real.attrs['long_name'] = 'Real part of 45-80 lat band average of ' +\
                                'longitudinal Fourier Transform of Geopot. Height'
    z_k_real.attrs['units'] = 'm'

    z_k_imag = np.imag(z_k_4580)
    z_k_imag.name = 'z_k_imag'
    z_k_imag.attrs['long_name'] = 'Imag part of 45-80 lat band average of ' +\
                                'longitudinal Fourier Transform of Geopot. Height'
    z_k_imag.attrs['units'] = 'm'

    outfile = f'{data_dir}/{CASENAME}_45-80-lat_hgt-zonal-fourier-coeffs.nc'
    encoding = {'z_k_real': {'dtype': 'float32'},
                'z_k_imag': {'dtype': 'float32'}}
    dat2save = xr.merge([z_k_real, z_k_imag])
    dat2save.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'
    dat2save.to_netcdf(outfile, encoding=encoding)
### END CORRELATION COHERENCE CODEBLOCK ###

print('\n=====================================')
print('END stc_vert_wave_coupling.py ')
print('=====================================\n')