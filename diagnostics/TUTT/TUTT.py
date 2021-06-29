# 28 June TUTT.py
# Tropical Upper Tropospheric Trough Diagnostic Package
#
# ================================================================================
# 
# Last update: 28 June, 2021
# Contributors: Zhuo Wang (zhuowang@illinois.edu)
# 
#  Evaluate model skill for representing vertical motion (omega) profile;
#  The diabatic heating profile is closely related to vertical motion profile. Thus, diagnosing omega 
#  would help us to better understand the coupling between large-scale circulation and precipitation process
#
# Version and contact info
#
#  - Version: 1.0
#  - Contact info: 
#                  Zhuo Wang (zhuowang@illinois.edu)
#
# ================================================================================
# Functionality
#
# 1) 
# 2) 
# 3)
#
# ================================================================================
#
#    All scripts of this package can be found under: /diagnostics/top_heaviness_metric 
#    & observational data under: /obs_data/top_heaviness_metric
#
#    Monthly 3-D (time-lat-lon) geopotential height fields are required;
#
# Required programming language: Tested in the Python 3.7 envrionment;
# Required libraries: Numpy, Scipy, ...
#
# ================================================================================
# Reference: 
#   1) Back, L. E., Hansen, Z., & Handlos, Z. (2017). Estimating vertical motion profile top-heaviness: 
#   Reanalysis compared to satellite-based observations and stratiform rain fraction. 
#   Journal of the Atmospheric Sciences, 74(3), 855-864.
#   2) Our paper which focuses on GEFS v12 diagnostics is under progress...
# 

# driver file
import os
import glob

obs_running=1 # =1 if the user wishes to run the example; =0 if the user wishes to disable it. 
model_running=1 # =1 if the user wishes to run the model data; =0 if the user wishes to disable it. 

missing_file=0
if len(glob.glob(os.environ["OMEGA_FILE"]))==0:
    print("Required OMEGA data missing!")
    missing_file=1

if missing_file == 1:
    print("TUTT Diag Package will NOT be executed!")
    
else:
    if obs_running == 0:
        print("The example data will Not be executed")
    elif obs_running == 1:
        try:
            os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc.py")
            print("The TUTT diag based on example data has been successfully conducted!")
        except OSError as e:
            print('WARNING',e.errno,e.strerror)
            print("**************************************************")
            print("TUTT_diag_obs.py based on example data is NOT Executed as Expected!")
            print("**************************************************")
    if model_running == 0:
        print("The example data will Not be executed")
    elif model_running == 1:
        try:
            os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc.py")
            print("The TUTT diag based on model data has been successfully conducted!")
        except OSError as e:
            print('WARNING',e.errno,e.strerror)
            print("**************************************************")
            print("Top-Heaviness Metric Diagnostics (top_heaviness_ratio_calculation.py) is NOT Executed as Expected!")
            print("**************************************************")
            
    print("**************************************************")
    print("Top-Heaviness Metric Diagnostics Executed!")
    print("**************************************************")


