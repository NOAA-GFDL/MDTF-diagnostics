#!/usr/bin/env python

"""
Python translation of the pr_diurnal_phase.ncl script.
Saves THREE SEPARATE PLOT FILES with improved formatting.
- Uses exact Fourier phase calculation to match NCL.
- Uses 240-degree hue offset (0.66) to match NCL colormap.
- Uses simplified linear color saturation to ensure vibrant colors.
"""

import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import sys
import logging
import yaml
import argparse
import time
import cftime

try:
    import cartopy.crs as ccrs
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False

# --- 1. Plotting & Analysis Constants ---
AMPLITUDE_VMIN = 0.5
AMPLITUDE_VMAX = 5.0
LAT_S = -50.
LAT_N = 50.
LON_W = 0.
LON_E = 360.
TSPD = 24 
HOURS_UTC_24 = np.arange(0, TSPD) 
MODEL_TIME_SHIFT = -3.0  
IMERG_TIME_SHIFT = 0.0   
HUE_OFFSET = 0.66  # (240 / 360) - Sets Midnight to Blue

# ---------------------------------------------------------------
# 2. LOGGER SETUP
# ---------------------------------------------------------------
logger = logging.getLogger()

def setup_logging(work_dir):
    log_dir = os.path.join(work_dir, "model", "PS")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "analysis_pr_diurnal_phase.log")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    for handler in logger.handlers[:]: logger.removeHandler(handler)
    
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# ---------------------------------------------------------------
# 3. ANALYSIS FUNCTIONS
# ---------------------------------------------------------------
def get_fourier_components(dcycle_composite):
    logger.info("    - Calculating Fourier transform...")
    N = len(dcycle_composite.time) 
    fft_result = np.fft.fft(dcycle_composite.values, axis=0)
    amplitude_data = (np.abs(fft_result[1, :, :]) * 2) / N
    phase_rad_data = np.angle(fft_result[1, :, :])
    phase_deg_data = np.degrees(phase_rad_data) 

    amplitude = xr.DataArray(amplitude_data, coords={'lat': dcycle_composite.lat, 'lon': dcycle_composite.lon}, dims=['lat', 'lon'])
    phase_deg = xr.DataArray(phase_deg_data, coords={'lat': dcycle_composite.lat, 'lon': dcycle_composite.lon}, dims=['lat', 'lon'])
    return amplitude, phase_deg

def convert_phase_to_local_time(phase_deg, lon_coords, time_shift):
    logger.info("    - Converting phase to local solar time...")
    phase_gmt_hours = phase_deg / (360.0 / TSPD) 
    lon_offset_hours = (lon_coords / 360.0) * TSPD
    phase_local = phase_gmt_hours - lon_offset_hours - time_shift
    phase_local_hours = phase_local % TSPD
    return phase_local_hours

# ---------------------------------------------------------------
# 4. DATA LOADING 
# ---------------------------------------------------------------
def load_and_process_model_data(config_dict):
    logger.info("--- Processing Model Data ---")
    pr_file = config_dict.get('pr_file')
    pr_var = config_dict.get('pr_var', 'pr')
    start_date_str = config_dict['analysis_period']['start']
    end_date_str = config_dict['analysis_period']['end']

    if not pr_file or not os.path.exists(pr_file):
        logger.error(f"Error: Model file not found at PR_FILE={pr_file}")
        return None

    try:
        time_coder = xr.coding.times.CFDatetimeCoder(use_cftime=True)
        ds_model = xr.open_dataset(pr_file, decode_times=time_coder, decode_timedelta=False)
        date_type = ds_model.indexes['time'].date_type
        start_date_cftime = date_type(*map(int, start_date_str.split('-')))
        end_date_cftime = date_type(*map(int, end_date_str.split('-')))
        time_slice = slice(start_date_cftime, end_date_cftime)
    except Exception as e:
        logger.warning(f"  - Could not auto-detect calendar type ({e}). Falling back to string slicing.")
        time_slice = slice(start_date_str, end_date_str)

    ds_filtered = ds_model.sel(time=time_slice)
    ds_filtered.coords['lon'] = np.mod(ds_filtered['lon'], 360)
    ds_filtered = ds_filtered.sortby('lon')
    da = ds_filtered[pr_var] * 86400.0 
    da = da.sel(lat=slice(LAT_S, LAT_N), lon=slice(LON_W, LON_E)).transpose('time', 'lat', 'lon')
    return da

