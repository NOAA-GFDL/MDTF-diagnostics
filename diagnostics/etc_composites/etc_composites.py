import numpy as np 
import xarray as xr 
import os 
import matplotlib.pyplot as plt 
import netCDF4 as nc

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

# Setting up the slp_file to be used
os.environ['MODEL_OUTPUT_DIR']  = os.environ['DATADIR'] + '/6hr'
slp_file =  os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['CASENAME'] + '.' + os.environ['slp_var'] + '.6hr.nc'

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
    
    # creating the filename of the output in the correct folder
    out_file= f"{os.environ['WK_DIR']}/tmp/data_converts/slp.{year:04d}.nc"
    print(out_file)
        
    # creating my custom time variable to match what is required by the tracker
    time = np.arange(0, np.sum(ind)*6, 6)
    
    # creating the xarray dataset
    out_ds = xr.Dataset(
        {'slp': (('time', 'lat', 'lon'), slp_sel)}, 
        coords={
            'time': time, 
            'lat': lat, 
            'lon': lon
        }
    )
    
    # adding the necessary attributes to the SLP file
    out_ds.slp.attrs['units'] = 'mb'
    
    out_ds.time.attrs['delta_t'] = "0000-00-00 06:00:00";
    out_ds.time.attrs['units'] = f"hours since {year:04d}-01-01 00:00:00";
    if (calendar == 'noleap'):
        out_ds.time.attrs['calendar'] = '365_day'
    else:
        out_ds.time.attrs['calendar'] = calendar
        
    out_ds.lon.attrs['long_name'] = 'longitude'
    out_ds.lon.attrs['standard_name'] = 'longitude'
    out_ds.lon.attrs['units'] = 'degrees_east'
    out_ds.lon.attrs['axis'] = 'X'
    
    out_ds.lat.attrs['long_name'] = 'latitude'
    out_ds.lat.attrs['standard_name'] = 'latitude'
    out_ds.lat.attrs['units'] = 'degrees_north'
    out_ds.lat.attrs['axis'] = 'Y'
            
    # writing to the netcdf file
    out_ds.to_netcdf(out_file)


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

print('Done Completing ETC-composites driver code.')
