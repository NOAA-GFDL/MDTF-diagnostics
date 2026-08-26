#!/usr/bin/env python

"""
Python translation of the pr_diurnal_cycle.ncl script.
This version contains the fix for the satellite unit conversion
and has been updated with new plot titles and legend labels.
"""

import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import sys
import logging
import yaml
import argparse
import time

# --- 1. Define Hardcoded Regions and Settings (from NCL) ---
REGIONS = [
    {
        "title": "Africa (20E,0) (30E,10N)",
        "north": 10., "south": 0., "west": 20., "east": 30.
    },
    {
        "title": "Tropical S. America (65W,20S) (50W,5S)",
        "north": -5., "south": -20., "west": 295., "east": 310.
    },
    {
        "title": "Borneo (110E,2S) (116E,2N)",
        "north": 2., "south": -2., "west": 110., "east": 116.
    },
    {
        "title": "N. American Plains (105W,34N) (95W,42N)",
        "north": 42., "south": 34., "west": 255., "east": 265.
    },
    {
        "title": "Indian Ocean (65E,10S) (90E,0)",
        "north": 0., "south": -10., "west": 65., "east": 90.
    },
    {
        "title": "Western Pacific (160E,12S) (180E,6S)",
        "north": -6., "south": -12., "west": 160., "east": 180.
    }
]
PLOT_RANGE = (0, 20.)
TSPD = 24
MODEL_TIME_SHIFT = -3.0  # For 6-hourly time-mean data
HOURS_LOCAL = np.arange(0, TSPD + 1)
HOURS_UTC_24 = np.arange(0, TSPD)
HOURS_UTC_3X = np.arange(-TSPD, 2 * TSPD)

# ---------------------------------------------------------------
# 2. LOGGER SETUP
# ---------------------------------------------------------------
logger = logging.getLogger() # Get the root logger

def setup_logging(work_dir):
    """Sets up logging to console and a file in the work_dir."""
    log_dir = os.path.join(work_dir, "model", "PS")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "analysis_pr_diurnal_cycle.log")

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.info(f"Logging initialized. Log file: {log_file}")

# ---------------------------------------------------------------
# 3. ANALYSIS FUNCTIONS
# ---------------------------------------------------------------
# (All functions from get_latitude_weights to process_trmm_data are unchanged)

def get_latitude_weights(lat_coord):
    """Calculates latitude weights (cosine of latitude)."""
    lat_rad = np.deg2rad(lat_coord)
    weights = np.cos(lat_rad)
    return xr.DataArray(weights, coords={'lat': lat_coord}, dims=['lat'])


def correct_to_local_time(da_hourly, is_model=False):
    """
    Adjusts a 24-hour UTC diurnal cycle to local solar time.
    This version robustly rebuilds the coordinates to prevent errors.
    """
    logger.info(f"  Adjusting to local time (is_model={is_model})...")
    
    time_dim_name = "time"
    
    original_lats = da_hourly.lat
    original_lons = da_hourly.lon
    
    da_3dc = xr.concat([da_hourly, da_hourly, da_hourly], dim=time_dim_name)
    da_3dc = da_3dc.assign_coords({time_dim_name: HOURS_UTC_3X})

    time_shift = MODEL_TIME_SHIFT if is_model else 0.0
    
    output_data = np.empty(
        (len(HOURS_LOCAL), len(original_lats), len(original_lons)), 
        dtype=np.float32
    )

    for i, lon_val in enumerate(original_lons.values):
        
        t_shift_values = HOURS_LOCAL - (TSPD * lon_val / 360.0 + time_shift)
        data_at_lon = da_3dc.sel(lon=lon_val) 
        
        interp_data = data_at_lon.interp(
            {time_dim_name: t_shift_values}, 
            kwargs={"fill_value": "extrapolate"}
        )
        
        interp_data = interp_data.assign_coords(
            {time_dim_name: HOURS_LOCAL}
        ).rename({time_dim_name: 'hour_local'})
        
        output_data[:, :, i] = interp_data.transpose('hour_local', 'lat').values
        
    da_adc = xr.DataArray(
        output_data,
        coords={
            'hour_local': HOURS_LOCAL,
            'lat': original_lats,
            'lon': original_lons
        },
        dims=['hour_local', 'lat', 'lon']
    )
    
    logger.info(f"    ...coords after robust rebuild: {da_adc.coords}")
    
    return da_adc