def load_and_process_imerg_data(config_dict, season):
    logger.info(f"--- Processing IMERG Data for {season} ---")
    base_dir = config_dict.get('processed_satellite_dir')
    imerg_file = os.path.join(base_dir, f"TRMM_{season}.nc") 
    
    if not os.path.exists(imerg_file):
        logger.warning(f"Warning: IMERG file not found for {season}")
        return None 

    ds_imerg = xr.open_dataset(imerg_file)
    ds_imerg['precip'] = ds_imerg['precip'] * 24.0
    da_imerg = ds_imerg['precip'].sel(lat=slice(LAT_S, LAT_N), lon=slice(LON_W, LON_E)).transpose('time', 'lat', 'lon')
    return da_imerg

# ---------------------------------------------------------------
# 5. PLOTTING FUNCTIONS
# ---------------------------------------------------------------
def add_color_wheel(fig, vmin, vmax, subplot_position=[0.85, 0.35, 0.13, 0.3]):
    cax = fig.add_axes(subplot_position, projection='polar')
    n_hue = 24
    n_sat = 10 
    hues = np.linspace(0, 1, n_hue + 1)
    sats = np.linspace(0.05, 1, n_sat) 
    
    for h in range(n_hue):
        for s in range(n_sat):
            hue_val = (hues[h] + 0.5/n_hue + HUE_OFFSET) % 1.0
            color = mcolors.hsv_to_rgb([hue_val, sats[s], 1.0])
            theta_start_rad = (hues[h]) * 2 * np.pi
            theta_end_rad = (hues[h+1]) * 2 * np.pi
            r_start = s / n_sat
            r_end = (s + 1) / n_sat
            cax.add_patch(mpatches.Wedge((0, 0), r_end, np.degrees(theta_start_rad), np.degrees(theta_end_rad), facecolor=color, edgecolor='none', width=(r_end - r_start)))

    cax.set_facecolor('none')
    n_labels = 5
    cax.set_yticks(np.linspace(0, 1, n_labels + 1)[:-1] + (0.5 / n_labels))
    cax.set_yticklabels([f"{val:.1f}" for val in np.linspace(vmin, vmax, n_labels)], fontsize=8)
    cax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
    cax.set_xticklabels(['0hr', '3hr', '6hr', '9hr', '12hr', '15hr', '18hr', '21hr'], fontsize=9)
    cax.set_ylim(0, 1)
    cax.set_title("Phase (hr) & \nAmplitude (mm/day)", fontsize=10)


