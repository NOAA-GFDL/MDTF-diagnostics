import matplotlib
matplotlib.use("Agg")  # non-X windows backend

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
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
    filter_data,
    isolate_WWEs,
    WWE_characteristics,
    find_WWE_time_lon,
    plot_model_Hovmollers_by_year,
    events_per_lon,
    plot_WWE_likelihood_per_lon)

####################################################################################
#Define some paths and functions
####################################################################################
def find_WWEs_and_characteristics(in_data = None, tauu_thresh = 0.04, mintime = 5, minlons = 10,
                                 xminmax = (3, 3), yminmax = (3, 3), minmax_dur_bins = (5, 27),
                                 dur_bin_space = 2, minmax_IWW_bins = (1, 42), IWW_bin_space = 4,
                                 xtend_past_lon = 140):
    '''
    This function call the following functions within WWE_diag_tools.py
    - isolate_WWEs
        - find_nearby_wwes_merge
        - renumber_wwes
    - WWE_chracteristics
    - find_WWE_time_lon
    '''
    
    start_time = time.time()
    
    # 1) Find WWEs
    #The isolate_WWEs function uses the find_nearby_wwes_merge, renumber_wwes functions 
    WWE_labels, WWE_mask = isolate_WWEs(data = in_data, tauu_thresh = tauu_thresh, mintime = mintime, 
                                        minlons = minlons, xmin = xminmax[0], xmax = xminmax[1], 
                                        ymin = yminmax[0], ymax = yminmax[1], xtend_past_lon = xtend_past_lon)

    # 2) Find characteristics (i.e., duration, zonal extent, integrated wind work sum and mean) of each WWE
    #Uses WWE_characteristics function
    duration, zonal_extent, IWW, tauu_mean = WWE_characteristics(wwe_labels = WWE_labels, data = in_data)
    
    # 3) Find central, min, and max time and longitude of each WWE
    #Uses find_WWE_time_lon function
    tauu_time   = in_data["time"]
    tauu_lon    = in_data["lon"]
    lon_array   = np.asarray(tauu_lon)
       
    center_lons, center_times, min_times, max_times, min_lons, max_lons \
    = find_WWE_time_lon(data = in_data, wwe_labels = WWE_labels, 
                         lon = lon_array, time_array = tauu_time)

    print("--- %s seconds to ID WWEs and compute characteristics---" % (time.time() - start_time))
    
    return duration, IWW, zonal_extent, tauu_mean, WWE_labels, WWE_mask, center_lons, \
           center_times, min_times, max_times, min_lons, max_lons, \
           lon_array, tauu_time


