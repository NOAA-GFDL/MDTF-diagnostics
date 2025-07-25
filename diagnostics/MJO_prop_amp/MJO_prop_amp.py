# This file is part of the MJO_prop_amp module of the MDTF code package (see LICENSE.txt)
# ===============================================================
#   Diagnostic package for MJO propagation and amplitude in GCMs
#   Version 2.1 September 25, 2018. Alex Gonzalez (UCLA, now at IA State) and Xianan Jiang (UCLA)
#   Contributors: M. Zhao (GFDL), E. Maloney (CSU)
#   PI: Xianan Jiang (UCLA)

#   Currently consists of following functionalities:
#    (1) Interpolate model output to regular horizontal grids (2.5 x 2.5 deg) ;
#    (2) Evaluate model skill for MJO propagation based on pattern correlation of rainfall Hovmoller diagrams 
#        following Jiang et al. (2015), and link model MJO propagation skill to model skill in the low-level
#        mean moisture pattern following Jiang (2017) and Gonzalez & Jiang (2017);
#    (3) Evaluate model MJO amplitude and link it to model convective moisture adjustment time scale
#        following Jiang et al. (2016);

#   All scripts of this package can be found under: /diagnostics/MJO_prop_amp 
#    & observational data under: /obs_data/MJO_prop_amp

#   The following Python packages are required: os, subprocess
#   These Python packages are already included in the standard installation

#   The following daily two 3-D (lat-lon-time) model fields and one 4-D (lat-lon-pressure-time) are required:
#    (1) 3-D precipitation rate (units: mm/s = kg/m^2/s)
#    (2) 3-D column water vapor (CWV, or precipitable water vapor; units mm = kg/m^2)
#    (3) 4-D specific humidity (units: g/g)  

#   Reference: 
#    Jiang et al. (2015): Vertical structure and physical processes of the Madden-Julian oscillation:
#       Exploring key model physics in climate simulations. JGR-Atmos, 10.1002/2014JD022375, 4718-4748.
#    Jiang et al. (2016): Convective moisture adjustment time scale as a key factor in regulating
#       model amplitude of the Madden-Julian Oscillation. GRL,43,10,412-10,419.
#    Jiang (2017): Key processes for the eastward propagation of the Madden-Julian Oscillation 
#       based on multimodel simulations. JGR-Atmos, 10.1002/2016JD025955.
#    Gonzalez & Jiang (2017): Winter Mean Lower-Tropospheric Moisture over the Maritime Continent 
#       as a Climate Model Diagnostic Metric for the Propagation of the Madden-Julian Oscillation. GRL.

import os
import subprocess
import time

# ============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
# ============================================================


def generate_ncl_plots(nclPlotFile):
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

# ============================================================
# Call NCL code here
# ============================================================

# create synonyms for env var names to avoid changes to rest of this POD's code


os.environ["file_pr"] = os.environ["PR_FILE"]
os.environ["file_prw"] = os.environ["PRW_FILE"]
os.environ["file_hus"] = os.environ["HUS_FILE"]

print("    ")
print("=======")
print("Diagnostics for MJO propagation and amplitude")
print("Interpolating model data to standard grids ...")
generate_ncl_plots(os.environ["POD_HOME"] + "/m_intp.ncl")
print("Starting diagnostic program ...")
generate_ncl_plots(os.environ["POD_HOME"] + "/m_diag.ncl")
