# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransBasic_usp_plot.py
#
#   Called by convecTransBasic.py
#    Provides User-Specified Parameters for Plotting
#
#   This file is part of the Convective Transition Diagnostic Package 
#    and the MDTF code package. See LICENSE.txt for the license.
#
import json
import os
import glob

with open(os.environ["WORK_DIR"] + "/" + "convecTransBasic_calc_parameters.json") as outfile:
    bin_data=json.load(outfile)
    
# ======================================================================
# START USER SPECIFIED SECTION
# ======================================================================
# Don't plot bins with PDF<PDF_THRESHOLD
PDF_THRESHOLD = 1e-5  # default: 1e-5

# Don't plot tave/qsat_int with narrow cwv range (< CWV_RANGE_THRESHOLD mm)
CWV_RANGE_THRESHOLD = 18  # default: 18

# Don't plot tave/qsat_int with low conditional probability of precipitation
CP_THRESHOLD = 0.2

FIG_OUTPUT_DIR = os.environ["WORK_DIR"] + "/model/PS"
FIG_OUTPUT_FILENAME = bin_data["BIN_OUTPUT_FILENAME"] + ".eps"

# Binned data filename & figure directory/filename for OBS (default: R2TMIv7) ##
OBS = "Reanalysis-2 + TMIv7r1"  # will show up in the MODEL figure
REGION_STR_OBS = ["WPac", "EPac", "Atl", "Ind"]
bin_obs_list = sorted(glob.glob(os.environ["OBS_DATA"]
                                + "/convecTransBasic_R2TMIv7r1_200206_201405_res="
                                + os.environ["RES"] + "_fillNrCWV_"
                                + bin_data["TEMP_VAR"] + ".nc"))
FIG_OBS_DIR = os.environ["WORK_DIR"] + "/obs/PS"
FIG_OBS_FILENAME = ("convecTransBasic_R2TMIv7r1_200206_201405_res="
                    + os.environ["RES"] + "_fillNrCWV_" + bin_data["TEMP_VAR"] + ".eps")

# Force the OBS & MODEL figures to use the same color map
# Will be ignored if binned OBS data does not exist
# Set to False if COLUMN is defined differently for OBS & MODEL
USE_SAME_COLOR_MAP = True

# Plot OBS results on top of MODEL results for comparison
# Will be ignored if binned OBS data does not exist
# If REGION MASK and/or COLUMN DEFINITION are changed
# set to False unless the corresponding binned OBS data exists
OVERLAY_OBS_ON_TOP_OF_MODEL_FIG = True

# Plot formatting ##
axes_fontsize = 12  # size of font in all plots
legend_fontsize = 9
marker_size = 40  # size of markers in scatter plots
xtick_pad = 10  # padding between x tick labels and actual plot
figsize1 = 14  # figure size set by figsize=(figsize1,figsize2)
figsize2 = 12 

# There are four figures in level 1 diagnostics ###
# Choose the plot parameters for each figure below ###
xlim1 = {}
xlim2 = {}

ylim1 = {}
ylim2 = {}

xlabel = {}
ylabel = {}

xticks = {}
yticks = {}

# ==========================================
# Figure 1 : Precip vs. CWV #########
# =========================================
xlim1['f1'] = 10
xlim2['f1'] = 80

ylim1['f1'] = 0
ylim2['f1'] = 8

# Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f1'] = "CWV (mm)"
ylabel['f1'] = "Precip (mm hr$^-$$^1$)"

# Enter ticks as lists ##
# Note: this option overrides axes limit options above ##
xticks['f1'] = [10, 20, 30, 40, 50, 60, 70, 80]
yticks['f1'] = [0, 1, 2, 3, 4, 5, 6, 7, 8]

# ========================================================
# Figure 2 : Probability of precip vs. CWV #########
# ========================================================
xlim1['f2'] = 10
xlim2['f2'] = 80

ylim1['f2'] = 0
ylim2['f2'] = 1

# Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f2'] = "CWV (mm)"
ylabel['f2'] = "Probability of Precip"

# Enter ticks as lists ##
# Note: this option overrides axes limit options above ##
xticks['f2'] = [10, 20, 30, 40, 50, 60, 70, 80]
yticks['f2'] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

# ==============================================
# ##### Figure 3 : Total PDF vs. CWV #########
# ==============================================
xlim1['f3'] = 10
xlim2['f3'] = 80

ylim1['f3'] = 1e-5
ylim2['f3'] = 5e-2

#  Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f3'] = "CWV (mm)"
ylabel['f3'] = "PDF (mm$^-$$^1$)"

# Enter ticks as lists ##
# Note: this option overrides axes limit options above ##
xticks['f3'] = [10, 20, 30, 40, 50, 60, 70, 80]
yticks['f3'] = []

# ====================================================
# ##### Figure 4 : Precipitating PDF vs. CWV #########
# ====================================================
xlim1['f4'] = 10
xlim2['f4'] = 80

ylim1['f4'] = 1e-5
ylim2['f4'] = 5e-2

# Enter labels as strings; Latex mathtype is allowed within $...$ ##
xlabel['f4'] = "CWV (mm)"
ylabel['f4'] = "PDF (mm$^-$$^1$)"

# Enter ticks as lists ##
# Note: this option overrides axes limit options above ##
xticks['f4'] = [10, 20, 30, 40, 50, 60, 70, 80]
yticks['f4'] = []

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
# ======================================================================
# DO NOT MODIFY CODE BELOW UNLESS
# YOU KNOW WHAT YOU ARE DOING
# ======================================================================
data = {}

data["PDF_THRESHOLD"] = PDF_THRESHOLD

data["CWV_RANGE_THRESHOLD"] = CWV_RANGE_THRESHOLD

data["CP_THRESHOLD"] = CP_THRESHOLD

data["FIG_OUTPUT_DIR"] = FIG_OUTPUT_DIR
data["FIG_OUTPUT_FILENAME"] = FIG_OUTPUT_FILENAME

data["FIG_OBS_FILENAME"] = FIG_OBS_FILENAME

data["args3"] = [bin_obs_list,
                 bin_data["TAVE_VAR"],
                 bin_data["QSAT_INT_VAR"],
                 bin_data["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"]
                 ]

data["args4"] = [ bin_data["CWV_BIN_WIDTH"], PDF_THRESHOLD, CWV_RANGE_THRESHOLD,
                  CP_THRESHOLD, bin_data["MODEL"], bin_data["REGION_STR"], bin_data["NUMBER_OF_REGIONS"],
                  bin_data["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"], bin_data["PRECIP_THRESHOLD"],
                  FIG_OUTPUT_DIR, FIG_OUTPUT_FILENAME,
                  OBS, os.environ["RES"], REGION_STR_OBS, FIG_OBS_DIR, FIG_OBS_FILENAME,
                  USE_SAME_COLOR_MAP, OVERLAY_OBS_ON_TOP_OF_MODEL_FIG
                  ]

fig_params = {}

fig_params['f0'] = [axes_fontsize, legend_fontsize, marker_size, xtick_pad, figsize1, figsize2]

for i in ['f1', 'f2', 'f3', 'f4']:
    fig_params[i] = [[xlim1[i], xlim2[i]], [ylim1[i], ylim2[i]], xlabel[i], ylabel[i], xticks[i], yticks[i]]
                
data["plot_params"] = fig_params

with open(os.environ["WORK_DIR"] + "/" + "convecTransBasic_plot_parameters.json", "w") as outfile:
    json.dump(data, outfile)