def save_filtered_tauu_WWEchar(WWE_labels = None, WWE_mask = None, tauu_anom_vals = None, duration = None, IWW = None,
                               zonal_extent = None,tauu_anom_mean = None, tauu_abs_mean = None, 
                               center_lon_vals = None, center_time_vals = None, min_lon_vals = None, 
                               max_lon_vals = None, min_time_vals = None, max_time_vals = None,
                               lon_array = None, tauu_time = None, save_name = '',
                               filt_descrip = '120-day HP filtered'):
    
    uniq_WWE_labels = np.unique(WWE_labels)[1:]
    #reference_time  = pd.Timestamp('1970-01-01T00:00:00Z')

    data_vars = dict(
        wwe_labels    =(['time', 'lon'], WWE_labels.squeeze(), dict(units='None', long_name='Unique label for each WWE')),
        wwe_mask      =(['time', 'lon'], WWE_mask.squeeze(), dict(units='Binary', long_name='1s are where WWEs are located, 0s are locations without WWEs')),
        tauu_anom     =(['time', 'lon'], tauu_anom_vals.squeeze(), dict(units='Pa', long_name = 'Mean ' + filt_descrip + ' zonal wind stress')),
        tauu_anom_mean=(['events'], tauu_anom_mean, dict(units='Pa', long_name = 'Mean ' + filt_descrip + ' zonal wind stress per WWE')),
        tauu_abs_mean =(['events'], tauu_abs_mean, dict(units='Pa', long_name = 'Mean absolute zonal wind stress per WWE')),
        duration      =(['events'], duration, dict(units='Days', long_name = 'duration of each WWE')),
        IWW_vals      =(['events'], IWW, dict(units='Pa', long_name='Integrated wind work for each WWE')),
        zonal_extent  =(['events'], zonal_extent, dict(units='Degrees', long_name = 'Longitudinal extent of each WWE')),
        center_lons   =(['events'], center_lon_vals, dict(units='Degrees', long_name = 'Mass-weighted center longitude for each WWE')),
        min_lons      =(['events'], min_lon_vals, dict(units='Degrees', long_name = 'Min longitude for each WWE')),
        max_lons      =(['events'], max_lon_vals, dict(units='Degrees', long_name = 'Max longitude for each WWE')),
        min_times     =(['events'], min_time_vals),
        max_times     =(['events'], max_time_vals),
        center_times  =(['events'], center_time_vals)
    )

    ds = xr.Dataset(data_vars = data_vars,
                    coords=dict(
                        events= (["events"], uniq_WWE_labels),
                        lon   = lon_array,
                        time  = tauu_time,
                    ),
                    attrs=dict(description= filt_descrip + " zonal wind stress and WWE characteristics. Generated using MDTF POD WWE diagnostic")
                   )

    ds.to_netcdf(save_name + '.WWE_characteristics.nc')
    
    return ds

def _preprocess(x, lon_bnds, lat_bnds):
    return x.sel(lon=slice(*lon_bnds), lat=slice(*lat_bnds))


print("\n=======================================")
print("BEGIN WWEs.py ")
print("=======================================")

print("*** Parse MDTF-set environment variables ...")
work_dir     = os.environ["WORK_DIR"]
obs_dir      = os.environ["OBS_DATA"]
casename     = os.environ["CASENAME"]
start_date   = os.environ["startdate"]
end_date     = os.environ["enddate"]
first_year   = os.environ["first_yr"]
last_year    = os.environ["last_yr"]
static_thresh= os.environ['do_static_threshold']
min_lat      = float(os.environ["min_lat"])
max_lat      = float(os.environ["max_lat"])
min_lon      = float(os.environ["min_lon"])
max_lon      = float(os.environ["max_lon"])
regrid_method= os.environ["regrid_method"]

#Define lats to average tauu over and lon range to analyze
lat_lim_list = [min_lat, max_lat]
lon_lim_list = [min_lon, max_lon]

###########################################################################
########### Part 1 ########################################################
########### Get TropFlux observations needed for regridding and plotting
###########################################################################
print(f'*** Now working on obs data\n------------------------------')
obs_file_WWEs = obs_dir + '/TropFlux_120-dayHPfiltered_tauu_1980-2014.nc'

print(f'*** Reading obs data from {obs_file_WWEs}')
obs_WWEs    = xr.open_dataset(obs_file_WWEs)
print(obs_WWEs)

# Subset the data for the user defined first and last years #
obs_WWEs = obs_WWEs.sel(time=slice(first_year, last_year))

obs_lons = obs_WWEs.lon
obs_lats = obs_WWEs.lat
obs_time = obs_WWEs.time
Pac_lons = obs_WWEs.Pac_lon
obs_WWE_mask        = obs_WWEs.WWE_mask
TropFlux_filt_tauu  = obs_WWEs.filtered_tauu
TropFlux_WWEsperlon = obs_WWEs.WWEs_per_lon

###################################################################################
######### PART 2 ##################################################################
######### Prepare Model output for WWE ID code#####################################
###################################################################################
print(f'*** Now starting work on {casename}\n------------------------------')
print('*** Reading variables ...')

#These variables come from the case_env_file that the framework creates
#the case_env_file points to the csv file, which in turn points to the data files.
#Variables from the data files are then read in. See example_multicase.py
# Read the input model data

case_env_file = os.environ["case_env_file"]
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

