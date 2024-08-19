import numpy as np
import pandas as pd
import xarray as xr
import sys
import glob
import os
import time 
import xesmf as xe
import scipy
from scipy import stats
import yaml
import sys
import matplotlib.pyplot as plt

from WWE_diag_tools import (
    land_mask_using_etopo,
    regridder_model2obs,
    nharm,
    calc_raw_and_smth_annual_cycle,
    isolate_WWEs,
    WWE_characteristics,
    WWE_statistics, #We don't need to do the statistics to make the likelihood by longitude plot
    find_WWE_time_lon)

def plot_model_Hovmollers_by_year(data = None, tauu_time = None):
    
    year_array = np.unique(tauu_time.dt.year)
    nyears     = np.unique(tauu_time.dt.year).size

    fig, ax = plt.subplots(ncols=5, nrows=4, figsize = (15, 16), sharex = True, sharey = True) 
    axlist = ax.flatten()
    shade_choice     = 'ColdHot'
    levs             = np.linspace(-0.1, 0.1, 21)

    kwargs = {'fontsize':12}
    ####################################################################################
    #Loop through each year to make a Hovmoller panel of filtered zonal wind stress
    #for each year overlapped with WWE blobs
    ####################################################################################
    for iyear in range(20):
        wiyear = np.where((np.asarray(tauu_time.dt.year) == year_array[iyear]))
        
        ########################################################################           
        #Plot details
        ########################################################################=
        cf = axlist[iyear].contourf(np.asarray(data.lon), np.arange(0, tauu_time[wiyear[0]].size),
                                    np.asarray(data[wiyear[0], :]), levels = levs, 
                                    cmap = shade_choice, extend = 'both')

        cl = axlist[iyear].contour(np.asarray(data.lon), np.arange(0, tauu_time[wiyear[0]].size),  
                                   wwe_mask[wiyear[0], :], cmap = 'binary', linewidths = 1)
        
        if iyear >=15 :axlist[iyear].set_xlabel('longitude', **kwargs)
        if iyear%5 == 0: axlist[iyear].set_ylabel('day of year', **kwargs)
        axlist[iyear].set_title(str(year_array[iyear]), fontsize=12, loc = 'left')
        axlist[iyear].tick_params(axis='y', labelsize=12)
        axlist[iyear].tick_params(axis='x', labelsize=12)
        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)

    cbar_ax = fig.add_axes([0.81, 0.35, 0.015, 0.3])
    cbar_ax.tick_params(labelsize=12)
    cb = plt.colorbar(cf, cax=cbar_ax)
    cb.set_label(label = '$\u03C4_x$ (N $m^{-2}$)', fontsize = 12)
    plt.savefig('test_Hovmoller.png', bbox_inches='tight')

    return cf

'''
obs_folder_name = '120dayHPfilter_static0p04TauxThresh/'
obs_dir = '/Users/eriley/Desktop/my-notebook/NOAA_MDTF/netcdf_files/WWE_characteristics/' + obs_folder_name
  
obs_ds          = xr.open_mfdataset(obs_dir + 'taux.*')
obs_data        = obs_ds["filtered_taux"]
obs_time        = obs_ds["time"]
obs_wwe_labels  = obs_ds["wwe_labels"]
wwe_mask        = np.where(obs_wwe_labels > 0, 1, 0)
center_lon_vals = obs_ds["wwe_lons"]
center_time_vals= obs_ds["wwe_times"]
obs_lon_vals    = np.asarray(obs_ds["lon"])

year_array      = np.unique(obs_time.dt.year)


plot_model_Hovmollers_by_year(data = obs_data, tauu_time = obs_time)
'''

print("\n=======================================")
print("BEGIN ID_WWEs.py ")
print("=======================================")

# Parse MDTF-set environment variables
print("*** Parse MDTF-set environment variables ...")
#*************************************************************************************
#***Ι DON'T KNOW WHERE THESE GET SET, A CONFIG FILE? THE CASE_INFO.YML FILE?******
#**** I think a lot of these variables end up coming from the case_env_file that the framework creates
#the case_env_file points to the csv file, which in turn points to the data files. Variables from the data files
#are then read in. See example_multicase.py

CASENAME = os.environ["CASENAME"]
STARTDATE= os.environ["startdate"]
ENDDATE  = os.environ["enddate"]
WK_DIR   = os.environ["WORK_DIR"]
OBS_DATA = os.environ["OBS_DATA"]

# Input and output files/directories
#MODEL FILES (I think these files go in the csv file, which is referred to in the CATALOG_FILE (i.e., a .json file) and CASE_ENVI_FILE)
#Model zonal wind stress (tauu) file
tauu_file     = os.environ["TAUU_FILE"] #'/Users/eriley/NOAA_POD/model_data/'+dir_name[imodel]+'/tauu/tauu*1.nc'