def plot_phase_amplitude_map(phase, amplitude, season_name, data_source, config_dict):
    logger.info(f"  - Plotting {data_source} Phase/Amplitude map for {season_name}...")
    fig = plt.figure(figsize=(14, 7)) 
    
    hue = (phase / 24.0 + HUE_OFFSET) % 1.0
    saturation = np.clip((amplitude - AMPLITUDE_VMIN) / (AMPLITUDE_VMAX - AMPLITUDE_VMIN), 0.0, 1.0)
    value = np.ones_like(hue)
    
    rgb = mcolors.hsv_to_rgb(np.stack([hue, saturation, value], axis=-1))
    
    if CARTOPY_AVAILABLE:
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
        ax.imshow(rgb, origin='lower', extent=[LON_W, LON_E, LAT_S, LAT_N], transform=ccrs.PlateCarree())
        ax.coastlines(color='0.3', linewidth=0.5)
        gl = ax.gridlines(draw_labels=True, linestyle=':', color='gray', alpha=0.5, ylocs=np.arange(-40, 51, 20)) 
        gl.top_labels = False; gl.right_labels = False
    else:
        ax = fig.add_subplot(1, 1, 1)
        ax.imshow(rgb, origin='lower', extent=[LON_W, LON_E, LAT_S, LAT_N], aspect='auto')
        ax.set_xlim(LON_W, LON_E); ax.set_ylim(LAT_S, LAT_N)

    add_color_wheel(fig, AMPLITUDE_VMIN, AMPLITUDE_VMAX)

    year = config_dict.get('startdate', 'YYYY')
    casename = config_dict.get('casename', 'Model')
    plot_source_name = casename if data_source == "MODEL" else "IMERG"
    plot_year = year if data_source == "MODEL" else "" 
    
    ax.set_title(f"{plot_source_name} {plot_year} - {season_name} Phase (Hue) and Amplitude (Saturation)", fontsize=16)
    fig.subplots_adjust(left=0.05, right=0.80, bottom=0.1, top=0.9)
    
    output_dir = os.path.join(config_dict.get('work_dir', '.'), "model", "PS")
    plt.savefig(os.path.join(output_dir, f"pr_diurnal_phase_{data_source.lower()}_{season_name}.png"), dpi=150) 
    plt.close(fig)


def plot_variance_map(variance, season_name, data_source, config_dict):
    logger.info(f"  - Plotting {data_source} Variance Explained map for {season_name}...")
    fig = plt.figure(figsize=(14, 7)) 

    if CARTOPY_AVAILABLE:
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
        plot_obj = variance.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), levels=np.arange(0, 101, 10), cmap='YlOrRd', add_colorbar=False)
        ax.coastlines(color='0.3', linewidth=0.5)
        gl = ax.gridlines(draw_labels=True, linestyle=':', color='gray', alpha=0.5, ylocs=np.arange(-40, 51, 20)) 
        gl.top_labels = False; gl.right_labels = False
        cbar = fig.colorbar(plot_obj, ax=ax, orientation='vertical', shrink=0.8, aspect=30, pad=0.03)
        cbar.set_label('%', fontsize=14)
    else:
        ax = fig.add_subplot(1, 1, 1)
        variance.plot.contourf(ax=ax, levels=np.arange(0, 101, 10), cmap='YlOrRd', cbar_kwargs={'label': '%', 'shrink': 0.8, 'aspect': 30})
        ax.set_xlim(LON_W, LON_E); ax.set_ylim(LAT_S, LAT_N)
        
    year = config_dict.get('startdate', 'YYYY')
    casename = config_dict.get('casename', 'Model')
    plot_source_name = casename if data_source == "MODEL" else "IMERG"
    plot_year = year if data_source == "MODEL" else ""
    ax.set_title(f"{plot_source_name} {plot_year} - {season_name} Variance Explained by 24hr Cycle (%)", fontsize=16)

    output_dir = os.path.join(config_dict.get('work_dir', '.'), "model", "PS")
    fig.subplots_adjust(left=0.05, right=0.85, bottom=0.1, top=0.9)
    plt.savefig(os.path.join(output_dir, f"pr_diurnal_variance_{data_source.lower()}_{season_name}.png"), dpi=150) 
    plt.close(fig)


