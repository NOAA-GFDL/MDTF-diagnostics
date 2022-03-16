#!/usr/bin/env python
################################# INSTRUCTIONS ##########################
# Edit the defines.py with the folder and information
# then run this code run_tracker.py

import os
print('Copying over the files to run the tracker...')
# os.system('cp ./defines.py ./tracker/defines.py')
cmd = 'cp %s/util/defines.py %s/util/tracker/defines.py'%(os.environ['POD_HOME'], os.environ['POD_HOME'])
os.system(cmd)
import defines
import run_tracker_setup

################## MAIN CODE #################

# Initially create the folders
# then copy the codes over
run_tracker_setup.init_setup()
run_tracker_setup.copy_code_over()

os.chdir(defines.code_folder)
print ("Curently in folder: ", os.getcwd())

####### running the code to track ###########
os.system('python3 setup_v4.py')
os.system('python3 center_finder_v4.py')
os.system('python3 track_finder_v4.py')
os.system('python3 read_mcms_v4.py template_temp_multi_1.py')
os.system('python3 read_mcms_v4.py template_temp_multi_2.py')
# if (defines.create_matlab_dictionaries):
#   os.system('python3 main_create_dict.py')
