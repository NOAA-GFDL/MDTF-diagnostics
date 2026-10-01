# This file is part of the convective_transition_diag module of the MDTF code package (see LICENSE.txt)

# ======================================================================
# convecTransCriticalCollapse.py
#
#   Convective Transition Critical Collapse
#    as part of functionality provided by 
#    Convective Transiton Diagnostic Package (convective_transition_diag_v1r2.py)
#
#   Version 1 revision 3 3-Nov-2017 Yi-Hung Kuo (UCLA)
#   Contributors: K. A. Schiro (UCLA), B. Langenbrunner (UCLA), F. Ahmed (UCLA), 
#    C. Martinez (UCLA), C.-C. (Jack) Chen (NCAR)
#   PI: J. David Neelin (UCLA)
#
#   Computes Citical CWV for Convective Transition Statistics following 
#    Kuo et al. (2017a, 2017b), similar to Sahany et al. (2012)
#  
#   Generates plots of:
#    (1) critical column water vapor w_c
#    (2) ratio of w_c to column-integrated saturation specific humidity qsat_int
#    both as a function of bulk tropospheric temperature,
#   and
#    (3) conditional average precipitation 
#    (4) conditional probability of precipitation
#    (5) probability density function (PDF) of all events
#    (6) PDF of precipitating events 
#    all as a function of column water vapor (CWV) relative to w_c 
#    and bulk tropospheric temperature
#
#   Depends on the following scripts:
#    (1) convecTransCriticalCollapse_usp.py
#    (2) convecTransCriticalCollapse_util.py
#
#   Depends on the output file from 
#    Convective Transition Basic Statistics (convecTransBasic.py) function
#
# Critical CWV w_c is defined to be the CWV value at which the asymptote to
#  the conditional average precipitation curve intersects with the CWV-axis
#  (i.e., precip rate=0)
# 
# The asymptote is found/approximated by fitting the segment of the 
#  conditional average precipitation curve with precip rate in the range
#  specified by PRECIP_FIT_MIN & PRECIP_FIT_MAX (appended by _MODEL or _OBS)
#  in convecTransCriticalCollapse_usp.py
#  (hence the procedure of finding w_c is referred to as Fitting)
#
# For the most probable temperature bins in the tropics 
#  OBS (Reanalysis temperature & TRMM CWV/precip retrievals) suggests that
#  shifting CWV by a temperature-dependent amount (e.g., w_c) collapses
#  the statistics (conditional average precip, conditional probability,
#  & PDFs near or above Critical CWV)
#  This observation is adopted as an working assumption for Fitting
#
# The Fitting is done in 3 steps:
#  (1) For each temperature, find the Reference CWV w_r at which 
#   the conditional average precip equals PRECIP_REF
#   (appended by _MODEL or _OBS, in convecTransCriticalCollapse_usp.py)
#  (2) Shift conditional average precip curves by w_r, then calculate
#   the "average" conditional average precip for the 3 most probable
#   temperature, and identify the segment with precip rate between
#   PRECIP_FIT_MIN & PRECIP_FIT_MAX
#  (3) Fit the segment to find the intersection with the (CWV-w_r)-axis
#   and correct w_r accordingly to find w_c
#
# Default parameters for Fitting & Plotting can be found in 
#  convecTransCriticalCollapse_usp.py
#
# For details of Fitting procedure, see 
#  convecTransCriticalCollapse_usp.py (search "FITTING-REQUIRED PARAMETERS")
#  & convecTransCriticalCollapse_fitCritical (in convecTransCriticalCollapse_util.py)
#  & Kuo et al. (2017a, 2017b)
#
# Parameters in convecTransCriticalCollapse_usp.py should be consistent with
#  those in convecTransBasic_usp_calc.py & convecTransBasic_usp_plot.py
#  e.g., BIN_OUTPUT_DIR & BIN_OUTPUT_FILENAME
# 
# OPEN SOURCE COPYRIGHT Agreement TBA
# ======================================================================
# Import standard Python packages
import os
import json

# Import Python functions specific to Convective Transition Thermodynamic Critical
from convecTransCriticalCollapse_util import convecTransCriticalCollapse_loadAnalyzedData
from convecTransCriticalCollapse_util import convecTransCriticalCollapse_fitCritical
from convecTransCriticalCollapse_util import convecTransCriticalCollapse_plot
print("**************************************************")
print("Excuting Convective Transition Critical Collapse (convecTransCriticalCollapse.py)......")
print("**************************************************")

# ======================================================================
# Load user-specified parameters (usp) for FITTING and PLOTTING
# This is in the diagnostics/convective_transition_diag folder under
#  convecTransCriticalCollapse_usp.py
print("Load user-specified binning parameters..."),

# Create and read user-specified parameters
os.system("python "+os.environ["POD_HOME"]+"/convecTransCriticalCollapse_usp.py")
with open(os.environ["WORK_DIR"]+"/convecTransCriticalCollapse_parameters.json") as outfile:
    params_data=json.load(outfile)
print("...Loaded!")

# ======================================================================
# Check if binned MODEL data from convecTransBasic.py 
#  exists in wkdir/casename/ from a previous computation
if (len(params_data["bin_output_list"])!=0): # binned MODEL data exists

    print("Binned output detected...")
    binned_model=convecTransCriticalCollapse_loadAnalyzedData(params_data["args1"])
    binned_obs=convecTransCriticalCollapse_loadAnalyzedData(params_data["args2"])
    print("Binned output Loaded!")

    print("Starting fitting procedure..."),  
    plot_model=convecTransCriticalCollapse_fitCritical(binned_model,params_data["fit_model_params"])
    plot_obs=convecTransCriticalCollapse_fitCritical(binned_obs,params_data["fit_obs_params"])
    print("...Fitted!")

    # ======================================================================
    # Plot binning results & save the figure in wkdir/casename/.../   
    convecTransCriticalCollapse_plot(binned_model,plot_model,\
                                 binned_obs,plot_obs,\
                                 params_data["args3"],params_data["plot_params"])
    print("Plotting Complete!") 

else: 
    print("Binned output from convecTransBasic.py does not exists!")
    print("   If you are certain that binned output exists, "\
          +"please double-check convecTransCriticalCollapse_usp.py, "\
          +"making sure that it is consistent with "\
          +"convecTransBasic_usp_calc.py & convecTransBasic_usp_plot.py!")

print("**************************************************")
print("Convective Transition Thermodynamic Critical Collapse (convecTransCriticalCollapse.py) Executed!")
print("**************************************************")
