import numpy as np 
import xarray as xr 
import pandas as pd
import os 
import glob
import matplotlib.pyplot as plt 
import netCDF4 as nc
from scipy import interpolate
import pickle
import sys
import time as timelib
sys.path.append(os.environ['POD_HOME']+'/util')

# have to setup topo file env var, before initial setup, because defines.py needs this variable
os.environ['topo_file'] = os.environ['DATADIR'] + '/topo.nc'
import run_tracker_setup 
import defines

# getting the starting time
start_time = timelib.time()

##################################
###### Running Cython
##################################
cwd = os.getcwd()
if (os.environ['RUN_MCMS'] == 'True'):
  print('Running the cythonize code...')
  
  so_files = ['g2l', 'gcd', 'rhumb_line_nav']
  for i_so_file in so_files: 
    cmd = f"cd {os.environ['POD_HOME']}/util/tracker; python setup_{i_so_file}_v4.py build_ext --inplace"
    os.system(cmd)
    output_file = glob.glob(f"{os.environ['POD_HOME']}/util/tracker/{i_so_file}_v4.*.so")
    cmd = f"mv {output_file[0]} {os.environ['POD_HOME']}/util/tracker/{i_so_file}_v4.so; cd {cwd}"
    os.system(cmd)


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
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  plt.savefig(out_file, dpi=100.)
  plt.close('all')

def plot_empty(out_file):
  plt.figure()
  plt.plot(0, 0, 'w.')
  plt.text(0, 0, 'Run Composites part of the POD to generate this Figure!', va='center', ha='center')
  plt.xticks([])
  plt.yticks([])
  plt.savefig(out_file)
  plt.close('all')