def process_model_data(ds, var_name, time_slice):
    """
    Reads, converts, and calculates seasonal diurnal cycles for model data
    ONLY for the specified time_slice.
    """
    logger.info("Processing model data...")
    
    logger.info(f"  - Filtering model data to time slice: {time_slice.start} to {time_slice.stop}")
    ds_filtered = ds.sel(time=time_slice)

    logger.info("  - Converting model longitude grid from -180/180 to 0/360...")
    ds_filtered.coords['lon'] = np.mod(ds_filtered['lon'], 360)
    ds_filtered = ds_filtered.sortby('lon')
    
    da = ds_filtered[var_name] * 86400.0
    
    logger.info("  Calculating seasonal-hourly composites...")
    
    seasonal_hourly_clim = da.groupby('time.season').map(
        lambda seasonal_group: seasonal_group.groupby(seasonal_group.time.dt.hour).mean(dim='time')
    )
    
    all_seasons_we_care_about = ['JJA', 'DJF']
    seasonal_hourly_clim = seasonal_hourly_clim.reindex(
        {"season": all_seasons_we_care_about}
    )

    model_jja_grouped = seasonal_hourly_clim.sel(season='JJA')
    model_djf_grouped = seasonal_hourly_clim.sel(season='DJF')
    
    logger.info("  Interpolating model data to hourly...")
    model_jja_hourly = model_jja_grouped.interp(
        hour=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"}
    ).rename({'hour': 'time'}) # Rename coord to 'time'
    
    model_djf_hourly = model_djf_grouped.interp(
        hour=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"}
    ).rename({'hour': 'time'}) # Rename coord to 'time'
    
    model_jja_adc = correct_to_local_time(model_jja_hourly, is_model=True)
    model_djf_adc = correct_to_local_time(model_djf_hourly, is_model=True)
    
    return model_jja_adc, model_djf_adc


def process_trmm_data(obs_path):
    """Reads and interpolates seasonal TRMM data."""
    logger.info("Processing TRMM data...")
    
    trmm_jja_file = os.path.join(obs_path, "TRMM_JJA.nc")
    trmm_djf_file = os.path.join(obs_path, "TRMM_DJF.nc")

    if not os.path.exists(trmm_jja_file):
        logger.warning(f"Warning: TRMM_JJA.nc not found in {obs_path}. JJA plot will be empty.")
        ds_jja = None
    else:
        ds_jja = xr.open_dataset(trmm_jja_file)
        # Convert from mm/hr (file unit) to mm/day (plot unit)
        ds_jja['precip'] = ds_jja['precip'] * 24.0
        
    if not os.path.exists(trmm_djf_file):
        logger.warning(f"Warning: TRMM_DJF.nc not found in {obs_path}. DJF plot will be empty.")
        ds_djf = None
    else:
        ds_djf = xr.open_dataset(trmm_djf_file)
        # Convert from mm/hr (file unit) to mm/day (plot unit)
        ds_djf['precip'] = ds_djf['precip'] * 24.0

    # Process JJA if it exists
    if ds_jja is not None:
        logger.info("  Interpolating TRMM JJA to hourly...")
        trmm_jja_hourly = ds_jja['precip'].interp(
            time=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"}
        )
        trmm_jja_adc = correct_to_local_time(trmm_jja_hourly, is_model=False)
    else:
        trmm_jja_adc = None 

    # Process DJF if it exists
    if ds_djf is not None:
        logger.info("  Interpolating TRMM DJF to hourly...")
        trmm_djf_hourly = ds_djf['precip'].interp(
            time=HOURS_UTC_24, kwargs={"fill_value": "extrapolate"}
        )
        trmm_djf_adc = correct_to_local_time(trmm_djf_hourly, is_model=False)
    else:
        trmm_djf_adc = None 
    
    return trmm_jja_adc, trmm_djf_adc