cat_def_file = case_info['CATALOG_FILE']
case_list    = case_info['CASE_LIST']

#Use partial function to only load part of the data file
lon_bnds, lat_bnds = (0, 360), (-32.5, 32.5)
partial_func       = partial(_preprocess, lon_bnds=lon_bnds, lat_bnds=lat_bnds)

# open the csv file using information provided by the catalog definition file
cat = intake.open_esm_datastore(cat_def_file)

# all cases share variable names and dimension coords in this example, so just get first result for each
tauu_var   = [case['tauu_var'] for case in case_list.values()][0]
time_coord = [case['time_coord'] for case in case_list.values()][0]
lat_coord  = [case['lat_coord'] for case in case_list.values()][0]
lon_coord  = [case['lon_coord'] for case in case_list.values()][0]

############################################################################
#Filter catalog by desired variable and output frequency
############################################################################
#Get tauu (zonal wind stress) variable
tauu_subset = cat.search(variable_id=tauu_var, frequency="day")

# convert tauu_subset catalog to an xarray dataset dict
tauu_dict = tauu_subset.to_dataset_dict(preprocess = partial_func,
                                        xarray_open_kwargs={"decode_times": True, "use_cftime": True})

for k, v in tauu_dict.items(): 
    tauu_arr = tauu_dict[k][tauu_var]

##################################################################
#Get sftlf (land fraction) variable if it exists & mask out land
##################################################################
key = 'sftlf_var'
x = list(case_list[casename].keys())

if(x.count(key) == 1):
    print("Using model land fraction variable to mask out land")
    sftlf_var    = [case['sftlf_var'] for case in case_list.values()][0]
    sftlf_subset = cat.search(variable_id=sftlf_var, frequency="fx")
    # convert sftlf_subset catalog to an xarray dataset dict
    sftlf_dict   = sftlf_subset.to_dataset_dict(preprocess = partial_func)

    for k, v in sftlf_dict.items():
        sftlf_arr = sftlf_dict[k][sftlf_var]

    #mask out land in tauu
    masked_tauu = tauu_arr.where(sftlf_arr < 10)

if(x.count(key) == 0):
    print("Need to use etopo.nc file to mask out the land")
    print('Program will exit for now, as need to build in more code')
    #ls_mask = land_mask_using_etopo(ds = model_ds, topo_latgrid_1D = topo_latgrid_1D, 
    #                                    topo_longrid_1D = topo_longrid_1D,
    #                                    topo_data1D = topo_data1D, lf_cutoff = 10)
    #masked_tauu = model_ds[tauu_name].where(ls_mask == 1)
    sys.exit()

if(x.count(key) > 1):
    print('Error: Multiple land fraction (sftlf) files found. There should only be one!')
    print('Program will exit')
    sys.exit()
    
##################################################
#Convert masked_tauu dataaray back to dataset    
tauu_ds = masked_tauu.to_dataset()

##################################################
#Only keep data during desired time range
tauu_ds = tauu_ds.where((tauu_ds.time.dt.year >= int(first_year)) &
                       (tauu_ds.time.dt.year <= int(last_year)), drop = True)

##################################################
#Create a mask variable for the tauu dataset
tauu_ds["mask"] = xr.where(~np.isnan(tauu_ds[tauu_var].isel(time = 0)), 1, 0)

##################################################
#Regrid tauu to the TropFlux obs grid
##################################################
print('lon size before regridding:', tauu_ds.lon.size)
print('Start regrid code using the following method:', regrid_method)

if tauu_ds.lat.size > 1:
    print('tauu_ds.lat.size > 1')
    regridder_tauu = regridder_model2obs(lon_vals = np.asarray(obs_lons), lat_vals = np.asarray(obs_lats),
                                        in_data = tauu_ds, type_name = regrid_method,
                                        isperiodic = True)
    re_model_tauu  = regridder_tauu(tauu_ds[tauu_var], skipna = True)

print('lon size after regridding:', re_model_tauu.lon.size)
    
