import numpy as np 
import xarray as xr 
import os 
import matplotlib.pyplot as plt 
import netCDF4 as nc
import sys
sys.path.append(os.environ['POD_HOME']+'/util')

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

# Setting up the slp_file to be used
os.environ['MODEL_OUTPUT_DIR']  = os.environ['DATADIR'] + '/6hr'
slp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['slp_var'] + '.6hr.nc'
tp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['tp_var'] + '.6hr.nc'

# read in the SLP files from the model data
# getting the type of calendar
ncid = nc.Dataset(slp_file)
calendar = ncid['time'].getncattr('calendar')
ncid.close()

# Using xarray to read in the slp_file
in_ds = xr.open_dataset(slp_file)

# Getting the necessary data 
time = in_ds.time.values
slp = in_ds.SLP
lat = in_ds.lat.values
lon = in_ds.lon.values
in_ds.close()

# Reading in total precipitation
in_ds = xr.open_dataset(tp_file)
tp = in_ds.PRECT
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
    
    # creating the filename of the output in the correct folder
    out_slp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/slp.{year:04d}.nc"
    out_tp_file= f"{os.environ['WK_DIR']}/tmp/data_converts/tp.{year:04d}.nc"
    print(out_slp_file)
    print(out_tp_file)
        
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
        }
    )
    
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
        }
    )
    
    # adding the necessary attributes to the SLP file
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


# Running the tracker 
cmd = "python %s/util/run_tracker.py"%(os.environ['POD_HOME'])
os.system(cmd)

# Running the track stats 
cmd = "python %s/util/run_track_stats.py"%(os.environ['POD_HOME'])
os.system(cmd)

# Code to create the yearly total precipitation files
# create a function and call it here? as well as above? 

# Running the composites code
# create the necesssary variable files and composites 
cmd = "python %s/util/run_composites.py"%(os.environ['POD_HOME'])
os.system(cmd)

print('Done Completing ETC-composites driver code.')