# ---
# <<< --- THIS FUNCTION IS MODIFIED --- >>>
# ---
def create_plot(
    model_data, trmm_data, model_gw, trmm_gw, season_name, 
    config_dict 
):
    """
    Generates the 3x2 panel plot for a given season.
    """
    logger.info(f"Creating {season_name} plot...")
    
    # Remove constrained_layout to use manual adjustments
    fig, axes = plt.subplots(
        3, 2, 
        figsize=(12, 15) 
    )
    axes_flat = axes.flatten()
    
    for i, region in enumerate(REGIONS):
        if i >= len(axes_flat):
            break 
            
        ax = axes_flat[i]
        region_slice = dict(
            lat=slice(region['south'], region['north']),
            lon=slice(region['west'], region['east'])
        )
        
        # 1D slice for the latitude-only weights
        lat_slice = dict(lat=region_slice['lat'])

        # Model
        try:
            model_slice = model_data.sel(region_slice)
            model_weights = model_gw.sel(lat_slice)
            model_region_mean = model_slice.weighted(model_weights).mean(
                dim=['lat', 'lon']
            )
        except Exception as e:
            logger.warning(f"Warning: Could not process model region {region['title']}. Error: {e}")
            model_region_mean = None

        # TRMM
        try:
            if trmm_data is None or trmm_gw is None:
                trmm_region_mean = None
            else:
                trmm_slice = trmm_data.sel(region_slice)
                trmm_weights = trmm_gw.sel(lat_slice)
                trmm_region_mean = trmm_slice.weighted(trmm_weights).mean(
                    dim=['lat', 'lon']
                )
        except Exception as e:
            logger.warning(f"Warning: Could not process TRMM region {region['title']}. Error: {e}")
            trmm_region_mean = None

        # Plot the time series
        if model_region_mean is not None and not np.isnan(model_region_mean).all():
            model_label = "SPEAR-MED"
            model_region_mean.plot(
                ax=ax, label=model_label, color='red', lw=2
            )
        if trmm_region_mean is not None and not np.isnan(trmm_region_mean).all():
            obs_label = "IMERG"
            trmm_region_mean.plot(
                ax=ax, label=obs_label, color='black', lw=2
            )
        
        # --- FONT SIZE INCREASED ---
        ax.set_title(region['title'], fontsize=14) 
        
        # --- COMMON LABEL FIX: Remove individual labels ---
        ax.set_xlabel("")
        ax.set_ylabel("")
        
        ax.set_ylim(PLOT_RANGE)
        ax.set_xticks(np.arange(0, 25, 4))
        # --- FONT SIZE INCREASED ---
        ax.tick_params(axis='both', which='major', labelsize=12) 
        ax.grid(True, linestyle='--', alpha=0.6)

    # ---
    # <<< --- NEW: ADD COMMON LABELS, LEGEND, AND LAYOUT FIX --- >>>
    # ---
    
    # 1. Add common X and Y labels with larger fonts
    #    Use 'y' and 'x' to manually position them
    fig.supxlabel("Local Hour", fontsize=20, y=0.07) 
    fig.supylabel("Precipitation (mm/day)", fontsize=20, x=0.03)

    # 2. Get handles and labels for the legend
    handles, labels = [], []
    for ax in axes_flat:
        h, l = ax.get_legend_handles_labels()
        if h: 
            handles, labels = h, l
            break
    
    # 3. Create a common legend, make it bigger, and move it down
    if handles:
        fig.legend(handles, labels, 
                   loc='lower center', 
                   # Place legend 2% from the bottom (y=0.02)
                   bbox_to_anchor=(0.5, 0.01), 
                   ncol=2, 
                   fontsize=25) # <<< FONT SIZE INCREASED

    # 4. Set the fixed title with a larger font
    year = config_dict.get('startdate', '2015')
    if season_name == "JJA":
        title = f"SPEAR-MED/IMERG Diurnal Cycle Comparison - JJA {year}"
    elif season_name == "DJF":
        title = f"SPEAR-MED/IMERG Diurnal Cycle Comparison - DJF {year}"
    else:
        # Fallback to old logic just in case
        casename = config_dict.get('casename', 'model')
        title = f"{year} {season_name} Diurnal Cycle - {casename}"
        
    fig.suptitle(title, fontsize=24) # <<< FONT SIZE INCREASED
    
    # 5. Manually adjust subplot spacing to prevent cutoff
    #    bottom=0.12 : Increase bottom margin to 12% to make room
    #    right=0.95  : Keep 5% margin on the right
    plt.subplots_adjust(left=0.1, right=0.95, bottom=0.12, top=0.92, wspace=0.2, hspace=0.3)
    
    # ---
    # <<< --- END OF MODIFICATIONS --- >>>
    # ---
    
    output_dir = os.path.join(config_dict.get('work_dir', '.'), "model", "PS")
    plot_filename = f"pr_{season_name}_dc_regions.png"
    output_path = os.path.join(output_dir, plot_filename)
    plt.savefig(output_path, dpi=600)
    logger.info(f"Plot saved to {output_path}")
    plt.close(fig)

