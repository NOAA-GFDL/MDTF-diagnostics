# 28 June TUTT.py
# Tropical Upper Tropospheric Trough Diagnostic Package
#
# ================================================================================
# 
# Last update: 28 June, 2021
# PI: Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)
# Developer/point of contact (Zhuo Wang, Gan Zhang, Chuan-Chieh Chang, and Jiacheng Ye, DAS UIUC)
# 
# Tropical upper-tropospheric troughs (TUTTs) are part of summertime stationary waves and 
# provide a unified framework that can be used to better understand variability of tropical
# cyclones (TCs) over different basins.Identifying deficiencies in representing TUTTs 
# has important implications for the improved regional TC simulation in climate models. A better 
# understanding of how TUTTs will change as climate warms also increases our confidence in 
# future TC projection. This diagnostic package is used to evaluate 200-hPa TUTT area in 
# both climate models and reanalysis datasets.
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
# 2) Identifies positions of the circumglobal contour of the long-term seasonal-mean Ug. The value of Ug can be specified by the user, and usually ranges from 1 to 2 m/s. The zonal-mean latitude of the circumglobal contour is chosen as the reference latitude.
# 3) The TUTT index is estimated from the area where the circumglobal contour of seasonal-mean Ug extends southward of the reference latitude.
# 4) Calculates TUTT strength and central location.
#
#
# ================================================================================
#
#    All scripts of this package can be found under: /diagnostics/TUTT/ 
#    & observational data under: /obs_data/TUTT/
#
#    3-D (time-lat-lon) 200 hPa geopotential height fields are required;
#
# Required programming language: Tested in the Python 3.7 envrionment;
# Required libraries: "netCDF4", "skimage", "numpy", "scipy", "shapely.geometry", "cartopy"
#
# ================================================================================
# Reference: 
# Wang, Z., Zhang, G., Dunkerton, T. J., & Jin, F. F. (2020). 
#   Summertime stationary waves integrate tropical and extratropical impacts on tropical cyclone activity. 
#   Proceedings of the National Academy of Sciences of the United States of America, 117(37), 22720-22726. https://doi.org/10.1073/pnas.2010547117
#
# Chuan-Chieh Chang and Zhuo's paper is in preparation...
#Title: Chang, C.-C. and Z. Wang, 2021: Summertime Subtropical Stationary Waves: Variability and Impacts on the Tropical Cyclone Activity 


# driver file
import os
import glob

#obs_running=1 # =1 if the user wishes to run the example; =0 if the user wishes to disable it. 
#model_running=1 # =1 if the user wishes to run the model data; =0 if the user wishes to disable it. 

missing_file=0
if len(glob.glob(os.environ["OMEGA_FILE"]))==0:
    print("Required HGT200 data missing!")
    missing_file=1

if missing_file == 1:
    print("TUTT Diag Package will NOT be executed!")
else:
    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc_obs.py")
        print("The TUTT diag based on example data has been successfully conducted!")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("TUTT_diag_obs.py based on example data is NOT Executed as Expected!")
        print("**************************************************")
    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"TUTT_calc_model.py")
        print("The TUTT diag based on model data has been successfully conducted!")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("TUTT_diag_model.py based on model data is NOT Executed as Expected!")
        print("**************************************************")
  
    print("**************************************************")
    print("Tropical Upper-Tropospheric Trough Diagnostics Executed!")
    print("**************************************************")


