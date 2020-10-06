import os
import glob

#########################################################################################
############################ TRACKER MODULE SETTINGS ####################################
#########################################################################################

# temporary assignment of the necessary values
os.environ['slp_var'] = 'slp'

# variable file 
os.environ['slp_file'] = '*.' + os.environ['slp_var'] + '.6hr.nc'

# model output filename file 
os.environ['MODEL_OUTPUT_DIR'] = os.environ['DATADIR'] + '/6hr'

missing_file = 0
# if (len(glob.glob(os.environ['MODEL_OUTPUT_DIR'] + '/' + os.environ['slp_file'])) == 0): 
#   print('Required SLP file missing!')
#   missing_file = 1

if (missing_file == 1): 
  print('MISSING FILES: ETC-composites will not be executed!')
else:

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

  # I have to split up the data into yearly chunks for the code to work
  # SLP directory to read in the data 
  # slp_data_directory = '/localdrive/drive6/era5/data/six_hrly/converts'
  slp_data_directory = os.environ['WK_DIR'] + '/tmp/data_converts' 

  # again this has to be provided, but for now I have to change this to match the data 
  topo_file = '/localdrive/drive6/erai/converts/invariants.nc'
  model = 'tmprun'

  # over write years have to changed from firstyr to last year
  # over_write_years = [2019, 2019]
  over_write_years = [int(os.environ['FIRSTYR']), int(os.environ['LASTYR'])]
 
  # this is needed to create the composites, for now I will assume the pre-processing code creates the necessary chunks of data
  # var_data_directory = '/localdrive/drive6/era5/data/six_hrly/converts/'
  slp_data_directory = os.environ['WK_DIR'] + '/tmp/data_converts' 

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
  thresh_landsea = 50.0/100.0

  # Print a lot to screen to debug
  verbose = 0

  # Flag to hard copy data files over to the RUN directory
  # If false, it will only create a symbolic link to outputs folder
  hard_copy = False

  ################ ADDITIONAL OPTIONS
  # set this flag to create the tracked cyclones into matlab dictionaries
  # the .mat files are required to compute statistics and create plots
  create_matlab_dictionaries = True

  #########################################################################################
  ####################### FRONT DETECTION MODULE SETTINGS #################################
  #########################################################################################

  # change below if you want to run the front deteciton module for different set of years
  front_years = over_write_years

  #########################################################################################
  ########################## TRANSECT ANALYSIS  ###########################################
  #########################################################################################

  # change below if you want to run the front deteciton module for different set of years
  transect_years = over_write_years

  # transect_var_list = ['w', 'u', 'v', 't']
  # transect_var_list = ['clc', 'cls']

  # transect_var_list = ['rh', 'clc', 'cls']
  # This variable sets all values below the threshold as NaN, before doing any calculations
  # Set to none, if you don't want to apply a threshold
  # transect_var_thres = [None, None, None] 
  transect_hemis_list = ['NH', 'SH']

  transect_var_list = ['rh',  'clc', 'cls', 'w', 'u', 'v', 't']
  transect_var_thres = [None, None, None, None, None, None, None] 

  # possible seasons ['all', 'djf', 'jja', 'son', 'mam']
  # transect_season_list = ['all'] 
  # transect_season_list = ['all', 'djf', 'jja', 'son', 'mam']
  transect_season_list = ['all', 'djf', 'jja', 'son', 'mam', 'warm']

  # colormap for the plots
  transect_cmap = 'default'

  # setting the center range that we consider for the centers of our cyclones (in Latitudes)
  # the latitude range provided here will be flipped for the SH
  # transect_centers_range = [30, 40]
  # transect_centers_range = [40, 60]
  transect_centers_range = [30, 60]

  #########################################################################################
  ########################## COMPOSITE ANALYSIS SETTINGS ##################################
  #########################################################################################

  # Number of cores used to process the datacyc creation, set it to 1 for serial processing
  # num_cores = mp.cpu_count() - 2
  # if I am running the new code, then I can't really do the parallel processing 
  # num_cores = 4
  # import multiprocessing as mp
  num_cores = 1

  # composite_var_list = ['pr']
  # composite_var_list = ['prw']
  composite_var_list = ['wap500', 'clt', 'prw', 'slp', 'cls850']
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

