import os

#########################################################################################
############################ TRACKER MODULE SETTINGS ####################################
#########################################################################################

# temporary assignment of the necessary values
os.environ['slp_var'] = 'slp'

# variable file 
os.environ['slp_file'] = '*.' + os.environ['slp_var'] + '.6hr.nc'

# model output filename file 
os.environ['MODEL_OUTPUT_DIR'] = os.environ['DATADIR'] + '/6hr'

# make the necessary directory 
if not os.path.exists(os.environ['WK_DIR'] + '/model'): 
  os.makedirs(os.environ['WK_DIR'] + '/model')
if not os.path.exists(os.environ['WK_DIR'] + '/obs'): 
  os.makedirs(os.environ['WK_DIR'] + '/obs')

# this is where the tracker code will be run from 
if not os.path.exists(os.environ['WK_DIR'] + '/tmp'): 
  os.makedirs(os.environ['WK_DIR'] + '/tmp')

# this is where I will be converting the model data into chunks of years that the code is run for
if not os.path.exists(os.environ['WK_DIR'] + '/tmp/data_converts'): 
  os.makedirs(os.environ['WK_DIR'] + '/tmp/data_converts')

# this is where I will be running my code from 
if not os.path.exists(os.environ['WK_DIR'] + '/tmp/RUNDIR'): 
  os.makedirs(os.environ['WK_DIR'] + '/tmp/RUNDIR')

# location of the source code that is required to run
# this is from pod home files
# source_code_folder = '/localdrive/drive10/mcms_tracker/'
source_code_folder = os.environ['POD_HOME'] + '/util/'

# again this has to be provided, but for now I have to change this to match the data 
# topo_file = '/localdrive/drive6/erai/converts/invariants.nc'
topo_file = os.environ['topo_file']
model = 'tmprun'

# the latitude distribution file for ERA-Interim/MERRA
obs_lat_distrib_file = os.environ['obs_lat_distrib_file']

# over write years have to changed from firstyr to last year
# over_write_years = [2019, 2019]
over_write_years = [int(os.environ['FIRSTYR']), int(os.environ['LASTYR'])]

# this is needed to create the composites, for now I will assume the pre-processing code creates the necessary chunks of data
slp_data_directory = os.environ['WK_DIR'] + '/tmp/data_converts' 
var_data_directory = os.environ['WK_DIR'] + '/tmp/data_converts' 

# location to which to save the outputs from the tracker
# also this is the location from which the tracker will be run 
# NOTE: the tracker does not run from the source code location
# main_folder_location = '/localdrive/drive10/mcms_tracker/RUNDIR/'
main_folder_location = os.environ['WK_DIR'] + '/tmp/RUNDIR/'

# creating the links to other folder locations that are called by other python codes
main_folder = os.path.join(main_folder_location, model) + '/'
code_folder = os.path.join(main_folder, 'CODE') + '/'
out_folder = os.path.join(main_folder, 'out_%s'%(model)) + '/'
read_folder = os.path.join(main_folder, 'read_%s'%(model)) + '/'
out_files_folder = os.path.join(out_folder, '%s_files'%(model)) + '/'
slp_folder = os.path.join(main_folder, 'data') + '/'
images_folder = os.path.join(read_folder, 'images') + '/'
fronts_folder = os.path.join(read_folder, 'fronts') + '/'
data_folder = os.path.join(main_folder, 'var_data') + '/'

# output images folders
model_images_folder = os.environ['WK_DIR'] + '/model/'
obs_images_folder = os.environ['WK_DIR'] + '/obs/'

# threshold for height to defining land mask and topo.
# JJJ - b/c of interpolation and non-zero height of some SST region,
# need to use a value larger than 0 otherwise parts of the ocean become land.
# thresh_landsea = 50.0/100.0
thresh_landsea_hgt = 50 # in meters # was 50 for all testing, changed this to match the v2 version of the code
thresh_landsea_lsm = 50.0/100.0 # in fractional amount of land #was 50 for all testing, changed this to match the v2 version of the code

# Print a lot to screen to debug
verbose = 0

# Flag to hard copy data files over to the RUN directory
# If false, it will only create a symbolic link to outputs folder
hard_copy = False

################ ADDITIONAL OPTIONS
# set this flag to create the tracked cyclones into matlab dictionaries
# the .mat files are required to compute statistics and create plots
# create_matlab_dictionaries = True
# removed aboved flag because we have to always create the matlab dictionaries

# check if we have to run the MCMS tracker or not
if (os.environ['USE_EXTERNAL_TRACKS'] == 'True'):
  track_file = os.environ['EXTERNAL_TRACKS_FILE']

#########################################################################################
####################### FRONT DETECTION MODULE SETTINGS #################################
#########################################################################################

# change below if you want to run the front deteciton module for different set of years
front_years = over_write_years

#########################################################################################
########################## COMPOSITE ANALYSIS SETTINGS ##################################
#########################################################################################

composite_years = over_write_years
# composite_years = [int(os.environ['FIRSTYR']),  int(os.environ['FIRSTYR'])]
# Number of cores used to process the datacyc creation, set it to 1 for serial processing
# num_cores = mp.cpu_count() - 2
# if I am running the new code, then I can't really do the parallel processing 
# num_cores = 4
# import multiprocessing as mp
num_cores = 1

# composite_var_list = ['pr']
# composite_var_list = ['prw']
# composite_var_list = ['wap500', 'clt', 'prw', 'slp', 'cls850']
folder_6hr =  os.environ['DATADIR'] + '/6hr/'
files = os.listdir(folder_6hr)

# getting the composites var list from the created variable in the "DATADIR"/6hr folder
composite_var_list = [file.replace(os.environ['CASENAME']+'.', '').replace('.6hr.nc', '') for file in files if not '.psl.6hr.nc' in file]
if ('u10' in composite_var_list) & ('v10' in composite_var_list):
  # if both exists then add uv10 to the list
  composite_var_list.append('uv10')
# always remove the u10 and v10 from the list
if ('u10' in composite_var_list):
  composite_var_list.remove('u10')
if ('v10' in composite_var_list):
  composite_var_list.remove('v10')

#renaming the wap500 to w500 used by the code
if ('omega' in composite_var_list):
  composite_var_list.remove('omega')
  composite_var_list.append('w500')

print(f'Variables to run composites: {composite_var_list}')

composite_available_var_list = ['pr', 'prw', 'w500', 'uv10', 'clt']

composite_hem_list = ['NH', 'SH']
composite_season_list = ['all', 'djf', 'jja', 'son', 'mam', 'warm']

# bins for histogram
circ = {
    'dist_div': 100., 
    'ang_div': 20.,
    'dist_max': 1500.,
    }

area = {
    'dist_div': 100., 
    'dist_max': 1500.
    }