def plot_mean_precip_map(mean_precip, season_name, data_source, config_dict):
    logger.info(f"  - Plotting {data_source} Mean Precipitation map for {season_name}...")
    fig = plt.figure(figsize=(14, 7)) 

    if CARTOPY_AVAILABLE:
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
        plot_obj = mean_precip.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), levels=np.arange(0, 21, 2), cmap='GnBu', add_colorbar=False)
        ax.coastlines(color='0.3', linewidth=0.5)
        gl = ax.gridlines(draw_labels=True, linestyle=':', color='gray', alpha=0.5, ylocs=np.arange(-40, 51, 20))
        gl.top_labels = False; gl.right_labels = False
        cbar = fig.colorbar(plot_obj, ax=ax, orientation='vertical', shrink=0.8, aspect=30, pad=0.03)
        cbar.set_label('mm/day', fontsize=14)
    else:
        ax = fig.add_subplot(1, 1, 1)
        mean_precip.plot.contourf(ax=ax, levels=np.arange(0, 21, 2), cmap='GnBu', cbar_kwargs={'label': 'mm/day', 'shrink': 0.8, 'aspect': 30})
        ax.set_xlim(LON_W, LON_E); ax.set_ylim(LAT_S, LAT_N)

    year = config_dict.get('startdate', 'YYYY')
    casename = config_dict.get('casename', 'Model')
    plot_source_name = casename if data_source == "MODEL" else "IMERG"
    plot_year = year if data_source == "MODEL" else ""
    ax.set_title(f"{plot_source_name} {plot_year} - {season_name} Mean Precipitation (mm/day)", fontsize=16)

    output_dir = os.path.join(config_dict.get('work_dir', '.'), "model", "PS")
    fig.subplots_adjust(left=0.05, right=0.85, bottom=0.1, top=0.9)
    plt.savefig(os.path.join(output_dir, f"pr_diurnal_mean_{data_source.lower()}_{season_name}.png"), dpi=150)
    plt.close(fig)

# ---------------------------------------------------------------
# 6. CONFIG AND MAIN
# ---------------------------------------------------------------
def load_config(config_path):
    try:
        with open(config_path, 'r') as f: return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}"); sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    setup_logging(config.get('work_dir', '.'))

    try:
        model_da_full = load_and_process_model_data(config)
        
        for season in ['JJA', 'DJF']:
            logger.info(f"\n===== Starting {season} Diurnal Cycle Analysis =====")

            if model_da_full is not None:
                model_ds_season = model_da_full.where(model_da_full['time'].dt.season == season, drop=True)
                if model_ds_season.time.size > 0:
                    dcycle_composite_model = model_ds_season.groupby(model_ds_season.time.dt.hour).mean(dim='time').interp(hour=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"}).rename({'hour': 'time'})
                    mean_precip_model = dcycle_composite_model.mean(dim='time')
                    amplitude_model, phase_deg_model = get_fourier_components(dcycle_composite_model)
                    phase_local_model = convert_phase_to_local_time(phase_deg_model, dcycle_composite_model.lon, MODEL_TIME_SHIFT)
                    variance_explained_model = (((amplitude_model**2) / 2.0) / dcycle_composite_model.var(dim='time') * 100.0).clip(0, 100)
                    
                    plot_phase_amplitude_map(phase_local_model, amplitude_model, season, "MODEL", config)
                    plot_variance_map(variance_explained_model, season, "MODEL", config)
                    plot_mean_precip_map(mean_precip_model, season, "MODEL", config)

            imerg_da_season = load_and_process_imerg_data(config, season)
            if imerg_da_season is not None:
                dcycle_composite_imerg = imerg_da_season.interp(time=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"})
                mean_precip_imerg = dcycle_composite_imerg.mean(dim='time')
                amplitude_imerg, phase_deg_imerg = get_fourier_components(dcycle_composite_imerg)
                phase_local_imerg = convert_phase_to_local_time(phase_deg_imerg, dcycle_composite_imerg.lon, IMERG_TIME_SHIFT)
                variance_explained_imerg = (((amplitude_imerg**2) / 2.0) / dcycle_composite_imerg.var(dim='time') * 100.0).clip(0, 100)
                
                plot_phase_amplitude_map(phase_local_imerg, amplitude_imerg, season, "IMERG", config)
                plot_variance_map(variance_explained_imerg, season, "IMERG", config)
                plot_mean_precip_map(mean_precip_imerg, season, "IMERG", config)

    except Exception as e:
        logger.error("A fatal error occurred in main()!", exc_info=True)

if __name__ == "__main__":
    main()