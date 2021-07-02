# 28 June TUTT.py
# Tropical Upper Tropospheric Trough Diagnostic Package
#
# ================================================================================
# 
# Last update: 28 June, 2021
# PI: Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)
# Developer/point of contact (Zhuo Wang, Gan Zhang, Chuan-Chieh Chang, and Jiacheng Ye, DAS UIUC)
# 
#  Tropical upper-tropospheric troughs (TUTTs) are part of summertime stationary waves and provide a 
#  unified framework that can be used to better understand tropical cyclone (TC) variability over different basins.
#  Thus, a better understanding of how TUTTs will change as climate warms also increases our confidence in future TC projection. 
#  This diagnostic package is used to evaluate 200-hPa TUTT area in both climate models and reanalysis datasets.
#
# Version and contact info
#
#  - Version: 1.0
#  - Contact info: 
#  Zhuo Wang (zhuowang@illinois.edu)
#
# ================================================================================
# Functionality
#
# 1) Calculates geostrophic zonal winds (Ug) using 200-hPa geopotential height with a fixed Coriolis parameter at 15N.
# 2) Identifies positions of the circumglobal contour of the long-term seasonal-mean Ug. The value of Ug can be specified by the user, 
#    usually ranges from 1 to 2 m/s. The zonal-mean latitude of the circumglobal contour is chosen as the reference latitude.
# 3) The TUTT index is estimated from the area where the circumglobal contour of seasonal-mean Ug extends southward of the reference latitude.
# 4) Calculates TUTT strength and central location.
#
#
# ================================================================================
#
#    All scripts of this package can be found under: /diagnostics/TUTT/ 
#    & observational data under: /obs_data/TUTT/
#
#    Long-term mean 2-D (lat-lon) geopotential height fields are required;
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
        print("The TUTT diag based on example data will Not be executed")
    elif obs_running == 1:
        try:
            os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc_obs.py")
            print("The TUTT diag based on example data has been successfully conducted!")
        except OSError as e:
            print('WARNING',e.errno,e.strerror)
            print("**************************************************")
            print("TUTT_diag_obs.py based on example data is NOT Executed as Expected!")
            print("**************************************************")
    if model_running == 0:
        print("The TUTT diag based on model data will Not be executed")
    elif model_running == 1:
        try:
            os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc_model.py")
            print("The TUTT diag based on model data has been successfully conducted!")
        except OSError as e:
            print('WARNING',e.errno,e.strerror)
            print("**************************************************")
            print("Top-Heaviness Metric Diagnostics (top_heaviness_ratio_calculation.py) is NOT Executed as Expected!")
            print("**************************************************")
            
    print("**************************************************")
    print("Top-Heaviness Metric Diagnostics Executed!")
    print("**************************************************")


