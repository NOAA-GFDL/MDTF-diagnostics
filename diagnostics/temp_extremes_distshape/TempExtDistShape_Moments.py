# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_Moments.py
#
#   Moments of Temperature Distribution
#    as part of functionality provided by
#   Surface Temperature Extremes and Distribution Shape Package (temp_extremes_distshape.py)
#
#   Version 1 15-Jan-2020 Arielle J. Catalano (PSU)
#   PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#   Science lead: Paul C. Loikith (PSU; ploikith@pdx.edu)
#   Current developer: Arielle J. Catalano (PSU; a.j.catalano@pdx.edu)
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
#   Computes the moments of the surface temperature probability distribution
#
#   Generates spatial plot of mean, variance, and skewness of two-meter temperature for season specified
#
#   Depends on the following scripts:
#    (1) TempExtDistShape_Moments_usp.py
#    (2) TempExtDistShape_Moments_util.py
#    (3) TempExtDistShape_SeasonAndTail_usp.py
#
#   Defaults for plotting parameters, etc. that can be altered by user are in TempExtDistShape_Moments_usp.py
#   Defaults for season, range of years, etc. that can be altered by user are in TempExtDistShape_SeasonAndTail_usp.py
# 
#   Utility functions are defined in TempExtDistShape_Moments_util.py
#  
# ======================================================================
# Import standard Python packages
import glob
import os
import json

# Import Python functions specific to Non-Gaussian to Gaussian Shift Ratio
from TempExtDistShape_Moments_util import Region_Mask
from TempExtDistShape_Moments_util import Seasonal_Moments
from TempExtDistShape_Moments_util import Moments_Plot

print("**************************************************")
print("Executing Moments (TempExtDistShape_Moments.py)......")
print("**************************************************")

# ======================================================================
### Load user-specified parameters (usp) for calcluating and plotting shift ratio
# ----  This is in the /var_code/temp_extremes_distshape folder under TempExtDistShape_ShiftRatio_usp.py and TempExtDistShape_SeasonAndTail_usp.py

print(("Load user-specified season and tail..."), end=' ')
os.system("python "+os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_SeasonAndTail_usp.py")
with open(os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_SeasonAndTail.json") as outfile:
    season_data=json.load(outfile)
print("...Loaded!")

print(("Load user-specified parameters..."), end=' ')
os.system("python "+os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_Moments_usp.py")
with open(os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_Moments_parameters.json") as outfile:
    mom_data=json.load(outfile)
print("...Loaded!")

# ======================================================================


# ======================================================================
### List model filenames for two-meter temperature data
T2Mfile=sorted(glob.glob(mom_data["MODEL_OUTPUT_DIR"]+"/"+mom_data["MODEL"]+"*"+mom_data["T2M_VAR"]+".day.nc"))[0]

# ======================================================================
### Load & pre-process region mask
# ----  Generate a map of values corresponding to land regions only
msk=Region_Mask(mom_data["REGION_MASK_DIR"]+'/'+mom_data["REGION_MASK_FILENAME"],T2Mfile,mom_data["LON_VAR"],mom_data["LAT_VAR"])

# ======================================================================
### Calculate seasonal subset for two-meter temperature
seas_mean,seas_std,seas_skew,lon,lat=Seasonal_Moments(T2Mfile,mom_data["LON_VAR"],mom_data["LAT_VAR"],mom_data["T2M_VAR"],mom_data["TIME_VAR"],season_data["monthsub"],season_data["yearbeg"],season_data["yearend"],msk)

# ======================================================================
data=[seas_mean,seas_std,seas_skew]
Moments_Plot(T2Mfile,mom_data["LON_VAR"],lat,season_data["monthstr"],mom_data["cmaps"],mom_data["titles"],data,mom_data["tickrange"],mom_data["var_units"],mom_data["FIG_OUTPUT_DIR"],mom_data["FIG_OUTPUT_FILENAME"])

# ======================================================================

### Copy observation figures over for comparisons
os.popen('cp '+os.environ["VARDATA"]+'temp_extremes_distshape/'+mom_data["FIG_OBS_FILENAME"]+' '+mom_data["FIG_OBS_DIR"]+'/')

# ======================================================================

print("**************************************************")
print("Moments of Temperature Distribution (TempExtDistShape_Moments.py) Executed!")
print("**************************************************")
