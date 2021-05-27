# 26 May top_heaviness_metric.py
# Top-Heaviness Metric 
#
# ================================================================================
# 
# Last update: 20 May, 2021
# Contributors: Jiacheng Ye (UIUC), Zhuo Wang (UIUC)
# 
#  Evaluate model skill for representing vertical motion (omega) profile;
#  The diabatic heating profile is closely related to vertical motion profile. Thus, diagnosing omega 
#  would help us to better understand the coupling between large-scale circulation and precipitation process
#
# Version and contact info
#
#  - Version: 1.0
#  - Contact info: Jiacheng Ye (jye18@illinois.edu) and
#                  Zhuo Wang (zhuowang@illinois.edu)
#
# ================================================================================
# Functionality
#
# 1) calculate top-heaviness ratio
# Under developing 
#
# ================================================================================
#
#    All scripts of this package can be found under: /diagnostics/top_heaviness_metric 
#    & observational data under: /obs_data/top_heaviness_metric
#
#    Monthly 4-D (time-plev-lat-lon) vertical motion (wap) fields are required;
#
# Required programming language and libraries: Tested by Python3; Numpy, Scipy
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

missing_file=0
if len(glob.glob(os.environ["OMEGA_FILE"]))==0:
    print("Required OMEGA data missing!")
    missing_file=1

if missing_file==1:
    print("Top-heaviness metric diagnostics Package will NOT be executed!")
else:
    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"top_heaviness_ratio_calculation.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Top-Heaviness Metric Diagnostics (top_heaviness_ratio_calculation.py) is NOT Executed as Expected!")
        print("**************************************************")
    # if the user only focuses on calculating top-heaviess ratio instead of applying some tests on 
    #   ratio robustness, the user can choose not to run the following python file.  
    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"top_heaviness_ratio_robustness_calc.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Top-Heaviness Metric Diagnostics (top_heaviness_ratio_robustness_calc.py) is NOT Executed as Expected!")
        print("**************************************************")

    print("**************************************************")
    print("Top-Heaviness Metric Diagnostics Executed!")
    print("**************************************************")


