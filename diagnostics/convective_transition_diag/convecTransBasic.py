# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransBasic.py
#
#  Convective Transition Basic Statistics
#  as part of functionality provided by
#  Convective Transition Diagnostic Package (convective_transition_diag_v1r3.py)
#
#  Version 1 revision 3 13-Nov-2017 Yi-Hung Kuo (UCLA)
#  PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#  Current developer: Yi-Hung Kuo (yhkuo@atmos.ucla.edu)
#  Contributors: K. A. Schiro (UCLA), B. Langenbrunner (UCLA), F. Ahmed (UCLA),
#  C. Martinez (UCLA), C.-C. (Jack) Chen (NCAR)
#
#  This file is part of the Convective Transition Diagnostic Package
#  and the MDTF code package. See LICENSE.txt for the license.
#
#  Computes a set of Convective Transition Statistics as in Kuo et al. (2018).
#  
#  Generates plots of:
#    (1) conditional average precipitation 
#    (2) conditional probability of precipitation
#    (3) probability density function (PDF) of all events
#    (4) PDF of precipitating events 
#    all as a function of column water vapor (CWV) and bulk tropospheric temperature
#   
#  Depends on the following scripts:
#    (1) convecTransBasic_usp_calc.py
#    (2) convecTransBasic_usp_plot.py
#    (3) convecTransBasic_util.py
#    
# Bulk tropospheric temperature measures used include
#  (1) tave: mass-weighted column average temperature
#  (2) qsat_int: column-integrated saturation humidity
# Choose one by setting BULK_TROPOSPHERIC_TEMPERATURE_MEASURE
# in mdtf.py (or convecTransBasic_usp_calc.py)
# Here the column is 1000-200 hPa by default
#
# tave & qsat_int are not standard model output yet, pre-processing calculates these two 
# and saves them in the model output directory (if there is a permission issue,
# change PREPROCESSING_OUTPUT_DIR with related changes, or simply force
# data["SAVE_TAVE_QSAT_INT"]=0, both in convecTransBasic_usp_calc.py)
#
# Defaults for binning choices, etc. that can be altered by user are in:
# convecTransBasic_usp_calc.py
#
# Defaults for plotting choices that can be altered by user are in:
# convecTransBasic_usp_calc_plot.py
# 
# Utility functions are defined in convecTransBasic_util.py
#
# To change regions over which binning computations are done, see
# convecTransBasic_usp_calc.py &
# generate_region_mask in convecTransBasic_util.py
# (and change obs_data/convective_transition_diag/region_0.25x0.25_costal2.5degExcluded.mat)
# ======================================================================
# Import standard Python packages
import os
import json

# Import Python functions specific to Convective Transition Basic Statistics
from convecTransBasic_util import generate_region_mask
from convecTransBasic_util import convecTransBasic_calc_model
from convecTransBasic_util import convecTransBasic_loadAnalyzedData
from convecTransBasic_util import convecTransBasic_plot
print("**************************************************")
print("Excuting Convective Transition Basic Statistics (convecTransBasic.py)......")
print("**************************************************")

# ======================================================================
# Load user-specified parameters (usp) for BINNING and PLOTTING
# This is in the /diagnostics/convective_transition_diag folder under
#  convecTransBasic_usp_calc.py
#  & convecTransBasic_usp_plot.py

print("Load user-specified binning parameters..."),

# Create and read user-specified parameters
os.system("python "+ os.environ["POD_HOME"]+ "/" + "convecTransBasic_usp_calc.py")
with open(os.environ["WORK_DIR"]+"/" + "convecTransBasic_calc_parameters.json") as outfile:
    bin_data = json.load(outfile)
print("...Loaded!")

print("Load user-specified plotting parameters..."),
os.system("python " + os.environ["POD_HOME"] + "/" + "convecTransBasic_usp_plot.py")
with open(os.environ["WORK_DIR"] + "/" + "convecTransBasic_plot_parameters.json") as outfile:
    plot_data = json.load(outfile)
print("...Loaded!")

# ======================================================================
# Binned data, i.e., convective transition statistics binned in specified intervals of 
#  CWV and tropospheric temperature (in terms of tave or qsat_int), are saved to avoid 
#  redoing binning computation every time
# Check if binned data file exists in wkdir/MDTF_casename/ from a previous computation
#  if so, skip binning; otherwise, bin data using model output
#  (see convecTransBasic_usp_calc.py for where the model output locate)

if len(bin_data["bin_output_list"]) == 0 or bin_data["BIN_ANYWAY"]:

    print("Starting binning procedure...")

    if bin_data["PREPROCESS_TA"] == 1:
        print(" Atmospheric temperature pre-processing required")
    if bin_data["SAVE_TAVE_QSAT_INT"] == 1:
        print(" Pre-processed temperature fields ("
              + os.environ["tave_var"] + " & " + os.environ["qsat_int_var"]
              + ") will be saved to " + bin_data["PREPROCESSING_OUTPUT_DIR"] + "/")

    # Load & pre-process region mask
    REGION=generate_region_mask(bin_data["REGION_MASK_DIR"] + "/" + bin_data["REGION_MASK_FILENAME"],
                                bin_data["pr_list"][0], bin_data["LAT_VAR"], bin_data["LON_VAR"])

    # Pre-process temperature (if necessary) & bin & save binned results
    binned_output=convecTransBasic_calc_model(REGION, bin_data["args1"])

else:  # Binned data file exists & BIN_ANYWAY=False
    print("Binned output detected..."),
    binned_output=convecTransBasic_loadAnalyzedData(bin_data["args2"])
    print("...Loaded!")

# ======================================================================
# Plot binning results & save the figure in wkdir/MDTF_casename/.../
convecTransBasic_plot(binned_output, plot_data["plot_params"], plot_data["args3"], plot_data["args4"])

print("**************************************************")
print("Convective Transition Basic Statistics (convecTransBasic.py) Executed!")
print("**************************************************")
