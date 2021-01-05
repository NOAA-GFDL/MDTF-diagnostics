import numpy as np 
import xarray as xr 
import pandas as pd
import os 
import matplotlib.pyplot as plt 
import netCDF4 as nc
from scipy import interpolate
import pickle
import sys
sys.path.append(os.environ['POD_HOME']+'/util')

# have to setup topo file env var, before initial setup, because defines.py needs this variable
os.environ['topo_file'] = os.environ['DATADIR'] + '/topo.nc'
import run_tracker_setup 

##################################
###### Function to plot composites
##################################

def plot_area_fig(x,y,data,title,out_file):
  plt.figure()
  plt.pcolormesh(x, y, data, cmap='jet')
  plt.colorbar()
  plt.title(title)
  plt.ylabel('Distance [km]')
  plt.xlabel('Distance [km]')
  plt.savefig(out_file)
  plt.close('all')

##################################
###### Main Code
##################################

# os.environ['topo_file'] = '/localdrive/drive6/erai/converts/invariants.nc'
# os.environ['topo_file'] = os.environ['DATADIR'] + '/topo.nc'
# '/localdrive/drive6/erai/converts/invariants.nc'

print('Start of ETC-Composites...')

### Copying over the MDTF_DOC file
cmd = "cp " + os.environ['POD_HOME']+'/MDTF_Documentation_etc_composites.pdf ' + os.environ['WK_DIR']+'/'
os.system(cmd)

# Creating the necessary SLP yearly files for the necessary years
sYear = int(os.environ['FIRSTYR'])
eYear = int(os.environ['LASTYR'])

# Setitng up the necessary variable names 
os.environ['slp_var'] = 'SLP'
os.environ['slp_file'] = '*.'+os.environ['slp_var']+'.6hr.nc'

os.environ['tp_var'] = 'PRECT'
os.environ['tp_file'] = '*.'+os.environ['tp_var']+'.6hr.nc'

os.environ['prw_var'] = 'PRW'
os.environ['prw_file'] = '*.'+os.environ['prw_var']+'.6hr.nc'

os.environ['uv10_var'] = 'UV10'
os.environ['uv10_file'] = '*.'+os.environ['uv10_var']+'.6hr.nc'

os.environ['w500_var'] = 'W500'
os.environ['w500_file'] = '*.'+os.environ['w500_var']+'.6hr.nc'

# Setting up the slp_file to be used
os.environ['MODEL_OUTPUT_DIR']  = os.environ['DATADIR'] + '/6hr'
slp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['slp_var'] + '.6hr.nc'
tp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['tp_var'] + '.6hr.nc'
prw_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['prw_var'] + '.6hr.nc'
uv10_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['uv10_var'] + '.6hr.nc'
w500_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['w500_var'] + '.6hr.nc'

print('Splitting into yearly files for the tracker ...')

# read in the SLP files from the model data
# getting the type of calendar
ncid = nc.Dataset(slp_file)
calendar = ncid['time'].getncattr('calendar')
ncid.close()

# Using xarray to read in the slp_file
in_ds = xr.open_dataset(slp_file)

# Getting the necessary data 
if (calendar == 'noleap'):
  time = in_ds.time.values
else:
  time = [pd.to_datetime(i) for i in in_ds.time.values]
slp = in_ds.SLP
lat = in_ds.lat.values
lon = in_ds.lon.values
in_ds.close()

# Reading in total precipitation
in_ds = xr.open_dataset(tp_file)
tp = in_ds.PRECT
in_ds.close()

# Reading in total column water vapor
in_ds = xr.open_dataset(prw_file)
prw = in_ds.PRW
in_ds.close()

# Reading in wind speed
in_ds = xr.open_dataset(uv10_file)
uv10 = in_ds.UV10
in_ds.close()

# Reading in wind speed
in_ds = xr.open_dataset(w500_file)
w500 = in_ds.W500
in_ds.close()

# creating the year_list to chunk out the yearly sections of the files
year_list = np.array([i.year for i in time])

# create the output folder if it does not exist
if not os.path.exists(os.environ['WK_DIR'] + '/tmp'): 
    os.makedirs(os.environ['WK_DIR'] + '/tmp')
if not os.path.exists(os.environ['WK_DIR'] + '/tmp/data_converts'): 
    os.makedirs(os.environ['WK_DIR'] + '/tmp/data_converts')

# loop through from sYear to eYear
reset_firstyr = True

