import multiprocessing as mp

#######################################################################
################### VARIABLES FOR PROCESSING   ########################
#######################################################################
# Number of cores used to process the datacyc creation, set it to 1 for serial processing
# num_cores = mp.cpu_count() - 2
num_cores = 1

#######################################################################
######### VARIABLES THAT NEED TO BE SET FOR THE MODELS ################
#######################################################################

# year_list = range(2013, 2014)
year_list = range(2007, 2008)
out_folder = '/localdrive/drive10/jj/datacycs/out_nc/'
hem_list = ['NH']

######################################
############## MERRA-2 ###############
######################################

# Defining the variables 
model_name = 'merra2'
model_calendar_type = 'julian'

## MERRA-2 TRACKING 
datacyc_file_format = '/mnt/drive1/processed_data/tracks/merra2_tracks/ERAI_{year}_cyc.mat'

# var_names = ['ps']
# model_var_names = ['ps']
# vardata_file_format = '/mnt/drive5/merra2/six_hrly/MERRA_{year}_slv.nc'

var_names = ['pr']
model_var_names = ['prectot']
vardata_file_format = '/mnt/drive5/merra2/six_hrly/MERRA_{year}_flx.nc'

# var_names = ['u850', 'v850']
# model_var_names = ['', '']
# vardata_file_format = '/mnt/drive5/merra2/six_hrly/MERRA_{year}_slv_2.nc'

# constant files
topo_lm_file = '/mnt/drive1/jj/MCMS/v1/datacyc/topo_lm_data/%s_topo.nc'%(model_name)

'''
######################################
################ ERAI ################
######################################

# Defining the variables 
model_name = 'erai'
model_calendar_type = 'julian'

## MERRA-2 TRACKING 
datacyc_file_format = '/mnt/drive1/processed_data/tracks/merra2_tracks/ERAI_{year}_cyc.mat'

#var_names = ['prw', 'prc']
# model_var_names = ['msl', 'cp', 'tp', 'var137'] # leave empty if same as var_names
# model_var_names = ['var137', 'cp'] # leave empty if same as var_names
# out_folder = '/mnt/drive1/jj/MCMS/v1/create_datacyc/out_nc'
vardata_file_format = '/mnt/drive5/ERAINTERIM/{VAR_NAME}/{VAR_NAME}_{year}.nc'

# constant files
topo_lm_file = '/mnt/drive1/jj/MCMS/v1/datacyc/topo_lm_data/%s_topo.nc'%(model_name)
'''
