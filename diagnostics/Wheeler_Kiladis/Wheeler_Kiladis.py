# This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)

# ============================================================
# Wheeler-Kiladis Plots
# Sample code to call NCL from python 
#
# This module produces figures of wavenumber-frequency spectra
#  as in Wheeler and Kiladis (1999). 
#
# Reference:
# Wheeler, M. and G.N. Kiladis, 1999: 
# Convectively Coupled Equatorial Waves: Analysis of Clouds 
#  and Temperature in the Wavenumber-Frequency Domain. 
# J. Atmos. Sci., 56, 374-399.
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
        print('NCL routine {0} \n {1}'.format(nclPlotFile, output))
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING', e.errno, e.strerror)

    return 0


print("COMPUTING THE SPACE-TIME SPECTRA")

# ============================================================
# Check data exists and Call NCL code
# ============================================================
os.chdir(os.environ["DATADIR"])  # inputdata

# OLR

varlist = [("u200_var", "U200_FILE"), ("u850_var", "U850_FILE"), ("omega500_var", "OMEGA500_FILE"),
           ("rlut_var", "RLUT_FILE"), ("pr_var", "PR_FILE")]

for var, file_ in varlist:
    print("starting var " + var)
    if os.path.isfile(os.environ[file_]):
        os.environ["file_WK"] = os.environ[file_]
        os.environ["MVAR"] = os.environ[var]
        # print("file of "+os.environ[var]+" for Wheeler-Kiladis plots found, computing wave spectra")
        generate_ncl_plots(os.environ["POD_HOME"] + "/wkSpaceTime_driver.ncl")
    else:
        print("WARNING: file not found (" + os.environ[var] + ") skipping wave spectra computation")
