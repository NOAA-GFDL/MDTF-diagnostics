# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_ShiftRatio.py
#
#   Underlying-to-Gaussian Distribution Shift Ratio
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
#   Computes the shifted underlying-to-Gaussian distribution tail exceedances ratio following Loikith and Neelin (2019), Loikith et al. (2018), Loikith and Neelin (2015), Ruff and Neelin (2012)
#
#   Generates spatial plot of this shift ratio over season specified as function of two-meter temperature
#
#   Depends on the following scripts:
#    (1) TempExtDistShape_ShiftRatio_usp.py
#    (2) TempExtDistShape_ShiftRatio_util.py
#
#   Defaults for plotting parameters, etc. that can be altered by user are in TempExtDistShape_ShiftRatio_usp.py
#
#   Utility functions are defined in TempExtDistShape_ShiftRatio_util.py
#
# ======================================================================
# Import standard Python packages
import glob
import os
import json

# Import Python functions specific to the Shift Ratio
from TempExtDistShape_ShiftRatio_util import Region_Mask
from TempExtDistShape_ShiftRatio_util import Seasonal_Anomalies
from TempExtDistShape_ShiftRatio_util import ShiftRatio_Calc
from TempExtDistShape_ShiftRatio_util import ShiftRatio_Plot

print("**************************************************")
print("Executing Underlying-to-Gaussian Distribution Shift Ratio (TempExtDistShape_ShiftRatio.py)......")
print("**************************************************")

# ======================================================================
### Load user-specified parameters (usp) for calcluating and plotting shift ratio

print("Load user-specified parameters...")
os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_ShiftRatio_usp.py")
with open(os.environ["WK_DIR"]+"/TempExtDistShape_ShiftRatio_parameters.json") as outfile:
    ratio_data=json.load(outfile)
print("...Loaded!")
monthsub=json.loads(ratio_data["monthsub"]) #change unicode string into array of integers

# ======================================================================
### List model filenames for two-meter temperature data
T2Mfile=sorted(glob.glob(ratio_data["MODEL_OUTPUT_DIR"]+"/"+ratio_data["MODEL"]+"*"+ratio_data["T2M_VAR"]+".day.nc"))[0]

# ======================================================================
### Load & pre-process region mask
# ----  Generate a map of values corresponding to land regions only
msk=Region_Mask(ratio_data["REGION_MASK_DIR"]+'/'+ratio_data["REGION_MASK_FILENAME"],T2Mfile,ratio_data["LON_VAR"],ratio_data["LAT_VAR"])

# ======================================================================
### Calculate seasonal anomalies for two-meter temperature
T2Manom_data,lon,lat=Seasonal_Anomalies(T2Mfile,ratio_data["LON_VAR"],ratio_data["LAT_VAR"],ratio_data["T2M_VAR"],ratio_data["TIME_VAR"],monthsub,ratio_data["yearbeg"],ratio_data["yearend"])

# ======================================================================
### Compute the ratio of Non-Gaussian to Gaussian shifted two-meter temperature distribution tails
shiftratio=ShiftRatio_Calc(ratio_data["ptile"],ratio_data["shift"],msk,T2Manom_data,lon,lat)

# ======================================================================
### Plot the shift ratio computed above and save the figure in wkdir/temp_extremes_distshape/
ShiftRatio_Plot(T2Mfile,ratio_data["LON_VAR"],ratio_data["COLORMAP_DIR"]+'/'+ratio_data["COLORMAP_FILENAME"],lat,shiftratio,ratio_data["monthstr"],ratio_data["ptile"],ratio_data["FIG_OUTPUT_DIR"],ratio_data["FIG_OUTPUT_FILENAME"])

# ======================================================================

print("**************************************************")
print("Underlying-to-Gaussian Distribution Shift Ratio (TempExtDistShape_ShiftRatio.py) Executed!")
print("**************************************************")
