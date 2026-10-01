# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransCriticalCollapse_usp.py
#
#   Called by convecTransCriticalCollapse.py
#    Provides User-Specified Parameters for Fitting and Plotting
#
#   This file is part of the Convective Transition Diagnostic Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
import json
import os
import glob

# ======================================================================
# START USER SPECIFIED SECTION
# ======================================================================
# Model name (will show up in the MODEL figure)
MODEL=os.environ["CASENAME"]

# Spatial resolution for OBS (default: R2+TMIv7)
#  Default: "0.25" rather than os.environ["RES"]
#  because the total number of events for OBS is "small"
RES="0.25"

# Number of regions
#  Use grids with 1<=region<=NUMBER_OF_REGIONS in the mask
NUMBER_OF_REGIONS=4 # default: 4
# Region names
REGION_STR=["WPac","EPac","Atl","Ind"]

TAVE_VAR=os.environ["tave_var"]
QSAT_INT_VAR=os.environ["qsat_int_var"]
# Use 1:tave, or 2:qsat_int as Bulk Tropospheric Temperature Measure 
BULK_TROPOSPHERIC_TEMPERATURE_MEASURE=int(os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"])

# Directory & Filename for saving binned results (netCDF4)
#  tave or qsat_int will be appended to BIN_OUTPUT_FILENAME
BIN_OUTPUT_DIR=os.environ["WORK_DIR"]+"/model/netCDF"
BIN_OUTPUT_FILENAME=os.environ["CASENAME"]+".convecTransBasic"

if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
    TEMP_VAR=TAVE_VAR
    TEMP_VAR_STR="$\widehat{T}$"
    TEMP_UNITS="(K)"
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
    TEMP_VAR=QSAT_INT_VAR
    TEMP_VAR_STR="$\widehat{q_{sat}}$"
    TEMP_UNITS="(mm)"
BIN_OUTPUT_FILENAME+="_"+TEMP_VAR

# List binned data file (with filename corresponding to casename)
bin_output_list=sorted(glob.glob(BIN_OUTPUT_DIR+"/"+BIN_OUTPUT_FILENAME+".nc"))

# Directory & Filename for saving figures 
#  convecTransCriticalCollapse.py generates 2 sets figures for MODEL
FIG_OUTPUT_DIR=os.environ["WORK_DIR"] + "/model/PS"
# Figure filename for Convective Transition Statistics (CTS)
#  collapsed by shifting CWV by Critical CWV
FIG_FILENAME_CTS=os.environ["CASENAME"]+".convecTransCriticalCollapse_stats"+"_"+TEMP_VAR+".eps"
# Figure filename for Critical CWV
FIG_FILENAME_WC=os.environ["CASENAME"]+".convecTransCriticalCollapse_wc"+"_"+TEMP_VAR+".eps"

## Binned data filename & figure directory/filename for OBS (default: R2TMIv7) ##
OBS="Reanalysis-2 + TMIv7r1" # will show up in the OBS figure
bin_obs_list=sorted(glob.glob(os.environ["OBS_DATA"]\
                    +"/convecTransBasic_R2TMIv7r1_200206_201405_res="\
                    +RES+"_fillNrCWV_"\
                    +TEMP_VAR+".nc"))
# convecTransCriticalCollapse.py generates 2 sets figures for OBS too
FIG_OBS_DIR=os.environ["WORK_DIR"] + "/obs/PS"
FIG_OBS_FILENAME_CTS="convecTransCriticalCollapse_stats_R2TMIv7r1_200206_201405_res="\
                      +RES+"_fillNrCWV_"+TEMP_VAR+".eps"
FIG_OBS_FILENAME_WC="convecTransCriticalCollapse_wc_R2TMIv7r1_200206_201405_res="\
                      +RES+"_fillNrCWV_"+TEMP_VAR+".eps"

# Don't fit/plot bins with PDF<PDF_THRESHOLD
PDF_THRESHOLD = 1e-5  # default: 1e-5

# Don't fit/plot tave/qsat_int with narrow cwv range (< CWV_RANGE_THRESHOLD mm)
CWV_RANGE_THRESHOLD = 18  # default: 18

# Don't fit/plot tave/qsat_int with low conditional probability of precipitation
CP_THRESHOLD = 0.2

##### Start: FITTING-REQUIRED PARAMETERS #####
# Use PRECIP_REF (units: mm/hr) to find a 0-th order approximation of Critical CWV w_c
#  and PRECIP_FIT_MIN<precip<PRECIP_FIT_MAX (units: mm/hr) for Fitting
# Different values for MODEL & OBS 
#  Change values for MODEL if necessary
PRECIP_REF_MODEL=1
PRECIP_FIT_MIN_MODEL=1.5
PRECIP_FIT_MAX_MODEL=2.5
#
PRECIP_REF_OBS=1
PRECIP_FIT_MIN_OBS=3
PRECIP_FIT_MAX_OBS=5
###### End: FITTING-REQUIRED PARAMETERS ######

# Range for CWV (minus w_c) over which fitting is done
#  DON NOT CHANGE THE VALUES (default: -60 & 30)
CWV_FIT_RANGE_MIN=-60
CWV_FIT_RANGE_MAX=30

# Force the OBS & MODEL figures to use the same color map
#  Will be ignored if binned OBS data does not exist
USE_SAME_COLOR_MAP=True

# Plot OBS results on top of MODEL results for comparison
#  Will be ignored if binned OBS data does not exist
# Only applies to FIG_FILENAME_WC
OVERLAY_OBS_ON_TOP_OF_MODEL_FIG=True

## Plot formatting ##
axes_fontsize = 12 # size of font in all plots
legend_fontsize = 9
marker_size = 40 # size of markers in scatter plots
xtick_pad = 10 # padding between x tick labels and actual plot
figsize1 = 14 # figure size set by figsize=(figsize1,figsize2)
figsize2 = 12 

### There are 4+2 figures in level 2 diagnostics ###
### Choose the plot parameters for each figure below ###
xlim1={}
xlim2={}

ylim1={}
ylim2={}

xlabel={}
ylabel={}

xticks={}
yticks={}

#==========================================
##### Figure 1 : Precip vs. CWV-w_c #######
#==========================================
xlim1['f1']=-45 
xlim2['f1']=15

ylim1['f1']=0
ylim2['f1']=8

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f1']="CWV-$w_c$ (mm)"
ylabel['f1']="Precip (mm hr$^-$$^1$)"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
xticks['f1']=[-45,-30,-15,0,15]
yticks['f1']=[0,1,2,3,4,5,6,7,8]


#========================================================
##### Figure 2 : Probability of precip vs. CWV-w_c ######
#========================================================
xlim1['f2']=-45 
xlim2['f2']=15

ylim1['f2']=0
ylim2['f2']=1

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f2']="CWV-$w_c$ (mm)"
ylabel['f2']="Probability of Precip"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
xticks['f2']=[-45,-30,-15,0,15]
yticks['f2']=[0.0,0.2,0.4,0.6,0.8,1.0]

#==============================================
###### Figure 3 : Total PDF vs. CWV-w_c #######
#==============================================
xlim1['f3']=-45
xlim2['f3']=15

ylim1['f3']=5e-3
ylim2['f3']=1e2

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f3']="CWV-$w_c$ (mm)"
ylabel['f3']="PDF/PDF($w_c$)"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
xticks['f3']=[-45,-30,-15,0,15]
yticks['f3']=[]

#====================================================
##### Figure 4 : Precipitating PDF vs. CWV-w_c ######
#====================================================
xlim1['f4']=-45
xlim2['f4']=15

ylim1['f4']=5e-4
ylim2['f4']=1e1

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f4']="CWV-$w_c$ (mm)"
ylabel['f4']="PDF/PDF($w_c$)"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
xticks['f4']=[-45,-30,-15,0,15]
yticks['f4']=[]

#====================================================
########## Figure 5 : w_c vs. Temperature ###########
#====================================================
if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
    xlim1['f5']=268
    xlim2['f5']=274
    ylim1['f5']=45
    ylim2['f5']=85
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
    xlim1['f5']=45
    xlim2['f5']=85
    ylim1['f5']=40
    ylim2['f5']=80

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f5']=TEMP_VAR_STR+" "+TEMP_UNITS
ylabel['f5']="$w_c$ (mm)"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
    xticks['f5']=[268,269,270,271,272,273,274]
    yticks['f5']=[45,50,55,60,65,70,75,80,85]
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
    xticks['f5']=[45,50,55,60,65,70,75,80,85]
    yticks['f5']=[40,45,50,55,60,65,70,75,80]

#====================================================
########## Figure 5 : w_c vs. Temperature ###########
#====================================================
if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
    xlim1['f6']=268
    xlim2['f6']=274
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
    xlim1['f6']=45
    xlim2['f6']=85

ylim1['f6']=0.78
ylim2['f6']=1

### Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f6']=TEMP_VAR_STR+" "+TEMP_UNITS
ylabel['f6']="$w_c/\widehat{q_{sat}}$"

### Enter ticks as lists ##
## Note: this option overrides axes limit options above ##
if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==1:
    xticks['f6']=[268,269,270,271,272,273,274]
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE==2:
    xticks['f6']=[45,50,55,60,65,70,75,80,85]
yticks['f6']=[0.78,0.8,0.82,0.84,0.86,0.88,0.9,0.92,0.94,0.96,0.98,1]

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
# ======================================================================
# DO NOT MODIFY CODE BELOW UNLESS
# YOU KNOW WHAT YOU ARE DOING
# ======================================================================
data={}

data["bin_output_list"]=bin_output_list
data["FIG_FILENAME_CTS"]=FIG_FILENAME_CTS
data["FIG_FILENAME_WC"]=FIG_FILENAME_WC
data["FIG_OBS_FILENAME_CTS"]=FIG_OBS_FILENAME_CTS
data["FIG_OBS_FILENAME_WC"]=FIG_OBS_FILENAME_WC

data["args1"]=[ bin_output_list,\
                TAVE_VAR,\
                QSAT_INT_VAR,\
                BULK_TROPOSPHERIC_TEMPERATURE_MEASURE ]

data["args2"]=[ bin_obs_list,\
                TAVE_VAR,\
                QSAT_INT_VAR,\
                BULK_TROPOSPHERIC_TEMPERATURE_MEASURE ]

data["args3"]=[ NUMBER_OF_REGIONS,\
                REGION_STR,\
                FIG_OUTPUT_DIR,\
                FIG_FILENAME_CTS,\
                FIG_FILENAME_WC,\
                MODEL,\
                FIG_OBS_DIR,\
                FIG_OBS_FILENAME_CTS,\
                FIG_OBS_FILENAME_WC,\
                OBS,\
                RES,\
                USE_SAME_COLOR_MAP,\
                OVERLAY_OBS_ON_TOP_OF_MODEL_FIG,\
                BULK_TROPOSPHERIC_TEMPERATURE_MEASURE]

data["fit_model_params"]=[ PDF_THRESHOLD,\
                           CWV_RANGE_THRESHOLD,\
                           CP_THRESHOLD,\
                           CWV_FIT_RANGE_MIN,\
                           CWV_FIT_RANGE_MAX,\
                           PRECIP_REF_MODEL,\
                           PRECIP_FIT_MIN_MODEL,\
                           PRECIP_FIT_MAX_MODEL ]

data["fit_obs_params"]=[ PDF_THRESHOLD,\
                         CWV_RANGE_THRESHOLD,\
                         CP_THRESHOLD,\
                         CWV_FIT_RANGE_MIN,\
                         CWV_FIT_RANGE_MAX,\
                         PRECIP_REF_OBS,\
                         PRECIP_FIT_MIN_OBS,\
                         PRECIP_FIT_MAX_OBS ]

fig_params={}

fig_params['f0']=[axes_fontsize,legend_fontsize,marker_size,xtick_pad,figsize1,figsize2]
for i in ['f1','f2','f3','f4','f5','f6']:    
    fig_params[i]=[[xlim1[i],xlim2[i]],[ylim1[i],ylim2[i]],xlabel[i],ylabel[i],xticks[i],yticks[i]]

data["plot_params"]=fig_params

with open(os.environ["WORK_DIR"] + "/convecTransCriticalCollapse_parameters.json", "w") as outfile:
    json.dump(data, outfile)
