# This file is part of the precip_diurnal_cycle module of the MDTF code package (see LICENSE.txt)

#============================================================
# Diurnal Cycle of Precipitation
# Sample code to call NCL from python
# Precipitation diurnal cycle code written by R. B. Neale
#
# This module calculates the local time of fist harmonic of
#  diurnal precipitation as in Gervais et al. (2014), Fig. 9.
#
# Reference:
# Gervais M., J. R. Gyakum, E. Atallah, L. B. Tremblay,
#  and R. B. Neale, 2014:
# How Well Are the Distribution and Extreme Values of Daily 
#  Precipitation over North America Represented in the 
#  Community Climate System Model? A Comparison to Reanalysis, 
#  Satellite, and Gridded Station Data.
# J. Climate, 27, 5219-5239.
# ============================================================

import os
import subprocess
import time

# ============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
# ============================================================


def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0].decode()
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING', e.errno, e.strerror)

    return 0


if os.path.isfile(os.environ["PR_FILE"]):
    print("3 hourly precipitation rate file found")
    print("computing diurnal cycle of precipitation")

# ============================================================
# Call NCL code here
# ============================================================
    print("--------- Starting DIURNAL CYCLE OF PRECIPITATION generate figures----------------------------")
    if True:
        generate_ncl_plots(os.environ["POD_HOME"] + "/pr_diurnal_cycle.ncl")

        generate_ncl_plots(os.environ["POD_HOME"] + "/pr_diurnal_phase.ncl")
    else:
        print("WARNING: For testing purposes, skipping diurnal cycle figure generation")

    print("--------- Finished DIURNAL CYCLE OF PRECIPITATION generate figures----------------------------")

else:
    print("3 hourly precipitation rate file NOT found, skip diurnal cycle of precipitation")            
