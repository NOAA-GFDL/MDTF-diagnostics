#!/usr/bin/env python
################################# INSTRUCTIONS ##########################
# Edit the defines.py with the folder and information
# then run this code run_tracker.py

import os
import defines

def init_setup():
  '''
  Creates the necessary directories and copies over the slp data into the folders
  '''

  # Create main folder specified in defines
  if not os.path.exists(defines.main_folder):
    print ("Making Directory!")
    os.makedirs(defines.main_folder)
    os.makedirs(defines.code_folder)
    os.makedirs(defines.out_folder)
    os.makedirs(defines.out_files_folder)
    os.makedirs(defines.slp_folder)
    os.makedirs(defines.read_folder)
    os.makedirs(defines.images_folder)
    print ("Completed making directories...")
  else:
    print ("Folder already exists!")

  if not defines.slp_data_directory:
    print ("SLP source directory not defined, copy slp data into the data folder!")
  elif (defines.hard_copy):
    sys_cmd = 'rsync %sslp*.nc %s'%(defines.slp_data_directory, defines.slp_folder)
    os.system(sys_cmd)
    print ("Loaded slp data files into the data folder...")
  else:
    for root, dirs, files in os.walk(defines.slp_data_directory):
      for fn in files:
        if (fn.endswith('.nc') & fn.startswith('slp')):
          full_file = os.path.join(root, fn)
          link_file = os.path.join(defines.slp_folder, fn)
          sys_cmd = "ln -s %s %s"%(full_file, link_file)
          os.system(sys_cmd)
    print ("Soft linked slp data files into the data folder...")
  
  # cd'ing into the CODE folder
  os.system('cd %s'%(defines.code_folder))
  print ("Cd'ing into the code folder...")

def copy_code_over():
  '''
  Function to copy code over from the specified locations to the locations needed by the tracker.
  '''
  print ("Copying files over...")
  sys_cmd = 'rsync -r --exclude ".git*" --exclude "*.mat" --exclude "*.nc" %s/ %s'%(os.path.join(defines.source_code_folder, 'tracker'), defines.code_folder)
  os.system(sys_cmd)
  if (defines.hard_copy):
    sys_cmd = 'rsync --progress %s %s'%(defines.topo_file, os.path.join(defines.out_files_folder, '%s_hgt.nc'%(defines.model)))
    os.system(sys_cmd)
    print ("Copied code and topography file...")
  else:
    sys_cmd = 'ln -s %s %s'%(defines.topo_file, os.path.join(defines.out_files_folder, '%s_hgt.nc'%(defines.model)))
    os.system(sys_cmd)
    print ("Copied code and soft linked topography file...")


 
################## MAIN CODE #################

# Initially create the folders
# then copy the codes over
init_setup()
copy_code_over()

os.chdir(defines.code_folder)
print ("Curently in folder: ", os.getcwd())

####### running the code to track ###########
os.system('python3 setup_v4.py')
os.system('python3 center_finder_v4.py')
os.system('python3 track_finder_v4.py')
os.system('python3 read_mcms_v4.py template_temp_multi_1.py')
os.system('python3 read_mcms_v4.py template_temp_multi_2.py')
if (defines.create_matlab_dictionaries):
  os.system('python3 main_create_dict.py')


####todo list
# 1) lat and lon adjust and time
# create a python dictionary for the identified tracks
# and grab the necessary data for the tracks
# move read folder to a backup with timestamp 
# and create the new folder 
