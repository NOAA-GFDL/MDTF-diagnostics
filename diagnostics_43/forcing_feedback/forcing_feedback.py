# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcing_feedback.py
#
# Forcing Feedback Diagnostic Package
#
# The forcing feedback diagnostic package uses radiative kernels to compute radiative forcing and radiative
# feedback terms.
#
#  Version 1 05-Sept-2023 Ryan Kramer (NOAA/GFDL prev. NASA GSFC/UMBC)
#  PI: Brian Soden (University of Miami; bsoden@rsmas.miami.edu)
#  Current developer: Ryan Kramer (ryan.kramer@noaa.gov)
#
#   This package and the MDTF code package are distributed under the LGPLv3 license
#    (see LICENSE.txt).
#
#
#   As a module of the MDTF code package, all scripts of this package can be found under
#    mdtf/MDTF_$ver/var_code/forcing_feedback**
#   and pre-digested radiative kernels used in the calculations under
#    mdtf/inputdata/obs_data/forcing_feedback
#   (**$ver depends on the actual version of the MDTF code package
#
#   This package is written in Python 3 and requires the following Python packages:
#   os,sys,numpy,xarray,scipy,matplotlib,cartopy,dask
#
#   The following 4-D (lon-lat-pressure levels-time) monthly-mean model fields
#   are required:
#   (1) air temperature (units: K)
#   (2) specific humidity (units: kg/kg)
#
#   The following 3-D (lon-lat-time) monthly-mean model fields are required:
#   (1) surface temperature (units: K)
#   (2) TOA longwave and shortwave radiative flux diagostics (TOA SW upwellling, TOA SW downwelling, etc.)
#       for longwave and shortwave and for all-sky and clear-sky conditions when applicable
#   (3) Surface shortwave radiative flux diagnostics (Surface SW Upwelling, Surface SW downwelling)
#        for all-sky and clear-sky conditions
#
#
##################################
# forcing_feedback
#
# Created By: Ryan J. Kramer, Brian J. Soden
#
#
# This is the main script for the forcing_feedback Toolkit. With some user-specified details
# this Toolkit uses radiative kernels to compute instantaneous radiative forcing and radiative feedbacks
# for a single model. Further details are in the module's documentation at ../doc.
#
##################################

import os

if not os.path.isfile(os.environ["OBS_DATA"] + "/forcing_feedback_kernels.nc"):
    print("Kernel file is missing. POD will not work!")

else:

    try:
        os.system("python " + os.environ["POD_HOME"] + "/" + "forcing_feedback_kernelcalcs.py")
        print('Working Directory is ' + os.environ['WORK_DIR'])
        print('Forcing Feedback POD is executing')
    except RuntimeError as e1:
        print('WARNING', e1.errno, e1.strerror)
        print("**************************************************")
        print("Kernel calculations (forcing_feedback_kernelcalcs.py) are NOT Executing as Expected!")

    try:
        os.system("python " + os.environ["POD_HOME"] + "/" + "forcing_feedback_plot.py")
        print('Generating Forcing Feedback POD plots')
    except RuntimeError as e2:
        print('WARNING', e2.errno, e2.strerror)
        print("**************************************************")
        print("Plotting functions (forcing_feedback_plots.py) are NOT Executing as Expected!")

    print("Last log message by Forcing Feedback POD: finished executing")
