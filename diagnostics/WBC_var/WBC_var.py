import os
import yaml
import xarray as xr
import warnings
import numpy as np
import pandas as pd #
import matplotlib.pyplot as plt

# Custom modules
from postprocessing import preprocess_data, normalize_metadata_global
from calculate_index import gs_index, gsp_index, EOF_index, region_define
from draw_figure import FIG1, FIG2, FIG3

warnings.simplefilter("ignore")

# =============================================================================
# 1. Setup & Config
# =============================================================================
#obs_dir = '/glade/work/jshin/mdtf/inputdata/obs_data/WBC_var/'
work_dir = os.environ.get("WORK_DIR", "./")
obs_dir = os.environ.get("OBS_DATA_ROOT", "./")
print(f"Work Dir: {work_dir}")
print(f"Obs Root: {obs_dir}")

print("reading case_info")
os.environ["case_env_file"] = os.path.join(work_dir, "case_info.yml")
case_env_file = os.environ["case_env_file"]

print(case_env_file)
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

save_dir = os.path.join(work_dir, 'obs/')
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# =============================================================================
# 2. Load Global Raw Data (Loading)
# =============================================================================

# --- 2.1 Load Observation (Global Raw) ---
print("\n[Step 1] Opening Observation Data (Lazy)...")
obs_filename = "cmems_obs.1993-01-01-2022-12-31_r360x180.nc"
obs_path = os.path.join(obs_dir, obs_filename)
ds_obs_global = None

if os.path.exists(obs_path):
    ds_raw = xr.open_dataset(obs_path, chunks={'time': 12})
    ds_obs_global = normalize_metadata_global(ds_raw, target_var='zos')
    print("  -> Observation opened successfully.")
else:
    print(f"  -> Error: Obs file not found at {obs_path}")

# --- 2.2 Load Models (Direct Load from case_info) ---
print("\n[Step 2] Opening Model Data directly from CASE_LIST...")
data_model_global = {} 
zos_var_model = 'zos'

if os.path.isfile(case_env_file):
    with open(case_env_file, 'r') as stream:
        case_info = yaml.safe_load(stream)

    case_list = case_info.get('CASE_LIST', {})
    if case_list:
        first_key = list(case_list.keys())[0]
        zos_var_model = case_list[first_key].get('zos_var', 'zos')

    for case_name, case_attrs in case_list.items():
        if "Obs" in case_name or "cmems" in case_name:
            continue

        filepath = case_attrs.get('ZOS_FILE')
        if not filepath or not os.path.exists(filepath):
            print(f"  -> Warning: File not found for {case_name}")
            continue

        print(f"  -> Processing Model: {case_name}")
        print(f"     File: {os.path.basename(filepath)}")

        try:
            # [중요] use_cftime=True 필수
            ds_mod = xr.open_dataset(filepath, chunks={'time': 12}, use_cftime=True)
            ds_mod = normalize_metadata_global(ds_mod, target_var=zos_var_model)
            data_model_global[case_name] = ds_mod

        except Exception as e:
            print(f"  -> Error loading {case_name}: {e}")

if ds_obs_global is None and len(data_model_global) > 0:
    print("  -> Warning: Using first model as Observation substitute.")
    key0 = list(data_model_global.keys())[0]
    ds_obs_global = data_model_global.pop(key0)

# =============================================================================
# 3. Main Analysis Loop
# =============================================================================
#REGION = ["gulf", "kuroshio", "australia", "agulhas", "brazil"]
REGION = ["gulf"] 
#REGION = ["kuroshio"]
#REGION = ["australia"]
#REGION = ["agulhas"]
#REGION = ["brazil"]
print(f"\n[Step 3] Starting Region Loop: {REGION}")

for region in REGION:
    print(f"\n==================================================")
    print(f" Processing Region: {region}")
    print(f"==================================================")

    bounds = region_define(region)

    # -------------------------------------------------------------------------
    # 3.1 Observation
    # -------------------------------------------------------------------------
    print("  -> Processing Observation...")
    ds_obs_slice = ds_obs_global.sel(lon=bounds["lon"], lat=bounds["lat"])
    #ds_obs_slice = ds_obs_slice.sel(time=slice('1993-01-01', '2020-12-31'))

    ds_obs_reg = preprocess_data(ds_obs_slice, target_var='zos')
    ds_obs_reg = ds_obs_reg.load()

    if 'msl' not in ds_obs_reg:
        ds_obs_reg['msl'] = ds_obs_reg['zos'].mean(dim='time', skipna=True)
    if 'sla_std' not in ds_obs_reg:
        ds_obs_reg['sla_std'] = ds_obs_reg['sla'].std(dim='time', skipna=True)

    gs_index(ds_obs_reg, region)
    gsp_index(ds_obs_reg, region)
    EOF_index(ds_obs_reg, region)

    # -------------------------------------------------------------------------
    # 3.2 Models
    # -------------------------------------------------------------------------
    print("  -> Processing Models...")
    model_datasets_reg = {} 

    for model_name, ds_mod_global in data_model_global.items():
        ds_mod_slice = ds_mod_global.sel(lon=bounds["lon"], lat=bounds["lat"])
        #ds_mod_slice = ds_mod_slice.sel(time=slice('1950-01-01', '2020-12-31'))

        ds_mod_reg = preprocess_data(ds_mod_slice, target_var=zos_var_model)
        ds_mod_reg = ds_mod_reg.load()

        if 'msl' not in ds_mod_reg:
            ds_mod_reg['msl'] = ds_mod_reg[zos_var_model].mean(dim='time', skipna=True)
        if 'sla_std' not in ds_mod_reg:
            ds_mod_reg['sla_std'] = ds_mod_reg['sla'].std(dim='time', skipna=True)

        gs_index(ds_mod_reg, region)
        gsp_index(ds_mod_reg, region)
        EOF_index(ds_mod_reg, region)

        model_datasets_reg[model_name] = ds_mod_reg
        #print(ds_mod_reg)
    # -------------------------------------------------------------------------
    # 3.3 Plotting
    # -------------------------------------------------------------------------
    print(f"  -> Generating Figures for {region}...")
    try:
        FIG1(ds_obs_reg, model_datasets_reg, save_path=save_dir, save_name=region)
        FIG2(ds_obs_reg, model_datasets_reg, save_path=save_dir, save_name=region)
        FIG3(ds_obs_reg, model_datasets_reg, save_path=save_dir, save_name=region) 
    except Exception as e:
        print(f"Error plotting {region}: {e}")
        import traceback
        traceback.print_exc()

print("\nAll Regions Completed.")



