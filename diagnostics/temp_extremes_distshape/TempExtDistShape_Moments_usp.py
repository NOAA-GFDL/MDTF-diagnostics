# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_Moments_usp.py
#
#   Called by TempExtDistShape_Moments.py
#    Provides User-Specified Parameters for Calculating and Plotting
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
import json
import os

# ======================================================================
# START USER SPECIFIED SECTION
# ======================================================================
### Model name and output directory
MODEL=os.environ["CASENAME"]
MODEL_OUTPUT_DIR=os.environ["DATADIR"]+"/day"

### Variable Names
T2M_VAR=os.environ["tas_var"]
TIME_VAR=os.environ["time_coord"]
LAT_VAR=os.environ["lat_coord"]
LON_VAR=os.environ["lon_coord"]

### Set range of years, season, and tail percentile threshold for calculations
yearbeg=int(os.environ["FIRSTYR"])
yearend=int(os.environ["LASTYR"])
monthstr=os.environ["monthstr"]
monthsub=os.environ["monthsub"]
ptile=int(os.environ["ptile"])

### Region mask directory & filename
REGION_MASK_DIR=os.environ["OBS_DATA"]
REGION_MASK_FILENAME="MERRA2_landmask.mat"

###  Set plotting properties
cmaps=['YlOrRd','GnBu','PiYG']
titles=['Mean','Standard Deviation','Skewness']
tickrange=[[-40,-30,-20,-10,0,10,20,30,40],[0,1,2,3,4,5,6,7,8,9,10],[-2,-1,0,1,2]]
var_units= u"\u00b0"+'C'

### Output figure name and directory
FIG_OUTPUT_DIR=os.environ["WK_DIR"]+"/model/PS"
FIG_OUTPUT_FILENAME="Moments_"+monthstr+".ps"

### Reanalysis output figure for comparisons
FIG_OBS_DIR=os.environ["WK_DIR"]+"/obs/PS"
FIG_OBS_FILENAME="MERRA2_198001-200912_res=0.5-0.66.Moments_"+monthstr+".png"

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
#
# ======================================================================
# DO NOT MODIFY CODE BELOW
# ======================================================================
data={}

data["MODEL"]=MODEL
data["MODEL_OUTPUT_DIR"]=MODEL_OUTPUT_DIR
data["REGION_MASK_DIR"]=REGION_MASK_DIR
data["REGION_MASK_FILENAME"]=REGION_MASK_FILENAME
data["FIG_OUTPUT_DIR"]=FIG_OUTPUT_DIR
data["FIG_OUTPUT_FILENAME"]=FIG_OUTPUT_FILENAME
data["FIG_OBS_DIR"]=FIG_OBS_DIR
data["FIG_OBS_FILENAME"]=FIG_OBS_FILENAME

data["TIME_VAR"]=TIME_VAR
data["LAT_VAR"]=LAT_VAR
data["LON_VAR"]=LON_VAR
data["T2M_VAR"]=T2M_VAR

data["yearbeg"]=yearbeg
data["yearend"]=yearend
data["monthsub"]=monthsub
data["monthstr"]=monthstr
data["ptile"]=ptile

data["cmaps"]=cmaps
data["titles"]=titles
data["tickrange"]=tickrange
data["var_units"]=var_units

# Taking care of function arguments for calculating shift ratio
data["args1"]=[ \
cmaps, \
tickrange, \
titles, \
var_units, \
REGION_MASK_DIR, \
REGION_MASK_FILENAME, \
MODEL_OUTPUT_DIR, \
MODEL, \
yearbeg, \
yearend, \
monthsub, \
monthstr, \
ptile, \
FIG_OUTPUT_FILENAME, \
FIG_OUTPUT_DIR, \
FIG_OBS_DIR, \
FIG_OBS_FILENAME, \
TIME_VAR, \
T2M_VAR, \
LAT_VAR, \
LON_VAR ]

with open(os.environ["WK_DIR"]+"/TempExtDistShape_Moments_parameters.json", "w") as outfile:
    json.dump(data, outfile)

