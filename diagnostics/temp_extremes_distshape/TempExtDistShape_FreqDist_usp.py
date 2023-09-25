# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_FreqDist_usp.py
#
#   Called by TempExtDistShape_FreqDist.py
#    Provides User-Specified Parameters for Calculating and Plotting
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Diagnostics Package
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

### Locations and associated coordinates
citynames=['Yellowknife','Pendleton','Rennes St-Jacques','Berlin','Adelaide','North Platte']
statlats=[62.4540,45.6721,48.0698,52.5200,-34.9285,41.1403] #in degrees N
statlons=[-114.3718,-118.7886,-1.7344,13.4050,138.6007,-100.7601] #in degrees E

### Set season, binwidth, and percentile threshold for Gaussian fit calculations
yearbeg=int(os.environ["FIRSTYR"])
yearend=int(os.environ["LASTYR"])
monthsub=[[1,2,12],[1,2,12],[6,7,8],[1,2,12],[1,2,12],[1,2,12]]
monthstr=['DJF','DJF','JJA','DJF','DJF','DJF']
binwidth=1 #to compute temperature anomaly histogram for fitting Gaussian distribution
ptile=int(os.environ["ptile"])

### Figure subplots - depends on number of locations specified
plotrows=3
plotcols=2

### Save figure to filename/directory
FIG_OUTPUT_DIR=os.environ["WK_DIR"]+"/model/PS"
FIG_OUTPUT_FILENAME='FreqDists.ps'

### Reanalysis output figure for comparisons
FIG_OBS_DIR=os.environ["WK_DIR"]+"/obs/PS"
FIG_OBS_FILENAME="MERRA2_198001-200912_res=0.5-0.66.FreqDists.png"

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
data["ptile"]=ptile
data["monthsub"]=monthsub
data["monthstr"]=monthstr
data["statlats"]=statlats
data["statlons"]=statlons
data["citynames"]=citynames
data["binwidth"]=binwidth
data["plotrows"]=plotrows
data["plotcols"]=plotcols

# Taking care of function arguments for calculating/plotting Gaussian fit
data["args1"]=[
monthsub, \
monthstr, \
statlats, \
statlons, \
citynames, \
binwidth, \
plotrows, \
plotcols, \
yearbeg, \
yearend, \
ptile, \
MODEL_OUTPUT_DIR, \
MODEL, \
FIG_OUTPUT_FILENAME, \
FIG_OUTPUT_DIR, \
FIG_OBS_DIR, \
FIG_OBS_FILENAME, \
TIME_VAR, \
T2M_VAR, \
LAT_VAR, \
LON_VAR ]

with open(os.environ["WK_DIR"]+"/TempExtDistShape_FreqDist_parameters.json", "w") as outfile:
    json.dump(data, outfile)

