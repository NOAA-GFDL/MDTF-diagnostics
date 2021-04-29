# ======================================================================
# NOAA Model Diagnotics Task Force (MDTF) Diagnostic Driver
#
# This release the following Python modules: 
#     os, glob, json, dataset, numpy, scipy, matplotlib, 
#     networkx, warnings, numba, netcdf4, xarrays
#
# This package and the MDTF code package are distributed under the LGPLv3 license 
#        (see LICENSE.txt).
#   updated 2021-01-20
# ======================================================================
import os
import sys
import subprocess
import os.path

# ======================================================================
# ======================================================================
# ======================================================================`

print( "Starting ENSO_RWS.py ") 


os.environ["ENSO_RWS_WKDIR"] = os.environ["WK_DIR"]

#DRB: unfortunately these don't get copied to namelist_save, which means
#debugging requires starting from this script. To add them here requires
#adding the POD_HOME/util path (easy, see mdtf.py) and getting the envvars
#dict here, but currently the file is written before the pods are called.

# ==================================================================================================

#### 1. LEVEL_01
print("=================================================================")
print(" Scripts is going to calculate ENSO composites of simple variables    ")
print("=================================================================")

print("=================================================================")
print(" General information is in README_general.docx/README_general.pdf files under")
print("  ~/diagnostics/ENSO_RWS                                             ")
print("=================================================================")

print("=================================================================")
print(" The LEVEL_01 routine requires the following monthly variables in the input:  ")
print("  Zg - geopotential height [m]        ")
print("  U  - U wind [m/s], V - V wind [m/s] ")
print("  T  - temperature [K]                ")
print("  OMEGA  - vertical velocity [Pa/s]   ")
print("  TS   - skin surface temperature [K] ")
print("  PR   - precipitation rate [kg/m2/s] ")
print("=================================================================")


print("=================================================================")
print(" More detailed information regarding the LEVEL_01 module is in  ")
print(" README_LEVEL_01.docx/README_LEVEL_01.pdf files under ~/diagnostics/ENSO_RWS/LEVEL_01/")
print("=================================================================")
       
###  
print("=================================================================")
print(" Starting Observational LEVEL_01 module                         ")
os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/check_input_files_OBS.py")
print("        Finished check_input_files_OBS.py")
os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/get_directories_OBS.py")
print("        Finished get_directories_OBS.py")

os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/get_directories.py")
print("        Finished get_directories.py")

os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/check_input_files.py")
print("        Finished check_input_files.py")

os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/process_data.py")
print("        Finished check_input_files.py")

os.system("python "+os.environ["POD_HOME"]+"/LEVEL_01/LEVEL_01.py")
print("        Finished LEVEL_01.py")
print(" Finished LEVEL_01 module                         ")
print("=================================================================")

###       copy the banner file : mdtf_diag_banner.png to "ENSO_RWS_WKDIR" needed by 
###                             individual component html files
file_src  = os.environ["POD_HOME"]+"/mdtf_diag_banner.png"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/mdtf_diag_banner.png"
if os.path.isfile( file_dest):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)

file_src  = os.environ["POD_HOME"]+"/ENSO_RWS.html"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/ENSO_RWS.html"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)

file_src  = os.environ["POD_HOME"]+"/doc/ENSO_RWS.pdf"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/ENSO_RWS.pdf"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)

print("=================================================================")
print("                         LEVEL_01 FINISHED                     ")
print("=================================================================")
#except OSError as e:
#    print('WARNING',e.errno,e.strerror)
#    print("LEVEL_01 is NOT Executed as Expected!")

# ==================================================================================================
# 2. LEVEL_02
#    
# ==================================================================================================
print("=================================================================")
print(" Scripts is going to calculate RWS terms based on results from LEVEL_01 ")
print("=================================================================")
print("=================================================================")
os.system("python "+os.environ["POD_HOME"]+"/LEVEL_02/LEVEL_02.py")
print("        Finished LEVEL_02.py")
print(" Finished LEVEL_02 module                         ")
print("=================================================================")

# ==================================================================================================
# 3. LEVEL_03
#   
# ==================================================================================================
print("=================================================================")
print(" Scripts is going to calculate expanded set of RWS terms based on results from LEVEL_01 ")
print("=================================================================")
print("=================================================================")
os.system("python "+os.environ["POD_HOME"]+"/LEVEL_03/LEVEL_03.py")
print("        Finished LEVEL_03.py")
print(" Finished LEVEL_03 module                         ")
print("=================================================================")
print("========================== END =================================")
# 4. LEVEL_04
#
# ==================================================================================================
print("=================================================================")
print(" Scripts is going to calculate expanded set of RWS terms based on results from LEVEL_01 ")
print("=================================================================")
print("=================================================================")
os.system("python "+os.environ["POD_HOME"]+"/LEVEL_04/LEVEL_04.py")
print("        Finished LEVEL_04.py")
print(" Finished LEVEL_04 module                         ")
print("=================================================================")
print("========================== END =================================")