#Model Land fraction file
lf_dir     = os.environ["LANDFRAC_DIR"] #'/Users/eriley/NOAA_POD/model_data/sftlf_historical/'
lf_file    = lf_dir + 'sftlf_fx_'+dir_name[imodel]+'_historical_*.nc'

#OBSERVATION FILES:
#Observed topography
topo_file     = os.environ["TOPO_FILE"] #'/Users/eriley/etopo2.nc'

#file with lat-lon grid info for observations
obs_grid_file = os.environ["TROPFLX_GRID_FILE"] #'/Users/eriley/NOAA_POD/obs_data/TropFlux_10m_windspeed/ws_tropflux_1d_2018.nc'
    
data_dir      = f"{WK_DIR}/model/netCDF"
plot_dir      = f"{WK_DIR}/model/PS/"
obs_plot_dir  = f"{WK_DIR}/obs/PS/"
#*************************************************************************************
#Where are these written in the new framework using the intake catalog instead of the settings file?
# Parse POD-specific environment variables
print("*** Parsing POD-specific environment variables")
regrid_method_type = os.environ["REGRID_METHOD"]                             
obs_firstyr        = int(os.environ["OBS_FIRSTYR"])
obs_lastyr         = int(os.environ["OBS_LASTYR"])
min_lon            = float(os.environ["min_lon"])
max_lon            = float(os.environ["max_lon"])
min_lat            = float(os.environ["min_lat"])
max_lat            = float(os.environ["max_lat"])
anom_method        = os.environ["ANOM_METHOD"]
do_bp_filter       = True if anom_method == 'bandpass' else False
do_hp_filter       = True if anom_method == 'highpass' else False
do_anom            = True if anom_method == 'dailyanom' else False
 
static_thresh = bool(int(os.environ["STATIC_THRESH"]))
LP_cutoff     = 5   #removes signals shorter than this many days
HP_cutoff     = 120 #removes singlas longer than this many days
sigma_factor  = int(os.environ["SIGMA_FACTOR"])
if do_hp_filter is True:
    filter_descrip= str(HP_cutoff)+' HP filter for $\u03C4_x$ ' + str(min_lat) + ' - ' + str(max_lat)

if do_bp_filter is True:
    filter_descrip= str(LP_cutoff)+ '-' + str(HP_cutoff) +' BP filter for $\u03C4_x$ ' + str(min_lat) + ' - ' + str(max_lat) 

if do_anom is True:
    filter_descrip = 'Annual cycle romoved for $\u03C4_x$ ' + str(min_lat) + ' - ' + str(max_lat)

#Note these thresh_values are the static values used for 1sigma
#and 2sigma of the observations
if sigma_factor == 1:
    thresh_val = '02' 
    tauu_thresh2use = 0.02 
    
if sigma_factor == 2:
    thresh_val = '04' 
    tauu_thresh2use = 0.04

#Input and output files/directories
#Open the topography file
'''
topo_ds               = xr.open_dataset(topo_file)
topo_ds.coords['lon'] = (topo_ds.coords['lon'] + 360) % 360
topo_ds               = topo_ds.sortby(topo_ds.lon)
trop_topo_ds          = topo_ds.sel(lat = slice(lat_bnds[1], lat_bnds[0]))
trop_topo_longrid, trop_topo_latgrid = np.meshgrid(trop_topo_ds.lon, trop_topo_ds.lat)
topo_longrid_1D       = trop_topo_longrid.reshape(trop_topo_ds.lon.size * trop_topo_ds.lat.size)
topo_latgrid_1D       = trop_topo_latgrid.reshape(trop_topo_ds.lon.size * trop_topo_ds.lat.size)
topo_data1D           = trop_topo_ds['btdata'].values.reshape(trop_topo_ds.lon.size * trop_topo_ds.lat.size)

#Open TropFlux wind speed file, so we have the TropFlux lat-lon information for regridding purposes 
obs_grid_ds   = xr.open_dataset(obs_grid_file)
obs_grid_ds   = obs_grid_ds.pad(longitude = 5).roll(longitude = 25, roll_coords = True)
obs_grid_ds   = obs_grid_ds.assign_coords(longitude = np.arange(0.5, 360.5))
obs_grid_ds   = obs_grid_ds.rename({'longitude': 'lon', 'latitude': 'lat'})
'''
    
#Define lats to average tauu over and lon range to analyze
lat_lim = [min_lat, max_lat]
lon_lim = [min_lon, max_lon]

firstyr = int(STARTEDATE[0:4])
lastyr  = int(ENDDATE[0:4])

#When opening model output and preprocessing, only open latitude band that is slightly larger
#than observation data set (i.e., TropFlux)
lon_bnds, lat_bnds = (0, 360), (-32.5, 32.5)
partial_func       = partial(_preprocess, lon_bnds=lon_bnds, lat_bnds=lat_bnds)

#Get zonal wind stress variable
model_ds = xr.open_mfdataset(tauu_file, preprocess=partial_func)

