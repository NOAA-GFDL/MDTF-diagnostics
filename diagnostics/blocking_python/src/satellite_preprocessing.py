#!/usr/bin/env python

"""
Pre-processes raw GPM IMERG 3B-HHR (half-hourly) HDF5 files into
the 3-hourly, seasonal climatology files (TRMM_JJA.nc, TRMM_DJF.nc).

This is a memory-efficient version that uses Dask to process
the data in chunks and correctly handles non-standard calendars.
"""

import xarray as xr
import numpy as np
import pandas as pd
import os
import glob
import sys
import time
import logging
import yaml
import argparse

try:
    from dask.distributed import Client, LocalCluster
except ImportError:
    print("CRITICAL: 'dask' and 'distributed' libraries not found. pip install dask distributed")
    sys.exit(1)

# --- USER: SET THESE PATHS & CONFIGS IN YOUR YAML ---
# These are defaults if not in config.yaml
INPUT_DIR = "/work/s1b/dc_pod/data/"
OUTPUT_DIR = "/work/s1b/dc_pod/output/"
N_CORES = 4
MEMORY_PER_WORKER = '16GB'
# --- END OF DEFAULTS ---

# ---------------------------------------------------------------
# 1. LOGGER SETUP
# ---------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

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

def preprocess_satellite_data(config):
    """Main preprocessing function."""
    
    start_script = time.time()
    
    # --- 1. Get Settings ---
    try:
        input_dir = config['raw_satellite_dir']
        output_dir = config['processed_satellite_dir']
        start_date_str = config['analysis_period']['start']
        end_date_str = config['analysis_period']['end']
        time_slice = slice(start_date_str, end_date_str)
        
        n_cores = config.get('n_cores', N_CORES)
        mem_limit = config.get('memory_per_worker', MEMORY_PER_WORKER)

    except KeyError as e:
        logger.error(f"Error: Missing key {e} in config.yaml.")
        return

    # --- 2. Setup File Logger ---
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "preprocessing.log")
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Starting satellite data preprocessing (Memory-Efficient Dask Version).")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Analysis Period: {start_date_str} to {end_date_str}")
    
    cluster = None
    client = None
    
    try:
        # --- 3. Find Files ---
        logger.info("Step 1: Finding files...")
        step_start = time.time()
        search_path = os.path.join(input_dir, "**", "*.HDF5")
        input_files = sorted(glob.glob(search_path, recursive=True))
        if not input_files:
            logger.error(f"Error: No .HDF5 files found in {input_dir}")
            return
        logger.info(f"Found {len(input_files)} files to process.")
        logger.info(f"Step 1 finished in {time.time() - step_start:.2f} seconds.\n")

        # --- 4. Setup Dask Cluster ---
        logger.info(f"Step 2: Setting up Dask LocalCluster with {n_cores} workers...")
        step_start = time.time()
        cluster = LocalCluster(n_workers=n_cores, threads_per_worker=1, memory_limit=mem_limit)
        client = Client(cluster)
        logger.info(f"Dask cluster running. Dashboard link: {client.dashboard_link}")
        logger.info(f"Step 2 finished in {time.time() - step_start:.2f} seconds.\n")

        # --- 5. Build Lazy Computation Graph ---
        logger.info("Step 3: Building lazy computation graph (no data loaded yet)...")
        step_start = time.time()
        
        try:
            logger.info("  - Opening all files with xarray.open_mfdataset (decode_times=False)...")
            ds = xr.open_mfdataset(
                input_files,
                engine="h5netcdf",
                group="Grid",
                combine="by_coords",
                data_vars=['precipitation'],
                parallel=True,
                decode_times=False,  # <<< --- THIS IS THE TRICK (Part 1)
                decode_timedelta=False
            )
            logger.info("  - Files opened (lazily).")
            
            # ---
            # <<< --- THIS IS THE CALENDAR FIX (Part 2) --- >>>
            # ---
            # 1. Load *only* the time coordinate (fast)
            logger.info("  - Manually decoding time coordinate to fix 'julian' calendar...")
            time_values = ds.time.values
            
            # 2. Manually convert 'seconds since 1980-01-06' to a standard datetime
            #    This is the key to fixing the .dt.season bug
            time_origin = '1980-01-06 00:00:00'
            times_as_datetime = pd.to_datetime(time_values, unit='s', origin=time_origin)
            
            # 3. Assign this corrected, in-memory array back to the lazy dataset
            ds['time'] = times_as_datetime
            logger.info("  - Time coordinate successfully replaced.")
            # ---
            # <<< --- END OF FIX --- >>>
            # ---

        except Exception as e:
            logger.error("Error: Failed to open HDF5 files.")
            logger.error(f"  Details: {e}")
            return
            
        logger.info(f"  - Filtering raw data to time slice: {start_date_str} to {end_date_str}")
        ds = ds.sel(time=time_slice)
            
        logger.info("  - Renaming variable 'precipitation' to 'precip'...")
        ds = ds.rename({'precipitation': 'precip'})

        logger.info("  - Converting longitude grid from -180/180 to 0/360...")
        ds.coords['lon'] = np.mod(ds['lon'], 360)
        ds = ds.sortby('lon')
        
        logger.info("  - Building lazy 3-hourly resample plan...")
        ds_3hr = ds.resample(time='3H').mean()
        
        logger.info("  - Building lazy seasonal-hourly climatology graph...")
        seasonal_clim = ds_3hr.groupby('time.season').map(
            lambda seasonal_group: seasonal_group.groupby(seasonal_group.time.dt.hour).mean(dim='time')
        )
        
        all_seasons = ['DJF', 'JJA', 'MAM', 'SON']
        seasonal_clim = seasonal_clim.reindex({"season": all_seasons})
        
        jja_clim = seasonal_clim.sel(season='JJA').rename({'hour': 'time'})
        djf_clim = seasonal_clim.sel(season='DJF').rename({'hour': 'time'})
        
        logger.info(f"Step 3 (Graph Building) finished in {time.time() - step_start:.2f} seconds.\n")

        # --- 6. Execute Computations and Save Files ---
        logger.info("Step 4: Executing Dask computations and saving files...")
        step_start = time.time()
        
        output_jja_path = os.path.join(output_dir, "TRMM_JJA.nc")
        output_djf_path = os.path.join(output_dir, "TRMM_DJF.nc")

        logger.info(f"  - Executing JJA chain and saving to: {output_jja_path}")
        jja_clim.to_netcdf(output_jja_path)
        logger.info("  - JJA file saved.")

        logger.info(f"  - Executing DJF chain and saving to: {output_djf_path}")
        djf_clim.to_netcdf(output_djf_path)
        logger.info("  - DJF file saved.")
        
        logger.info(f"Step 4 (Execution) finished in {time.time() - step_start:.2f} seconds.\n")
        logger.info("Preprocessing finished successfully!")

    except Exception as e:
        logger.error("A fatal error occurred!", exc_info=True)
    finally:
        logger.info("Step 5: Shutting down Dask cluster...")
        if client: client.close()
        if cluster: cluster.close()
        logger.info("Dask cluster shut down.")
        logger.info(f"Total time: {time.time() - start_script:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-process raw satellite data.")
    parser.add_argument('-c', '--config', type=str, required=True, help="Path to the .yaml configuration file.")
    args = parser.parse_args()
    config = load_config(args.config)

    if 'raw_satellite_dir' not in config or 'processed_satellite_dir' not in config:
        print("Error: config.yaml must contain 'raw_satellite_dir' and 'processed_satellite_dir' paths.")
        sys.exit(1)

    try:
        import h5netcdf
    except ImportError:
        logger.critical("CRITICAL: 'h5netcdf' library not found. pip install h5netcdf")
        sys.exit(1)
        
    preprocess_satellite_data(config)