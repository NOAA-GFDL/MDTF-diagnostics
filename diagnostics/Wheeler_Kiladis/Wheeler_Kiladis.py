# This file is part of the Wheeler_Kiladis module of the MDTF code package (see LICENSE.txt)

#============================================================
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
#============================================================

import os
import subprocess
import time

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#============================================================
def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

print("COMPUTING THE SPACE-TIME SPECTRA")

#============================================================
# Check data exists and Call NCL code
#============================================================
os.chdir(os.environ["DATADIR"])

#OLR

if os.path.isfile(os.environ["RLUT_VAR_FILE"]):
    os.environ["file_WK"] = os.path.basename(os.environ["RLUT_VAR_FILE"])
    os.environ["MVAR"] = os.environ["rlut_var"]
    os.environ["LEV"] = "sfc"
    os.environ['CESM_VAR'] = 'FLUT'
    print("file of "+os.environ["rlut_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
    generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
else:  
    print("file of "+os.environ["rlut_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#Precipitation

if os.path.isfile(os.environ["PR_VAR_FILE"]):
    os.environ["file_WK"] = os.path.basename(os.environ["PR_VAR_FILE"])
    os.environ["MVAR"] = os.environ["pr_var"]
    os.environ["LEV"] = "sfc"
    os.environ['CESM_VAR'] = 'PRECT'
    print("file of "+os.environ["pr_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
    generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
else:  
    print("file of "+os.environ["pr_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#Omega500

if os.path.isfile(os.environ["OMEGA500_VAR_FILE"]):
    os.environ["file_WK"] = os.path.basename(os.environ["OMEGA500_VAR_FILE"])
    os.environ["MVAR"] = os.environ["omega500_var"]
    os.environ["LEV"] = "500"
    os.environ['CESM_VAR'] = 'OMEGA500'
    print("file of "+os.environ["omega500_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
    generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
else:  
    print("file of "+os.environ["omega500_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#U200

if os.path.isfile(os.environ["U200_VAR_FILE"]):
    os.environ["file_WK"] = os.path.basename(os.environ["U200_VAR_FILE"])
    os.environ["MVAR"] = os.environ["u200_var"]
    os.environ["LEV"] = "200"
    os.environ['CESM_VAR'] = 'U200'
    print("file of "+os.environ["u200_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
    generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
else:  
    print("file of "+os.environ["u200_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#U850

if os.path.isfile(os.environ["U850_VAR_FILE"]):
    os.environ["file_WK"] = os.path.basename(os.environ["U850_VAR_FILE"])
    os.environ["MVAR"] = os.environ["u850_var"]
    os.environ["LEV"] = "850"
    os.environ['CESM_VAR'] = 'U850'
    print("file of "+os.environ["u850_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
    generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
else:  
    print("file of "+os.environ["u850_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")
