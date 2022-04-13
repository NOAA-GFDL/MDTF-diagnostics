# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# ObsSubset_usp.py
#
#   Called by ObsSubset.py
#    Provides User-Specified Parameters for Subsetting Observation Files
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

### Set shift for non-Gaussian tail calculations
shift=0.5

### Set seasons and percentiles to identify distribution tails
monthsubs=[[6,7,8],[12,1,2]]
monthstrs=['JJA','DJF']
ptiles=[5,95]

### Set range of years, season, and tail percentile threshold for calculations
yearbeg=int(os.environ["FIRSTYR"])
yearend=int(os.environ["LASTYR"])

### Region mask directory & filename
REGION_MASK_DIR=os.environ["OBS_DATA"]
REGION_MASK_FILENAME="MERRA2_landmask.mat"

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
data["shift"]=shift
data["yearbeg"]=yearbeg
data["yearend"]=yearend
data["TIME_VAR"]=TIME_VAR
data["LAT_VAR"]=LAT_VAR
data["LON_VAR"]=LON_VAR
data["T2M_VAR"]=T2M_VAR
data["monthsubs"]=monthsubs
data["monthstrs"]=monthstrs
data["ptiles"]=ptiles

# Taking care of function arguments
data["args1"]=[ \
REGION_MASK_DIR, \
REGION_MASK_FILENAME, \
MODEL_OUTPUT_DIR, \
MODEL, \
shift, \
yearbeg, \
yearend, \
monthsubs, \
monthstrs, \
ptiles, \
TIME_VAR, \
T2M_VAR, \
LAT_VAR, \
LON_VAR ]

with open(os.environ["WK_DIR"]+"/ObsSubset_parameters.json", "w") as outfile:
    json.dump(data, outfile)