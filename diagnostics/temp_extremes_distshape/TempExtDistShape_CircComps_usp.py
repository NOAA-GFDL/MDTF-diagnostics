# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_CircComps_usp.py
#
#   Called by TempExtDistShape_CircComps.py
#    Provides User-Specified Parameters for Calculating and Plotting
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
import json
import os
import glob

# ======================================================================
# START USER SPECIFIED SECTION
# ======================================================================
### Model name and output directory
MODEL=os.environ["CASENAME"]
MODEL_OUTPUT_DIR=os.environ["MODEL_OUTPUT_DIR"] # where original model data are located

### Variable names
T2M_VAR=os.environ["tas_var"]
SLP_VAR=os.environ["psl_var"]
Z500_VAR=os.environ["zg_var"]
TIME_VAR=os.environ["time_var"]
LAT_VAR=os.environ["lat_var"]
LON_VAR=os.environ["lon_var"]

### Location information, use "-" or "_" instead of spaces in city name
# ----- For DJF
city='Yellowknife'
statlat=62.4540
statlon=-114.3718
# ----- For JJA
#city='Rennes'
#statlat=48.0698
#statlon=-1.7344

### Plotting parameters
lagstep=2 #number of days between lags
lagtot=4 #maximum lag prior to t=0
SLPminval=980
SLPmaxval=1040
SLPrangestep=1
SLPcbarstep=4 #different range for colorbar ticks
Tminval=-40
Tmaxval=20
Trangestep=2
Tcbarstep=4 #different range for colorbar ticks
Tanomminval=-50
Tanommaxval=50
Tanomrangestep=0.5
Z500minval=5000
Z500maxval=5800
Z500rangestep=50
Z500cbarstep=100 #different range for colorbar ticks
Z500anomminval=-2
Z500anommaxval=2
Z500anomrangestep=0.1

### Model output figure
# -----  load monthstr from user-defined file TempExtDistShape_SeasonAndTail_usp.py
os.system("python "+os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_SeasonAndTail_usp.py")
with open(os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_SeasonAndTail.json") as outfile:
    season_data=json.load(outfile)

FIG_OUTPUT_DIR=os.environ["variab_dir"]+"/temp_extremes_distshape/model/PS"
FIG_OUTPUT_FILENAME="CircComps_"+city+"_"+season_data["monthstr"]+".ps"

### Reanalysis output figure for comparisons
FIG_OBS_DIR=os.environ["variab_dir"]+"/temp_extremes_distshape/obs"
FIG_OBS_FILENAME="MERRA2_198001-200912_res=0.5-0.66.CircComps_"+city+"_"+season_data["monthstr"]+".png"

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
#
# ======================================================================
# DO NOT MODIFY CODE BELOW UNLESS
# YOU KNOW WHAT YOU ARE DOING
# ======================================================================
data={}

data["MODEL"]=MODEL
data["MODEL_OUTPUT_DIR"]=MODEL_OUTPUT_DIR

### File names
data["FIG_OUTPUT_DIR"]=FIG_OUTPUT_DIR
data["FIG_OUTPUT_FILENAME"]=FIG_OUTPUT_FILENAME
data["FIG_OBS_DIR"]=FIG_OBS_DIR
data["FIG_OBS_FILENAME"]=FIG_OBS_FILENAME

### Variable names
data["T2M_VAR"]=T2M_VAR
data["SLP_VAR"]=SLP_VAR
data["Z500_VAR"]=Z500_VAR
data["TIME_VAR"]=TIME_VAR
data["LAT_VAR"]=LAT_VAR
data["LON_VAR"]=LON_VAR

data["city"]=city
data["statlat"]=statlat
data["statlon"]=statlon

data["lagstep"]=lagstep
data["lagtot"]=lagtot
data["SLPminval"]=SLPminval
data["SLPmaxval"]=SLPmaxval
data["SLPrangestep"]=SLPrangestep
data["SLPcbarstep"]=SLPcbarstep
data["Tminval"]=Tminval
data["Tmaxval"]=Tmaxval
data["Trangestep"]=Trangestep
data["Tcbarstep"]=Tcbarstep
data["Tanomminval"]=Tanomminval
data["Tanommaxval"]=Tanommaxval
data["Tanomrangestep"]=Tanomrangestep
data["Z500minval"]=Z500minval
data["Z500maxval"]=Z500maxval
data["Z500rangestep"]=Z500rangestep
data["Z500cbarstep"]=Z500cbarstep
data["Z500anomminval"]=Z500anomminval
data["Z500anommaxval"]=Z500anommaxval
data["Z500anomrangestep"]=Z500anomrangestep

# Taking care of function arguments for calculating circulation composites
data["args1"]=[ \
city, \
statlat, \
statlon, \
lagstep, \
lagtot, \
SLPminval, \
SLPmaxval, \
SLPrangestep, \
SLPcbarstep, \
Tminval, \
Tmaxval, \
Trangestep, \
Tcbarstep, \
Tanomminval, \
Tanommaxval, \
Tanomrangestep, \
Z500minval, \
Z500maxval, \
Z500rangestep, \
Z500cbarstep, \
Z500anomminval, \
Z500anommaxval, \
Z500anomrangestep, \
MODEL_OUTPUT_DIR, \
MODEL, \
FIG_OUTPUT_FILENAME, \
FIG_OUTPUT_DIR, \
FIG_OBS_FILENAME, \
FIG_OBS_DIR, \
TIME_VAR, \
T2M_VAR, \
SLP_VAR, \
Z500_VAR, \
LAT_VAR, \
LON_VAR ]

with open(os.environ["VARCODE"]+"/temp_extremes_distshape/"+"TempExtDistShape_CircComps_parameters.json", "w") as outfile:
    json.dump(data, outfile)

