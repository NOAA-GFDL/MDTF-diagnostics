# Flow-Dependent, Cross-Timescale Model Diagnostics POD
#
# ================================================================================
#
# Last update: 4/27/2021
#
#   The flow-dependent model diagnostics compares daily atmospheric circulation patterns,
#   or weather types, characteristics in reanalyses and models to analyze misrepresented
#   physical processes related to spatiotemporal systematic errors in those models.
#   Relationships between these biases and climate teleconnections
#   (e.g., SST patterns, ENSO, MJO, etc.) can be explored in different models.
#
# Version and contact info
#
#   - Version/revision information: version 1 (4/27/2021)
#   - Developer/point of contact: Ángel G. Muñoz (agmunoz@iri.columbia.edu) and
#                                 Andrew W. Robertson (awr@iri.columbia.edu)
#   - Other contributors: Drew Resnick (drewr@iri.columbia.edu), James Doss-Gollin
#
# Open source copyright agreement
#
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#
# Functionality
#
#   The currently package consists of following functionalities:
#   (1) Calculation of climatologies and anomalies for the input fields (ClimAnom_func.py)
#   (2) Calculation of weather types spatial patterns (WeatherTypes.py.py)
#   (3) Calculation of weather types temporal characteristics (* to be added soon)
#   (4) Procrustes analysis(* to be added soon)
#   As a module of the MDTF code package, all scripts of this package can be
#   found under mdtf/MDTF_$ver/var_code/flow_dep_diag

#   This diagnostic assumes:
#   (1)the longitude if in range -180,180 for plotting purposes
#   (2) The data has been cropped for a specific region
#   Refer to cropping.py for code to crop your data / shift the grid
#
# Required programming language and libraries
#
#   This diagnostic runs on the most recent version of python3.
#   The required packages are as follows, and all should be the most updated version.
#   Python Libraries used: "netCDF4", "xarray", "numpy", "sklearn",
#                          "cartopy", "matplotlib", "numba", "datetime", "typing"
#
# Required model output variables
#
#   Geopotential height anomalies (units: HPa, daily resolution)
#   Rainfall (units: mm/day, daily resolution)
#   Temperature (units: Celsius, daily resolution)
#
#   This diagnostic assumes the data is structured on a time grid with no leap years.
#   It also assumes each variable is for a single ensemble member.
#
# References
#
#   Muñoz, Á. G., Yang, X., Vecchi, G. A., Robertson, A. W., & Cooke, W. F. (2017):
#       PA Weather-Type-Based Cross-Time-Scale Diagnostic Framework for Coupled Circulation
#       Models. Journal of Climate, 30 (22), 8951–8972, doi:10.1175/JCLI-D-17-0115.1.
#
# ================================================================================

#driver file
import os
import glob

missing_file=0
if len(glob.glob(os.environ["PRECT_FILE"]))==0:
    print("Required Precipitation data missing!")
    missing_file=1
if len(glob.glob(os.environ["Z250_FILE"]))==0:
    print("Required Geopotential height data missing!")
    missing_file=1
if len(glob.glob(os.environ["T250_FILE"]))==0:
    print("Required temperature data missing!")
    missing_file=1

if missing_file==1:
    print("Flow-Dependent, Cross-Timescale Model Diagnostics Package will NOT be executed!")
else:

    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"WeatherTypes.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Flow-Dependent, Cross-Timescale Model Diagnostics (WeatherTypes.py) is NOT Executed as Expected!")
        print("**************************************************")

    print("**************************************************")
    print("Flow-Dependent, Cross-Timescale Model Diagnostics (WeatherTypes.py) Executed!")
    print("**************************************************")
