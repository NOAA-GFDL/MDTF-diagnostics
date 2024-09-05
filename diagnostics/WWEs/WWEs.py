import matplotlib
matplotlib.use("Agg")  # non-X windows backend

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import glob
import os
import time 
import xesmf as xe
import scipy
from scipy import stats
from functools import partial
import intake
import sys
import yaml

from WWE_diag_tools import (
    land_mask_using_etopo,
    regridder_model2obs,
    nharm,
    calc_raw_and_smth_annual_cycle,
    isolate_WWEs,
    WWE_characteristics,
    WWE_statistics, #We don't need to do the statistics to make the likelihood by longitude plot
    find_WWE_time_lon,
    plot_model_Hovmollers_by_year)

print("\n=======================================")
print("BEGIN WWEs.py ")
print("=======================================")

def _preprocess(x, lon_bnds, lat_bnds):
    return x.sel(lon=slice(*lon_bnds), lat=slice(*lat_bnds))

work_dir  = os.environ["WORK_DIR"]
obs_dir   = os.environ["OBS_DATA"]
casename  = os.environ["CASENAME"]
first_year= os.environ["first_yr"]
last_year = os.environ["last_yr"]

###########################################################################
##############Part 1: Get, Plot Observations ##############################
###########################################################################
print(f'*** Now working on obs data\n------------------------------')
obs_file_WWEs = obs_dir + '/TropFlux_120-dayHPfiltered_tauu_1980-2014.nc'

print(f'*** Reading obs data from {obs_file_WWEs}')
obs_WWEs    = xr.open_dataset(obs_file_WWEs)
print(obs_WWEs, 'obs_WWEs')

# Subset the data for the user defined first and last years #
obs_WWEs = obs_WWEs.sel(time=slice(first_year, last_year))

obs_lons = obs_WWEs.lon
obs_lats = obs_WWEs.lat
obs_time = obs_WWEs.time
Pac_lons = obs_WWEs.Pac_lon
obs_WWE_mask        = obs_WWEs.WWE_mask
TropFlux_filt_tauu  = obs_WWEs.filtered_tauu
TropFlux_WWEsperlon = obs_WWEs.WWEs_per_lon

plot_model_Hovmollers_by_year(data = TropFlux_filt_tauu, wwe_mask = obs_WWE_mask,
                                  lon_vals = Pac_lons, tauu_time = obs_time,
                                  savename = f"{work_dir}/obs/PS/TropFlux_",
                                  first_year = first_year, last_year = last_year)

###########################################################################
###########Parse MDTF-set environment variables############################
###########################################################################
#These variables come from the case_env_file that the framework creates
#the case_env_file points to the csv file, which in turn points to the data files.
#Variables from the data files are then read in. See example_multicase.py
print("*** Parse MDTF-set environment variables ...")

case_env_file = os.environ["case_env_file"]
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

cat_def_file = case_info['CATALOG_FILE']
case_list    = case_info['CASE_LIST']
# all cases share variable names and dimension coords in this example, so just get first result for each
tauu_var   = [case['tauu_var'] for case in case_list.values()][0]
time_coord = [case['time_coord'] for case in case_list.values()][0]
lat_coord  = [case['lat_coord'] for case in case_list.values()][0]
lon_coord  = [case['lon_coord'] for case in case_list.values()][0]

# open the csv file using information provided by the catalog definition file
cat = intake.open_esm_datastore(cat_def_file)

# filter catalog by desired variable and output frequency
tauu_subset = cat.search(variable_id=tauu_var, frequency="day")

# examine assets for a specific file
#tas_subset['CMIP.synthetic.day.r1i1p1f1.day.gr.atmos.r1i1p1f1.1980-01-01-1984-12-31'].df

#Use partial function to only load part of the data file
lon_bnds, lat_bnds = (0, 360), (-32.5, 32.5)
partial_func       = partial(_preprocess, lon_bnds=lon_bnds, lat_bnds=lat_bnds)

# convert tas_subset catalog to an xarray dataset dict
tauu_dict = tauu_subset.to_dataset_dict(preprocess = partial_func,
    xarray_open_kwargs={"decode_times": True, "use_cftime": True}
)

tauu_arrays = {}
for k, v in tauu_dict.items(): 
    arr = tauu_dict[k][tauu_var]
    arr = arr.sel(lon = slice(120,280), lat = slice(-2.5, 2.5),
                      time = slice(first_year, last_year))
    arr = arr.mean(dim = (tauu_dict[k][lat_coord].name,tauu_dict[k][time_coord].name))

    tauu_arrays[k] = arr

###########################################################################
# Part 3: Make a plot that contains results from each case
# --------------------------------------------------------

# set up the figure
fig = plt.figure(figsize=(12, 4))
ax = plt.subplot(1, 1, 1)

# loop over cases
for k, v in tauu_arrays.items():
    v.plot(ax=ax, label=k)

# add legend
plt.legend()

# add title
plt.title("Mean Zonal Wind Stress")

assert os.path.isdir(f"{work_dir}/model/PS"), f'Assertion error: {work_dir}/model/PS not found'
plt.savefig(f"{work_dir}/model/PS/{casename}.Mean_TAUU.eps", bbox_inches="tight")

# Part 4: Close the catalog files and
# release variable dict reference for garbage collection
# ------------------------------------------------------
cat.close()
tauu_dict = None
# Part 5: Confirm POD executed successfully
# ----------------------------------------
print("Last log message by example_multicase POD: finished successfully!")
sys.exit(0)
