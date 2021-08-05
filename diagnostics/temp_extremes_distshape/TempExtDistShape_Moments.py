# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_Moments.py
#
#   Moments of Temperature Distribution
#    as part of functionality provided by
#   Surface Temperature Extremes and Distribution Shape Package (temp_extremes_distshape.py)
#
#   Version 1 07-Jul-2020 Arielle J. Catalano (PSU)
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
#
#   Defaults for plotting parameters, etc. that can be altered by user are in TempExtDistShape_Moments_usp.py
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
print("Load user-specified parameters...")
os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_Moments_usp.py")
with open(os.environ["WK_DIR"]+"/TempExtDistShape_Moments_parameters.json") as outfile:
    mom_data=json.load(outfile)
print("...Loaded!")
monthsub=json.loads(mom_data["monthsub"]) #change unicode string into array of integers

# ======================================================================
### List model filenames for two-meter temperature data
print(mom_data["MODEL_OUTPUT_DIR"])
T2Mfile=sorted(glob.glob(mom_data["MODEL_OUTPUT_DIR"]+"/"+mom_data["MODEL"]+"*"+mom_data["T2M_VAR"]+".day.nc"))[0]

# ======================================================================
### Load & pre-process region mask
# ----  Generate a map of values corresponding to land regions only
msk=Region_Mask(mom_data["REGION_MASK_DIR"]+'/'+mom_data["REGION_MASK_FILENAME"],T2Mfile,mom_data["LON_VAR"],mom_data["LAT_VAR"])

# ======================================================================
### Calculate seasonal subset for two-meter temperature
seas_mean,seas_std,seas_skew,lon,lat=Seasonal_Moments(T2Mfile,mom_data["LON_VAR"],mom_data["LAT_VAR"],mom_data["T2M_VAR"],mom_data["TIME_VAR"],monthsub,mom_data["yearbeg"],mom_data["yearend"],msk)

# ======================================================================
data=[seas_mean,seas_std,seas_skew]
Moments_Plot(T2Mfile,mom_data["LON_VAR"],lat,mom_data["monthstr"],mom_data["cmaps"],mom_data["titles"],data,mom_data["tickrange"],mom_data["var_units"],mom_data["FIG_OUTPUT_DIR"],mom_data["FIG_OUTPUT_FILENAME"])

# ======================================================================

print("**************************************************")
print("Moments of Temperature Distribution (TempExtDistShape_Moments.py) Executed!")
print("**************************************************")
