# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransBasic_usp_calc.py
#
#   Called by convecTransBasic.py
#    Provides User-Specified Parameters for Binning and Plotting
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
# Model name
MODEL=os.environ["CASENAME"]#os.environ["model"] # will show up in the figure
# Model output directory
MODEL_OUTPUT_DIR=os.environ["MODEL_OUTPUT_DIR"] # where original model data are located
# Variable Names
PR_VAR=os.environ["pr_var"]
PRW_VAR=os.environ["prw_var"]
TA_VAR=os.environ["ta_var"]
PRES_VAR=os.environ["lev_coord"]
TIME_VAR=os.environ["time_coord"]
LAT_VAR=os.environ["lat_coord"]
LON_VAR=os.environ["lon_coord"]

# ======================================================================
# Region mask directory & filename
REGION_MASK_DIR = os.environ["OBS_DATA"]
REGION_MASK_FILENAME = "region_0.25x0.25_costal2.5degExcluded.mat"
# Number of regions
#  Use grids with 1<=region<=NUMBER_OF_REGIONS in the mask
NUMBER_OF_REGIONS = 4  # default: 4
# Region names
REGION_STR = ["WPac", "EPac", "Atl", "Ind"]

# ======================================================================
# Directory for saving pre-processed temperature fields
# tave [K]: Mass-weighted column average temperature
# qsat_int [mm]: Column-integrated saturation specific humidity
# USER MUST HAVE WRITE PERMISSION
# If one changes PREPROCESSING_OUTPUT_DIR, one must also modify data["tave_list"]
# & data["qsat_int_list"] below by replacing MODEL_OUTPUT_DIR with
# PREPROCESSING_OUTPUT_DIR
PREPROCESSING_OUTPUT_DIR = os.environ["DATADIR"]
TAVE_VAR = os.environ["tave_var"]
QSAT_INT_VAR = os.environ["qsat_int_var"]
# Number of time-steps in Temperature-preprocessing
# Default: 1000 (use smaller numbers for limited memory)
time_idx_delta = 1000
# Use 1:tave, or 2:qsat_int as Bulk Tropospheric Temperature Measure 
BULK_TROPOSPHERIC_TEMPERATURE_MEASURE = int(os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"])

# ======================================================================
# Directory & Filename for saving binned results (netCDF4)
#  tave or qsat_int will be appended to BIN_OUTPUT_FILENAME
BIN_OUTPUT_DIR = os.environ["WORK_DIR"] + "/model/netCDF"
BIN_OUTPUT_FILENAME = os.environ["CASENAME"] + ".convecTransBasic"

# ======================================================================
# Re-do binning even if binned data file detected (default: True)
BIN_ANYWAY = True

# ======================================================================
# Column Water Vapor (CWV in mm) range & bin-width
#  CWV bin centers are integral multiples of cwv_bin_width
CWV_BIN_WIDTH = 0.3  # default=0.3 (following satellite retrieval product)
CWV_RANGE_MAX = 90.0  # default=90 (75 for satellite retrieval product)

# Mass-weighted Column Average Temperature tave [K] range & bin-width
#  with 1K increment and integral bin centers
T_RANGE_MIN = 260.0
T_RANGE_MAX = 280.0
T_BIN_WIDTH = 1.0

# Column-integrated Saturation Specific Humidity qsat_int [mm] range & bin-width
# with bin centers = Q_RANGE_MIN + integer*Q_BIN_WIDTH
# Satellite retrieval suggests T_BIN_WIDTH=1 
# is approximately equivalent to Q_BIN_WIDTH=4.8
Q_RANGE_MIN = 16.0
Q_RANGE_MAX = 106.0
Q_BIN_WIDTH = 4.5

# Define column [hPa] (default: 1000-200 hPa)
# One can re-define column by changing p_lev_bottom & p_lev_top,
# but one must also delete/re-name existing tave & qsat_int files
# since the default tave & qsat_int filenames do not contain conlumn info
p_lev_bottom = 1000
p_lev_top = 200
# If model pressure levels are close to p_lev_bottom and/or p_lev_top
# (within dp-hPa neighborhood), use model level(s) to define column instead
dp = 1.0

# Threshold value defining precipitating events [mm/hr]
PRECIP_THRESHOLD = 0.25

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
# ======================================================================
# DO NOT MODIFY CODE BELOW UNLESS
# YOU KNOW WHAT YOU ARE DOING
# ======================================================================
data = {}

data["MODEL"] = MODEL
data["MODEL_OUTPUT_DIR"] = MODEL_OUTPUT_DIR
data["PREPROCESSING_OUTPUT_DIR"] = PREPROCESSING_OUTPUT_DIR

data["REGION_MASK_DIR"] = REGION_MASK_DIR
data["REGION_MASK_FILENAME"] = REGION_MASK_FILENAME

data["NUMBER_OF_REGIONS"] = NUMBER_OF_REGIONS
data["REGION_STR"] = REGION_STR

data["TIME_VAR"] = TIME_VAR
data["LAT_VAR"] = LAT_VAR
data["LON_VAR"] = LON_VAR
data["TAVE_VAR"] = TAVE_VAR
data["QSAT_INT_VAR"] = QSAT_INT_VAR
data["PRES_VAR"] = PRES_VAR
data["time_idx_delta"] = time_idx_delta
data["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] = BULK_TROPOSPHERIC_TEMPERATURE_MEASURE

data["BIN_OUTPUT_DIR"] = BIN_OUTPUT_DIR
data["BIN_OUTPUT_FILENAME"] = BIN_OUTPUT_FILENAME

if BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 1:
    data["BIN_OUTPUT_FILENAME"] += "_" + TAVE_VAR
    data["TEMP_VAR"] = TAVE_VAR
elif BULK_TROPOSPHERIC_TEMPERATURE_MEASURE == 2:
    data["BIN_OUTPUT_FILENAME"] += "_" + QSAT_INT_VAR
    data["TEMP_VAR"] = QSAT_INT_VAR

data["BIN_ANYWAY"] = BIN_ANYWAY
    
data["CWV_BIN_WIDTH"] = CWV_BIN_WIDTH
data["CWV_RANGE_MAX"] = CWV_RANGE_MAX

data["T_RANGE_MIN"] = T_RANGE_MIN
data["T_RANGE_MAX"] = T_RANGE_MAX
data["T_BIN_WIDTH"] = T_BIN_WIDTH

data["Q_RANGE_MIN"] = Q_RANGE_MIN
data["Q_RANGE_MAX"] = Q_RANGE_MAX
data["Q_BIN_WIDTH"] = Q_BIN_WIDTH

data["p_lev_bottom"] = p_lev_bottom
data["p_lev_top"] = p_lev_top
data["dp"] = dp

data["PRECIP_THRESHOLD"] = PRECIP_THRESHOLD

# List binned data file (with filename corresponding to casename)
data["bin_output_list"] = sorted(glob.glob(data["BIN_OUTPUT_DIR"] + "/" + data["BIN_OUTPUT_FILENAME"] + ".nc"))

# List available netCDF files
# Assumes that the corresponding files in each list
# have the same spatial/temporal coverage/resolution
pr_list = sorted(glob.glob(os.environ["pr_file"]))
prw_list = sorted(glob.glob(os.environ["prw_file"]))
ta_list = sorted(glob.glob(os.environ["ta_file"]))

data["pr_list"] = pr_list
data["prw_list"] = prw_list
data["ta_list"] = ta_list

# Check for pre-processed tave & qsat_int data
data["tave_list"] = sorted(glob.glob(os.environ["tave_file"]))
data["qsat_int_list"] = sorted(glob.glob(os.environ["qsat_int_file"]))

if len(data["tave_list"]) == 0 or len(data["qsat_int_list"]) == 0:
    data["PREPROCESS_TA"] = 1
else:
    data["PREPROCESS_TA"] = 0
# Save pre-processed tave & qsat_int or not; default=0 (don't save)
data["SAVE_TAVE_QSAT_INT"] = int(os.environ["SAVE_TAVE_QSAT_INT"])
if data["PREPROCESS_TA"] != data["SAVE_TAVE_QSAT_INT"]:
    print("Pre-processing of air temperature (ta) required to compute weighted column averages,")
    print(" but the pre-processed results will not be saved as intermediate output.")
    print("To save the pre-processed results as NetCDF files for re-use (write permission required),")
    print(" go to settings.jsonc, and changes SAVE_TAVE_QSAT_INT to 1.")

# Taking care of function arguments for binning
data["args1"]=[
    BULK_TROPOSPHERIC_TEMPERATURE_MEASURE,
    CWV_BIN_WIDTH,
    CWV_RANGE_MAX,
    T_RANGE_MIN,
    T_RANGE_MAX,
    T_BIN_WIDTH,
    Q_RANGE_MIN,
    Q_RANGE_MAX,
    Q_BIN_WIDTH,
    NUMBER_OF_REGIONS,
    pr_list,
    PR_VAR,
    prw_list,
    PRW_VAR,
    data["PREPROCESS_TA"],
    MODEL_OUTPUT_DIR,
    data["qsat_int_list"],
    QSAT_INT_VAR,
    data["tave_list"],
    TAVE_VAR,
    ta_list,
    TA_VAR,
    PRES_VAR,
    MODEL,
    p_lev_bottom,
    p_lev_top,
    dp,
    time_idx_delta,
    data["SAVE_TAVE_QSAT_INT"],
    PREPROCESSING_OUTPUT_DIR,
    PRECIP_THRESHOLD,
    data["BIN_OUTPUT_DIR"],
    data["BIN_OUTPUT_FILENAME"],
    TIME_VAR,
    LAT_VAR,
    LON_VAR
]

data["args2"] = [
    data["bin_output_list"],
    TAVE_VAR,
    QSAT_INT_VAR,
    BULK_TROPOSPHERIC_TEMPERATURE_MEASURE
]

with open(os.environ["WORK_DIR"] + "/" + "convecTransBasic_calc_parameters.json", "w") as outfile:
    json.dump(data, outfile)