##################################################
#Find region of interest
#At this point, re_model_tauu is a DataArray
##################################################
tauu_region = ((re_model_tauu).where(
    (re_model_tauu.lat >= np.array(lat_lim_list).min()) &
    (re_model_tauu.lat <= np.array(lat_lim_list).max()) &
    (re_model_tauu.lon >= np.array(lon_lim_list).min()) &
    (re_model_tauu.lon <= np.array(lon_lim_list).max()),
    drop = True))

print('tauu_region:', tauu_region)

##################################################
#Average over the latitudes
##################################################
#The xarray mean function ignores the nans
tauu_region_latavg = tauu_region.mean(dim = 'lat') 
    
###################################################################################
#Check to see if westerly zonal wind stresses are recorded as positive or negative
###################################################################################
mean_lon220p5 = np.array(np.mean(tauu_region_latavg.sel(lon = 220.5)))
print('mean tauu at 220.5E:', mean_lon220p5)
factor = -1 if mean_lon220p5 > 0 else 1
tauu   = tauu_region_latavg * factor

#Control the chunk size because the chunk size when computing data2use below goes to (1, 1) 
#using the latest MDTF python 3.12, which then takes forever to run
tauu = tauu.chunk({"time": tauu["time"].size})

print('tauu after lat averaging:', tauu)
print('At this point, tauu is a DataArray with time longitude dimensions on the TropFlux grid')

###################################################################################
#Filter tauu to use as input to find WWEs and their chracteristics
###################################################################################
#filt_dataLP = filter_data(data = tauu, nweights = 201, a = 5)
#For now the only option is to apply a 120-day highpass filter
filt_dataHP = filter_data(data = tauu, nweights = 201, a = 120)

#As above, control the chunk size
filt_dataHP = filt_dataHP.chunk({"time": tauu["time"].size})

data2use        = tauu - filt_dataHP
obs_tauu_thresh = 0.04 #Nm-2 Two standard deviations of the TropFlux lat-averaged 120E-280E zonal wind stress.
tauu_thresh2use = obs_tauu_thresh if static_thresh is True else np.round(data2use.std()*2, decimals = 2)

print('tauu_thresh2use:', tauu_thresh2use)
print('data2use', data2use)

###################################################################################
######### PART 3 ##################################################################
######### Find & Save WWEs and their characteristics & statistics #################
###################################################################################
duration, IWW, zonal_extent, tauu_mean, WWE_labels, WWE_mask, center_lons, \
center_times, min_times, max_times, min_lons, max_lons, lon_array, tauu_time = \
find_WWEs_and_characteristics(in_data = data2use, tauu_thresh = tauu_thresh2use, mintime = 5, minlons = 10,
                              xminmax = (3, 3), yminmax = (3, 3), minmax_dur_bins = (5, 27),
                              dur_bin_space = 2, minmax_IWW_bins = (1, 42), IWW_bin_space = 4,
                              xtend_past_lon = 140)

durationB, zonal_extentB, tauu_sum, tauu_abs_mean = WWE_characteristics(wwe_labels = WWE_labels, data = tauu)


print('nWWEs:', duration.size)
print('')

##################################################################################
# Save the WWE characteristics and statistics to a netcdf file
##################################################################################
print('Saving the WWE characteristics to a netcdf file')

save_name = f"{work_dir}/model/netCDF/{casename}.{first_year}-{last_year}"

WWE_chars = save_filtered_tauu_WWEchar(WWE_labels = WWE_labels, WWE_mask = WWE_mask, tauu_anom_vals = np.asarray(data2use), 
                                       duration = duration, IWW = IWW, zonal_extent = zonal_extent, 
                                       tauu_anom_mean = tauu_mean, tauu_abs_mean = tauu_abs_mean, 
                                       center_lon_vals = center_lons, center_time_vals = np.asarray(center_times), 
                                       min_lon_vals = min_lons, max_lon_vals = max_lons, 
                                       min_time_vals = np.asarray(min_times), max_time_vals = np.asarray(max_times), 
                                       lon_array = lon_array, tauu_time = np.asarray(tauu_time), save_name = save_name)