def create_empty_figs():

  print('Creating Empty Figures...')

  # Creating empty figures
  for hemis in defines.composite_hem_list: 
    for var in defines.composite_var_list:
      for season in defines.composite_season_list:
        for lm_type in ['land', 'ocean']:
          out_file = os.path.join(defines.model_images_folder, f"{os.environ['CASENAME']}_area_{var}_{hemis}_{lm_type}_{season.upper()}.png")
          plot_empty(out_file)

  # Plotting empty obs figures
  out_file = f"{os.environ['WK_DIR']}/obs/diff_merra_erai_prw_SH_ocean_WARM.png"
  plot_empty(out_file)

  # SH
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_modis_cld_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_prw_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_w500_SH_ocean_WARM.png"
  plot_empty(out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_SH_ocean_WARM.png"
  plot_empty(out_file)

  # NH
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_modis_cld_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_prw_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_w500_NH_ocean_WARM.png"
  plot_empty(out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_NH_ocean_WARM.png"
  plot_empty(out_file)

  # Plotting empty diff plots 
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_tp_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_w500_SH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_uv10_SH_ocean_WARM.png"
  plot_empty(out_file)

  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_tp_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_w500_NH_ocean_WARM.png"
  plot_empty(out_file)
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_uv10_NH_ocean_WARM.png"
  plot_empty(out_file)
  

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

os.environ['clt_var'] = 'CLT'
os.environ['clt_file'] = '*.'+os.environ['clt_var']+'.6hr.nc'

# Setting up the slp_file to be used
os.environ['MODEL_OUTPUT_DIR']  = os.environ['DATADIR'] + '/6hr'
slp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['slp_var'] + '.6hr.nc'
tp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['tp_var'] + '.6hr.nc'
prw_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['prw_var'] + '.6hr.nc'
uv10_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['uv10_var'] + '.6hr.nc'
w500_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['w500_var'] + '.6hr.nc'
clt_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['clt_var'] + '.6hr.nc'

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

if (os.environ['RUN_COMPOSITES'] == 'True'):
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
  
  # Reading in total cloud fraction
  in_ds = xr.open_dataset(clt_file)
  clt = in_ds.CLT
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
    if (not np.any(ind)) & (reset_firstyr) & (year < eYear): 
        # resetting the first year, because we dont have model data for the specified years
        os.environ['FISTYR'] = f'{year:04d}'
        reset_firstyr = False
        continue
       
    # selecting only the time index for the year
    slp_sel = slp[ind, :, :]
    if (os.environ['RUN_COMPOSITES'] == 'True'):
      tp_sel = tp[ind, :, :]
      prw_sel = prw[ind, :, :]
      uv10_sel = uv10[ind, :, :]
      w500_sel = w500[ind, :, :]
      clt_sel = clt[ind, :, :]

    
    # creating the filename of the output in the correct folder
    out_slp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/slp.{year:04d}.nc"
    print(out_slp_file)
    if (os.environ['RUN_COMPOSITES'] == 'True'):
      out_tp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/tp.{year:04d}.nc"
      out_prw_file= f"{os.environ['WK_DIR']}/tmp/data_converts/prw.{year:04d}.nc"
      out_uv10_file= f"{os.environ['WK_DIR']}/tmp/data_converts/uv10.{year:04d}.nc"
      out_w500_file= f"{os.environ['WK_DIR']}/tmp/data_converts/w500.{year:04d}.nc"
      out_clt_file= f"{os.environ['WK_DIR']}/tmp/data_converts/clt.{year:04d}.nc"
      print(out_tp_file)
      print(out_prw_file)
      print(out_uv10_file)
      print(out_w500_file)
      print(out_clt_file)
    
        
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
    
    if (os.environ['RUN_COMPOSITES'] == 'True'):
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


      ###### Outputting the CLT file
      # creating the xarray dataset
      out_var_ds = xr.Dataset(
          {'clt': (('time', 'lat', 'lon'), w500_sel)}, 
          coords={
              'time': time, 
              'lat': lat, 
              'lon': lon
          })
      # adding the necessary attributes to the file
      out_var_ds.clt.attrs['units'] = '{}'.format('%')
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
      out_var_ds.to_netcdf(out_clt_file)

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

if (os.environ['RUN_COMPOSITES'] == 'False'): 
  print('Composites code turned off!\nCreating empty figures for the html page...')
  create_empty_figs()
else:
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
  merra_prw = ds['merra_pw'].values
  merra_w500 = ds['merra_omega'].values
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
  merra_prw_1d = merra_prw.flatten()
  merra_w500_1d = merra_w500.flatten()

  ## the erai x and y are 1d, have to convert it to a 2d grid
  erai_x_grid, erai_y_grid = np.meshgrid(erai_x, erai_y)
  erai_x_1d = erai_x_grid.flatten()
  erai_y_1d = erai_y_grid.flatten()

  # interpolating the ang, dist plots from observations on to the erai standard grid (same grid as the outputs from the model)
  erai_modis_cld = interpolate.griddata((obs_x_1d, obs_y_1d), modis_cld_1d, (erai_x_1d, erai_y_1d))
  erai_modis_cld = erai_modis_cld.reshape(erai_x_grid.shape)

  erai_merra_prw = interpolate.griddata((obs_x_1d, obs_y_1d), merra_prw_1d, (erai_x_1d, erai_y_1d))
  erai_merra_prw = erai_merra_prw.reshape(erai_x_grid.shape)

  erai_merra_w500 = interpolate.griddata((obs_x_1d, obs_y_1d), merra_w500_1d, (erai_x_1d, erai_y_1d))
  erai_merra_w500 = erai_merra_w500.reshape(erai_x_grid.shape)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_modis_cld_SH_ocean_WARM.png"
  title = 'MODIS Cloud Cover [SH-OCEAN-WARM]'
  # plot_area_fig(obs_x,obs_y,modis_cld,title,out_file)
  plot_area_fig(erai_x,erai_y,erai_modis_cld,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_prw_SH_ocean_WARM.png"
  title = 'MERRA Precipitation [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,erai_merra_prw,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_merra_w500_SH_ocean_WARM.png"
  title = 'MERRA Omega @ 500 hPa [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,erai_merra_w500,title,out_file)


  # SH - Ocean - WARM
  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_SH_ocean_WARM.png"
  title = 'ERA-Interim TP [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,tp_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_SH_ocean_WARM.png"
  title = 'ERA-Interim PRW [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,prw_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_SH_ocean_WARM.png"
  title = 'ERA-Interim Wind Speed [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,uv10_sh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_SH_ocean_WARM.png"
  title = 'ERA-Interim Omega @ 500hPa [SH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,w500_sh_ocean_warm,title,out_file)


  # NH - Ocean - WARM

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_tp_NH_ocean_WARM.png"
  title = 'ERA-Interim TP [NH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,tp_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_prw_NH_ocean_WARM.png"
  title = 'ERA-Interim PRW [NH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,prw_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_uv10_NH_ocean_WARM.png"
  title = 'ERA-Interim Wind Speed [NH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,uv10_nh_ocean_warm,title,out_file)

  out_file = f"{os.environ['WK_DIR']}/obs/{os.environ['CASENAME']}_erai_w500_NH_ocean_WARM.png"
  title = 'ERA-Interim Omega @ 500hPa [NH-OCEAN-WARM]'
  plot_area_fig(erai_x,erai_y,w500_nh_ocean_warm,title,out_file)


  ############################################################
  ####### Creating Difference Plots
  ############################################################

  ## Reading in the model composites
  model_file = f"{os.environ['WK_DIR']}/tmp/RUNDIR/tmprun/read_tmprun/composites.pkl"
  model_data = pickle.load(open(model_file, 'rb'))

  # Creating the plots
  ##################### Model - ERA-Interim SH [All vars] ###########################################
  plt.figure(figsize=(12,8))

  plt.subplot(4,3,1)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'prw'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]}\nPRW [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,2)
  plt.pcolormesh(erai_x, erai_y, prw_sh_ocean_warm, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title('ERA-Interim\nPRW [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,3)
  diff_val = model_val - prw_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]} - ERA-Interim\nPRW [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,4)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'tp'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=0.6)
  plt.colorbar()
  plt.title(f'TP [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,5)
  plt.pcolormesh(erai_x, erai_y, tp_sh_ocean_warm, cmap='jet', vmin=0, vmax=0.6)
  plt.colorbar()
  plt.title('TP [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,6)
  diff_val = model_val - tp_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'TP [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,7)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'uv10'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=14)
  plt.colorbar()
  plt.title(f'UV10 [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,8)
  plt.pcolormesh(erai_x, erai_y, uv10_sh_ocean_warm, cmap='jet', vmin=0, vmax=14)
  plt.colorbar()
  plt.title('UV10 [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,9)
  diff_val = model_val - uv10_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'UV10 [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,10)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'w500'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=-0.3, vmax=.06)
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,11)
  plt.pcolormesh(erai_x, erai_y, w500_sh_ocean_warm, cmap='jet', vmin=-.3, vmax=.06)
  plt.colorbar()
  plt.title('Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,12)
  diff_val = model_val - w500_sh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.tight_layout()
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_vars_SH_ocean_WARM.png"
  plt.savefig(out_file)
  plt.close('all')

  ##################### NH ###########################################
  ##################### Model - ERA-Interim NH [All vars] ###########################################
  plt.figure(figsize=(12,8))

  plt.subplot(4,3,1)
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'prw'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]}\nPRW [NH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,2)
  plt.pcolormesh(erai_x, erai_y, prw_nh_ocean_warm, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title('ERA-Interim\nPRW [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,3)
  diff_val = model_val - prw_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]} - ERA-Interim\nPRW [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,4)
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'tp'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=0.6)
  plt.colorbar()
  plt.title(f'TP [NH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,5)
  plt.pcolormesh(erai_x, erai_y, tp_nh_ocean_warm, cmap='jet', vmin=0, vmax=0.6)
  plt.colorbar()
  plt.title('TP [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,6)
  diff_val = model_val - tp_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'TP [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,7)
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'uv10'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=14)
  plt.colorbar()
  plt.title(f'UV10 [NH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,8)
  plt.pcolormesh(erai_x, erai_y, uv10_nh_ocean_warm, cmap='jet', vmin=0, vmax=14)
  plt.colorbar()
  plt.title('UV10 [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,9)
  diff_val = model_val - uv10_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'UV10 [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)
  
  plt.subplot(4,3,10)
  hemis = 'NH'; lo = 'ocean'; season = 'warm'; var = 'w500'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=-0.3, vmax=.06)
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [NH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,11)
  plt.pcolormesh(erai_x, erai_y, w500_nh_ocean_warm, cmap='jet', vmin=-.3, vmax=.06)
  plt.colorbar()
  plt.title('Omega @ 500 hPa [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(4,3,12)
  diff_val = model_val - w500_nh_ocean_warm
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [NH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.tight_layout()
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_erai_vars_NH_ocean_WARM.png"
  plt.savefig(out_file)
  plt.close('all')
    
  ####################### MODEL - MERRA variables
  plt.figure(figsize=(12,6))

  plt.subplot(2,3,1)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'prw'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]}\nPRW [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(2,3,2)
  tmp = erai_merra_prw.copy()
  tmp[np.isnan(model_val)] = np.nan
  plt.pcolormesh(erai_x, erai_y, tmp, cmap='jet', vmin=0, vmax=24)
  plt.colorbar()
  plt.title('MERRA\nPRW [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(2,3,3)
  diff_val = model_val - erai_merra_prw
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'{os.environ["CASENAME"]} - MERRA\nPRW [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(2,3,4)
  hemis = 'SH'; lo = 'ocean'; season = 'warm'; var = 'w500'
  model_val = model_data[hemis][lo][season][var]['area_sum']/model_data[hemis][lo][season][var]['area_cnt']
  plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet', vmin=-.3, vmax=.06)
  # plt.pcolormesh(erai_x, erai_y, model_val, cmap='jet')
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylabel('Distance [km]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(2,3,5)
  tmp = (erai_merra_w500.copy())
  tmp[np.isnan(model_val)] = np.nan
  # plt.pcolormesh(erai_x, erai_y, tmp, cmap='jet', vmin=-.3, vmax=.06)
  plt.pcolormesh(erai_x, erai_y, tmp, cmap='jet')
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.subplot(2,3,6)
  diff_val = model_val - erai_merra_w500
  vmax = np.nanpercentile(np.abs(diff_val).flatten(), 95)
  vmin = -1*vmax
  plt.pcolormesh(erai_x, erai_y, diff_val, vmin=vmin, vmax=vmax, cmap='bwr')
  plt.colorbar()
  plt.title(f'Omega @ 500 hPa [SH-OCEAN-WARM]')
  plt.ylim(-1500, 1500)
  plt.xlim(-1500, 1500)

  plt.tight_layout()
  out_file = f"{os.environ['WK_DIR']}/model/diff_{os.environ['CASENAME']}_merra_vars_SH_ocean_WARM.png"
  plt.savefig(out_file)
  plt.close('all')

  # End run composites true/false

end_time = timelib.time()

run_time = timelib.gmtime(end_time - start_time)

# Completed Code
print(f'Done Completing ETC-composites driver code in {timelib.strftime("%H:%M:%S", run_time)} seconds.')