for year in range(sYear, eYear+1): 
    ind = (year_list == year)
    if (not np.any(ind)) & (reset_firstyr): 
        # resetting the first year, because we dont have model data for the specified years
        os.environ['FISTYR'] = f'{year:04d}'
        reset_firstyr = False
        continue
        
    # selecting only the time index for the year
    slp_sel = slp[ind, :, :]
    tp_sel = tp[ind, :, :]
    prw_sel = prw[ind, :, :]
    uv10_sel = uv10[ind, :, :]
    w500_sel = w500[ind, :, :]

    
    # creating the filename of the output in the correct folder
    out_slp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/slp.{year:04d}.nc"
    out_tp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/tp.{year:04d}.nc"
    out_prw_file= f"{os.environ['WK_DIR']}/tmp/data_converts/prw.{year:04d}.nc"
    out_uv10_file= f"{os.environ['WK_DIR']}/tmp/data_converts/uv10.{year:04d}.nc"
    out_w500_file= f"{os.environ['WK_DIR']}/tmp/data_converts/w500.{year:04d}.nc"
    
    print(out_slp_file)
    print(out_tp_file)
    print(out_prw_file)
    print(out_uv10_file)
    print(out_w500_file)
        
    # creating my custom time variable to match what is required by the tracker
    time = np.arange(0, np.sum(ind)*6, 6)
    
    ###### Outputting the SLP file
    # creating the xarray dataset
    out_slp_ds = xr.Dataset(
        {'slp': (('time', 'lat', 'lon'), slp_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        })
   # adding the necessary attributes to the SLP file
    out_slp_ds.slp.attrs['units'] = 'mb'
    out_slp_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_slp_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_slp_ds.time.attrs['calendar'] = '365_day'
    else:
        out_slp_ds.time.attrs['calendar'] = calendar
    out_slp_ds.lon.attrs['long_name'] = 'longitude'
    out_slp_ds.lon.attrs['standard_name'] = 'longitude'
    out_slp_ds.lon.attrs['units'] = 'degrees_east'
    out_slp_ds.lon.attrs['axis'] = 'X'
    out_slp_ds.lat.attrs['long_name'] = 'latitude'
    out_slp_ds.lat.attrs['standard_name'] = 'latitude'
    out_slp_ds.lat.attrs['units'] = 'degrees_north'
    out_slp_ds.lat.attrs['axis'] = 'Y'       
    # writing to the netcdf file
    out_slp_ds.to_netcdf(out_slp_file)
    
    ###### Outputting the total precip file
    # creating the xarray dataset
    out_tp_ds = xr.Dataset(
        {'tp': (('time', 'lat', 'lon'), tp_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        })
    # adding the necessary attributes to the file
    out_tp_ds.tp.attrs['units'] = 'mm/hr'
    out_tp_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_tp_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_tp_ds.time.attrs['calendar'] = '365_day'
    else:
        out_tp_ds.time.attrs['calendar'] = calendar
    out_tp_ds.lon.attrs['long_name'] = 'longitude'
    out_tp_ds.lon.attrs['standard_name'] = 'longitude'
    out_tp_ds.lon.attrs['units'] = 'degrees_east'
    out_tp_ds.lon.attrs['axis'] = 'X'
    out_tp_ds.lat.attrs['long_name'] = 'latitude'
    out_tp_ds.lat.attrs['standard_name'] = 'latitude'
    out_tp_ds.lat.attrs['units'] = 'degrees_north'
    out_tp_ds.lat.attrs['axis'] = 'Y'  
    # writing to the netcdf file
    out_tp_ds.to_netcdf(out_tp_file)
    
    ###### Outputting the total column water vapor file
    # creating the xarray dataset
    out_prw_ds = xr.Dataset(
        {'prw': (('time', 'lat', 'lon'), prw_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        })
    # adding the necessary attributes to the file
    out_prw_ds.prw.attrs['units'] = 'mm/hr'
    out_prw_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_prw_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_prw_ds.time.attrs['calendar'] = '365_day'
    else:
        out_prw_ds.time.attrs['calendar'] = calendar
    out_prw_ds.lon.attrs['long_name'] = 'longitude'
    out_prw_ds.lon.attrs['standard_name'] = 'longitude'
    out_prw_ds.lon.attrs['units'] = 'degrees_east'
    out_prw_ds.lon.attrs['axis'] = 'X'
    out_prw_ds.lat.attrs['long_name'] = 'latitude'
    out_prw_ds.lat.attrs['standard_name'] = 'latitude'
    out_prw_ds.lat.attrs['units'] = 'degrees_north'
    out_prw_ds.lat.attrs['axis'] = 'Y'    
    # writing to the netcdf file
    out_prw_ds.to_netcdf(out_prw_file)

    ###### Outputting the UV10 file
    # creating the xarray dataset
    out_var_ds = xr.Dataset(
        {'uv10': (('time', 'lat', 'lon'), uv10_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        })
    # adding the necessary attributes to the file
    out_var_ds.uv10.attrs['units'] = 'm/s'
    out_var_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_var_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_var_ds.time.attrs['calendar'] = '365_day'
    else:
        out_var_ds.time.attrs['calendar'] = calendar
    out_var_ds.lon.attrs['long_name'] = 'longitude'
    out_var_ds.lon.attrs['standard_name'] = 'longitude'
    out_var_ds.lon.attrs['units'] = 'degrees_east'
    out_var_ds.lon.attrs['axis'] = 'X'
    out_var_ds.lat.attrs['long_name'] = 'latitude'
    out_var_ds.lat.attrs['standard_name'] = 'latitude'
    out_var_ds.lat.attrs['units'] = 'degrees_north'
    out_var_ds.lat.attrs['axis'] = 'Y'    
    # writing to the netcdf file
    out_var_ds.to_netcdf(out_uv10_file)
    
    ###### Outputting the W500 file
    # creating the xarray dataset
    out_var_ds = xr.Dataset(
        {'w500': (('time', 'lat', 'lon'), w500_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        })
    # adding the necessary attributes to the file
    out_var_ds.w500.attrs['units'] = 'Pa/s'
    out_var_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_var_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_var_ds.time.attrs['calendar'] = '365_day'
    else:
        out_var_ds.time.attrs['calendar'] = calendar
    out_var_ds.lon.attrs['long_name'] = 'longitude'
    out_var_ds.lon.attrs['standard_name'] = 'longitude'
    out_var_ds.lon.attrs['units'] = 'degrees_east'
    out_var_ds.lon.attrs['axis'] = 'X'
    out_var_ds.lat.attrs['long_name'] = 'latitude'
    out_var_ds.lat.attrs['standard_name'] = 'latitude'
    out_var_ds.lat.attrs['units'] = 'degrees_north'
    out_var_ds.lat.attrs['axis'] = 'Y'    
    # writing to the netcdf file
    out_var_ds.to_netcdf(out_w500_file)

print('Splitting into yearly files for the tracker ... Completed.')

if (os.environ['RUN_MCMS'] == 'True'): 
  print('Running the MCMS Tracker...')
  # Running the tracker 
  cmd = "python %s/util/run_tracker.py"%(os.environ['POD_HOME'])
  os.system(cmd)
  print('Completed the MCMS Tracker')
else:
  print('Running the code using different tracker outputs...')
  run_tracker_setup.init_setup()
  run_tracker_setup.copy_code_over()
  cmd = "python %s/util/run_create_dict.py"%(os.environ['POD_HOME'])
  os.system(cmd)
  print('Completed creating the mat file used for the analysis.')

# Running the track stats 
cmd = "python %s/util/run_track_stats.py"%(os.environ['POD_HOME'])
os.system(cmd)

if (os.environ['RUN_COMPOSITES'] == 'True'): 
  print('Running the Composites Code and creating the figures...')

  # Running the composites code
  # create the necesssary variable files and composites 
  print('Running the composites code...')
  cmd = "python %s/util/run_composites.py"%(os.environ['POD_HOME'])
  os.system(cmd)

  ###################################################
  ##### Creating plots from obs/merra and era-interim
  ###################################################

  # load in the netcdf files 
  obs_file = f"{os.environ['OBS_DATA']}/modis_merra.nc"
  era_file = f"{os.environ['OBS_DATA']}/era_interim.nc"

  # reading in the observation file
  ds = xr.open_dataset(obs_file)
  obs_x = ds['X'].values
  obs_y = ds['Y'].values
  modis_cld = ds['modis_cld'].values
  merra_pw = ds['merra_pw'].values
  merra_omega = ds['merra_omega'].values
  ds.close()

  # reading in the re-analysis file
  ds = xr.open_dataset(era_file)
  erai_x = ds['X'].values
  erai_y = ds['Y'].values
  tp_nh_ocean_warm = ds['tp_nh_ocean_warm'].values
  prw_nh_ocean_warm = ds['prw_nh_ocean_warm'].values
  uv10_nh_ocean_warm = ds['uv10_nh_ocean_warm'].values
  w500_nh_ocean_warm = ds['w500_nh_ocean_warm'].values
  tp_sh_ocean_warm = ds['tp_sh_ocean_warm'].values
  prw_sh_ocean_warm = ds['prw_sh_ocean_warm'].values
  uv10_sh_ocean_warm = ds['uv10_sh_ocean_warm'].values
  w500_sh_ocean_warm = ds['w500_sh_ocean_warm'].values
  ds.close()

  # Re-griding the observation data 
  ## setting up the necessary x,y values in the format required for griddata
  obs_x_1d = obs_x.flatten()
  obs_y_1d = obs_y.flatten()

  modis_cld_1d = modis_cld.flatten()
  merra_pw_1d = merra_pw.flatten()
  merra_omega_1d = merra_omega.flatten()

  ## the erai x and y are 1d, have to convert it to a 2d grid
  erai_x_grid, erai_y_grid = np.meshgrid(erai_x, erai_y)
  erai_x_1d = erai_x_grid.flatten()
  erai_y_1d = erai_y_grid.flatten()

  # interpolating the ang, dist plots from observations on to the erai standard grid (same grid as the outputs from the model)
  erai_modis_cld = interpolate.griddata((obs_x_1d, obs_y_1d), modis_cld_1d, (erai_x_1d, erai_y_1d))
  erai_modis_cld = erai_modis_cld.reshape(erai_x_grid.shape)

  erai_merra_pw = interpolate.griddata((obs_x_1d, obs_y_1d), merra_pw_1d, (erai_x_1d, erai_y_1d))
  erai_merra_pw = erai_merra_pw.reshape(erai_x_grid.shape)

  erai_merra_omega = interpolate.griddata((obs_x_1d, obs_y_1d), merra_omega_1d, (erai_x_1d, erai_y_1d))
  erai_merra_omega = erai_merra_omega.reshape(erai_x_grid.shape)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_modis_cld_SH_ocean_WARM.png"
  title = 'MODIS Cloud Cover [SH-Ocean-WARM]'
  # plot_area_fig(obs_x,obs_y,modis_cld,title,out_file)
  plot_area_fig(erai_x,erai_y,erai_modis_cld,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_pw_SH_ocean_WARM.png"
  title = 'MERRA Precipitation [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,erai_merra_pw,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_omega_SH_ocean_WARM.png"
  title = 'MERRA Omega @ 500 hPa [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,erai_merra_omega,title,out_file)


  # SH - Ocean - WARM
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_SH_ocean_WARM.png"
  title = 'ERA-Interim TP [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,tp_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
  title = 'ERA-Interim PRW [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,prw_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_SH_ocean_WARM.png"
  title = 'ERA-Interim Wind Speed [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,uv10_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_SH_ocean_WARM.png"
  title = 'ERA-Interim Omega @ 500hPa [SH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,w500_sh_ocean_warm,title,out_file)


  # NH - Ocean - WARM

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_NH_ocean_WARM.png"
  title = 'ERA-Interim TP [NH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,tp_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
  title = 'ERA-Interim PRW [NH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,prw_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_NH_ocean_WARM.png"
  title = 'ERA-Interim Wind Speed [NH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,uv10_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_NH_ocean_WARM.png"
  title = 'ERA-Interim Omega @ 500hPa [NH-Ocean-WARM]'
  plot_area_fig(erai_x,erai_y,w500_nh_ocean_warm,title,out_file)


  ############################################################
  ####### Creating Difference Plots
  ############################################################

  ## Reading in the model composites
  model_file = f"{os.environ['WK_DIR']}/tmp/RUNDIR/tmprun/read_tmprun/composites.pkl"
  model_data = pickle.load(open(model_file, 'rb'))

  # Creating the plots

  ##################### SH ###########################################
  # MODEL - ERA-Interim PR (Total Precip)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_tp_SH_ocean_WARM.png"
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'tp'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - tp_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nSH OCEAN WARM TP")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim PRW (Total Column Water Vapor)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'prw'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - prw_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nSH OCEAN WARM PRW")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim W500 (Vertical Velocity at 500hPa)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_w500_SH_ocean_WARM.png"
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'w500'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - w500_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nSH OCEAN WARM Omega @ 500hPa")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim UV10 (Wind Speeds)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_uv10_SH_ocean_WARM.png"
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'uv10'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - uv10_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nSH OCEAN WARM Wind Speeds")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  ##################### NH ###########################################
  # MODEL - ERA-Interim PR (Total Precip)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_tp_NH_ocean_WARM.png"
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'tp'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - tp_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nNH OCEAN WARM TP")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim PRW (Total Column Water Vapor)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'prw'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - prw_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nNH OCEAN WARM PRW")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim W500 (Vertical Velocity at 500hPa)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_w500_NH_ocean_WARM.png"
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'w500'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - w500_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nNH OCEAN WARM Omega @ 500hPa")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  # MODEL - ERA-Interim UV10 (Wind Speeds)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_uv10_NH_ocean_WARM.png"
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'uv10'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.figure()
  diff_val = model_val - uv10_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.title(f"{os.environ['CASENAME']} - ERA-Interim\nNH OCEAN WARM Wind Speeds")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

  ####################### MERRA - ERA-Interim Difference

  # MERRA - ERA-Interim
  out_file = f"{os.environ['WK_DIR']}/obs/diff_merra_erai_prw_SH_ocean_WARM.png"
  plt.figure()
  diff_val = erai_merra_pw - prw_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 80)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  # plt.title(f"MERRA -  {os.environ['CASENAME']}\nPW")
  plt.title(f"MERRA -  ERA-Interim\nSH OCEAN WARM PW")
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.colorbar()
  plt.savefig(out_file)
  plt.close('all')

# Completed Code
print('Done Completing ETC-composites driver code.')