# ---------------------------------------------------------------
# 4. CONFIG LOADING FUNCTION
# ---------------------------------------------------------------
def load_config(config_path):
    """Loads the YAML config file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"Successfully loaded config from {config_path}")
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

# ---------------------------------------------------------------
# 5. MAIN FUNCTION
# ---------------------------------------------------------------
def main():
    """
    Main driver function to orchestrate the analysis.
    """
    parser = argparse.ArgumentParser(
        description="Run diurnal cycle comparison from a config file."
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help="Path to the .yaml configuration file."
    )
    args = parser.parse_args()

    config = load_config(args.config)
    
    setup_logging(config.get('work_dir', '.'))

    start_main = time.time()
    try:
        # --- Get settings from config dictionary ---
        PR_FILE = config.get('pr_file')
        OBS_DATA = config.get('processed_satellite_dir') # Use the unified key
        pr_var = config.get('pr_var', 'precip')
        
        try:
            start_date = config['analysis_period']['start']
            end_date = config['analysis_period']['end']
            time_slice = slice(start_date, end_date)
            logger.info(f"Analysis period set: {start_date} to {end_date}")
        except KeyError:
            logger.error("Error: 'analysis_period: {start: ... , end: ...}' not found in config file.")
            return

        # --- Check for required inputs ---
        if not PR_FILE or not os.path.exists(PR_FILE):
            logger.error(f"Error: Model file not found at PR_FILE={PR_FILE}")
            return
        if not OBS_DATA or not os.path.exists(OBS_DATA): 
            logger.error(f"Error: 'processed_satellite_dir' directory not found at {OBS_DATA}")
            return

        # --- Run Main Processing Steps ---
        logger.info(f"Loading model file: {PR_FILE}")
        
        try:
            time_coder = xr.coding.times.CFDatetimeCoder(use_cftime=True)
            ds_model = xr.open_dataset(
                PR_FILE, 
                decode_times=time_coder, 
                decode_timedelta=False 
            )
        except Exception as e:
            logger.error(f"Failed to open model file with cftime coder: {e}")
            return

        model_gw = get_latitude_weights(ds_model.lat)
        
        model_jja_adc, model_djf_adc = process_model_data(ds_model, pr_var, time_slice)
        
        trmm_jja_adc, trmm_djf_adc = process_trmm_data(OBS_DATA)
        
        # Get weights from whichever TRMM file is available
        if trmm_jja_adc is not None:
             trmm_gw = get_latitude_weights(trmm_jja_adc.lat)
        elif trmm_djf_adc is not None: 
             trmm_gw = get_latitude_weights(trmm_djf_adc.lat)
        else:
             logger.warning("No TRMM data at all. Weights will be missing.")
             trmm_gw = None 
        
        # --- Create Plots ---
        create_plot(
            model_jja_adc, trmm_jja_adc, model_gw, trmm_gw,
            "JJA", config
        )
        create_plot(
            model_djf_adc, trmm_djf_adc, model_gw, trmm_gw, 
            "DJF", config
        )

        logger.info(f"Python script finished successfully in {time.time() - start_main:.2f} seconds.")

    except Exception as e:
        logger.error("A fatal error occurred in main()!", exc_info=True)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    main()