###################################################################################
######### PART 4 ##################################################################
######### Plot Hovmollers and histograms for observations and model ###############
###################################################################################
#Plot the yearly Hovmollers for observations
plot_model_Hovmollers_by_year(data = TropFlux_filt_tauu, wwe_mask = obs_WWE_mask,
                                  lon_vals = Pac_lons, tauu_time = obs_time,
                                  savename = f"{work_dir}/obs/PS/TropFlux",
                                  start_date = '1980-1999', end_date = '2000-2014')

###########################################################################
# Plot Homollers for Model
###########################################################################
plot_model_Hovmollers_by_year(data = data2use, wwe_mask = WWE_mask,
                                  lon_vals = lon_array, tauu_time = tauu_time,
                                  savename = f"{work_dir}/model/PS/{casename}",
                                  start_date = start_date, end_date = end_date)


###########################################################################
# Plot the likelihood of a WWE affecting a given 1degree longitude
###########################################################################
#Convert WWE_lavels from a numpy array to a DataArray
WWE_labels_da = xr.DataArray(data=WWE_labels, dims = ['time', 'lon'], 
                                 coords=dict(
                                     lon=(['lon'], lon_array),
                                     time=tauu_time,),
                                 attrs=dict(description="WWE labels", units = 'N/A',)
                                )


#Call function events_per_lon in WWE_diag_tools.py, which calculates the
#number of unique WWEs affecting a given 1degree longitude bin (i.e., count_all_event_lons)
count_all_event_lons, nall_events = events_per_lon(in_da = WWE_labels_da)


#Convert count_all_even_lons into a probability per day
obs_prop_per_day   = TropFlux_WWEsperlon/obs_time.size*100.
model_prop_per_day = count_all_event_lons/tauu_time.size*100.

#Save the count and probability of a unique WWE per 1degree longitude bin 
data_vars = dict(
    model_WWEs_per_lon      =(['lon'], count_all_event_lons, dict(units='count', long_name='Number of unique WWEs affecting a 1degree lon bin from the model')),
    model_freq_WWEs_per_lon =(['lon'], model_prop_per_day,  dict(units='fractuion', long_name='The fraction of unique WWEs affecting a 1degree lon bin from the model calculated as count/ndays ')),
    obs_WWEs_per_lon        =(['lon'], np.asarray(TropFlux_WWEsperlon), dict(units='count', long_name='Number of unique WWEs affecting a 1degree lon bin in TropFlux observations from 1980-2014')),
    obs_freq_WWEs_per_lon   =(['lon'], np.asarray(obs_prop_per_day),  dict(units='fractuion', long_name='The fraction of unique WWEs affecting a 1degree lon bin from TropFlux calculated as count/ndays '))
)
 
ds = xr.Dataset(data_vars = data_vars,
                coords=dict(lon = lon_array,),
                    attrs=dict(description= "Variables needed to make the *model*_and_TropFlux_WWE_prob_per_day.png figures that the WWEs POD produces")
                   )

ds.to_netcdf(f"{work_dir}/model/netCDF/{casename}_and_TropFlux_WWE_probability_per_day.nc")


# ***** Make the plot ******
save_path = f"{work_dir}/model/PS/"
model_titlename = {casename}

plot_WWE_likelihood_per_lon(lons = Pac_lons, model_prop_per_day = model_prop_per_day,
                            obs_prop_per_day = obs_prop_per_day, savepath = save_path,
                            model_name = casename)
###################################################################################
######### PART 5 ##################################################################
#Close the catalog files and release variable dict reference for garbage collection
###################################################################################
cat.close()
tauu_dict = None

###################################################################################
######### PART 6 ##################################################################
######### Confirm POD executed successfully #######################################
###################################################################################
# ----------------------------------------
print("Last log message by example_multicase POD: finished successfully!")
sys.exit(0)

