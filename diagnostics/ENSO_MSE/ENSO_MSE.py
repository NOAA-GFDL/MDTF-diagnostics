# ======================================================================
# NOAA Model Diagnotics Task Force (MDTF) Diagnostic Driver
#
# This release the following Python modules:
#     os, glob, json, dataset, numpy, scipy, matplotlib,
#     networkx, warnings, numba, netcdf4
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
# set ENSO_MSE switches  from  ../mdtf.py
# ======================================================================`

print( "Starting ENSO_MSE.py ")

os.environ["ENSO_MSE_WKDIR"] = os.environ["WK_DIR"]

# TODO remove the ENSO module environment switch definitions after framework
# pod_env_vars issue is fixed
os.environ["ENSO_OBS"] = "1"
os.environ["ENSO_COMPOSITE"] = "1"
os.environ["ENSO_MSE"] = "1"
os.environ["ENSO_MSE_VAR"] = "1"
os.environ["ENSO_SCATTER"] = "1"

os.environ["slon1"] = "160"
os.environ["slon2"] = "200"
os.environ["slat1"] = "-10"
os.environ["slat2"] = "5"

# Subpackage control variables optionally set in namelist eg. VAR ENSO_COMPOSITE 1
# nb. OBS isn't really a subpackage but is a switch used by all subpackages
subpackages = ["OBS","COMPOSITE","MSE","MSE_VAR","SCATTER"]
subpack_default = "1"  #Run all subpackage unless envvars are set not to

for subpack in subpackages:
    os.environ["ENSO_"+subpack] = os.environ.get("ENSO_"+subpack,subpack_default)
    os.environ["ENSO_MSE_WKDIR_"+subpack] = os.environ["ENSO_MSE_WKDIR"]+"/"+subpack
    print(subpack, os.environ["ENSO_"+subpack])
    if os.environ["ENSO_"+subpack] == "1":
        print(" ENSO_MSE subpackage ENSO_"+subpack+" active, output will be in " + os.environ["ENSO_MSE_WKDIR_"+subpack])
    else:
        print(" ENSO_MSE subpackage ENSO_"+subpack+" off. Turn on by adding line to namelist input: VAR ENSO_"+subpack+" 1 ")


#DRB: unfortunately these don't get copied to namelist_save, which means
#debugging requires starting from this script. To add them here requires
#adding the POD_HOME/util path (easy, see mdtf.py) and getting the envvars
#dict here, but currently the file is written before the pods are called.

# ==================================================================================================

#### 1.  COMPOSITE
if os.environ["ENSO_COMPOSITE"] == "1":
    try:
        print("=================================================================")
        print(" Scripts is going to calculate composites of simple variables    ")
        print("=================================================================")

        print("=================================================================")
        print(" General information is in README_general.docx/README_general.pdf files under")
        print("  ~/diagnostics/ENSO_MSE                                              ")
        print("=================================================================")

        print("=================================================================")
        print(" The COMPOSITE routine requires the following monthly variables in the input:  ")
        print("  Zg - geopotential height [m]        ")
        print("  U  - U wind [m/s], V - V wind [m/s] ")
        print("  T  - temperature [K]                ")
        print("  Q  - specific humidity [kg/kg]      ")
        print("  OMEGA  - vertical velocity [Pa/s]   ")
        print("  TS   - skin surface temperature [K] ")
        print("  PR   - precipitation rate [kg/m2/s] ")
        print("  TS   - skin surface temperature [K] ")
        print("  PR   - precipitation rate [kg/m2/s] ")
        print("  SHF  - surface sensible heat flux [W/m2] ")
        print("  LHF  - surface latent heat flux [W/m2]  ")
        print("  SW   - shortwave radiative fluxes [W/m2]  as follows: ")
        print("         RSUS - surface SW up   ")
        print("         RSDS - surface SW down ")
        print("         RSDT - TOA incoming SW ")
        print("         RSUT - TOA outgoing SW ")
        print("  LW   - longwave radiative fluxes [W/m2]  as follows: ")
        print("         RLUS - surface LW up ")
        print("         RLDS - surface LW down ")
        print("         RLUT - TOA outgoing LW ")
        print("=================================================================")


        print("=================================================================")
        print(" More detailed information regarding the COMPOSITE module is in  ")
        print(" README_LEVEL_01.docx/README_LEVEL_01.pdf files under ~/diagnostics/ENSO_MSE/COMPOSITE/")
        print("=================================================================")

###  set if to run Observational Preprocessing :
        if os.environ["ENSO_OBS"] == "1":
            print("=================================================================")
            print(" Starting Observational COMPOSITE module                         ")
            os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/check_input_files_OBS.py")
            print("        Finished check_input_files_OBS.py")
            os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/get_directories_OBS.py")
            print("        Finished get_directories_OBS.py")
            os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/COMPOSITE_OBS.py")
            print("        Finished COMPOSITE_OBS.py")
            print(" Finished Observational COMPOSITE module                         ")
            print("=================================================================")

###  check for model input dat
        os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/check_input_files.py")

        os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/get_directories.py")
        os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/preprocess.py")
        os.system("python "+os.environ["POD_HOME"]+"/COMPOSITE/COMPOSITE.py")
###       copy the banner file : mdtf_diag_banner.png to "ENSO_MSE_WKDIR" needed by
###                             individual component html files
        file_src  = os.environ["POD_HOME"]+"/mdtf_diag_banner.png"
        file_dest = os.environ["ENSO_MSE_WKDIR"]+"/mdtf_diag_banner.png"
        if os.path.isfile( file_dest ):
            os.system("rm -f "+file_dest)
            os.system("cp "+file_src+" "+file_dest)
        file_src  = os.environ["POD_HOME"]+"/ENSO_MSE.html"
        file_dest = os.environ["ENSO_MSE_WKDIR"]+"/ENSO_MSE.html"
        if os.path.isfile( file_dest ):
            os.system("rm -f "+file_dest)
            os.system("cp "+file_src+" "+file_dest)

        file_src  = os.environ["POD_HOME"]+"/ENSO_MSE.pdf"
        file_dest = os.environ["ENSO_MSE_WKDIR"]+"/ENSO_MSE.pdf"
        if os.path.isfile( file_dest ):
            os.system("rm -f "+file_dest)
        os.system("cp "+file_src+" "+file_dest)

        print("=================================================================")
        print("                         COMPOSITES FINISHED                     ")
        print("=================================================================")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("COMPOSITE is NOT Executed as Expected!")


# ==================================================================================================
# 2. MSE
#    getting Moist Static Energy variables  + Composites
# ==================================================================================================
if os.environ["ENSO_MSE"] == "1":
    try:
        print("=================================================================")
        print(" Scripts is going to calculate Moist Static Energy compoments    ")
        print(" The routine requires data  input from COMPOSITE routine         ")
        print("=================================================================")

        print("=================================================================")
        print(" More detailed information regarding the MSE module is in        ")
        print(" README_LEVEL_02.docx/README_LEVEL_02.pdf  files under           ")
        print(" ~/diagnostics/ENSO_MSE/MSE/                                        ")
        print("=================================================================")
        if os.environ["ENSO_OBS"] == "1":
            print("=================================================================")
            print("   Starting Observational Moist Static Energy calculations       ")
            print("=================================================================")
            os.system("python "+os.environ["POD_HOME"]+"/MSE/get_directories_OBS.py")
            os.system("python "+os.environ["POD_HOME"]+"/MSE/check_input_files_OBS.py")
            os.system("python "+os.environ["POD_HOME"]+"/MSE/MSE_OBS.py")

        os.system("python "+os.environ["POD_HOME"]+"/MSE/get_directories.py")
        os.system("python "+os.environ["POD_HOME"]+"/MSE/check_input_files.py")
        os.system("python "+os.environ["POD_HOME"]+"/MSE/MSE.py")

        print("=================================================================")
        print("         Moist Static Energy calculations  FINISHED              ")
        print("=================================================================")

    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("MSE is NOT Executed as Expected!")

# 3. MSE variances
#    getting Moist Static Energy variable VARIANCES
# ==================================================================================================
if os.environ["ENSO_MSE_VAR"] == "1":
    try:
        print("=================================================================")
        print(" Scripts is going to calculate Moist Static Energy Variances     ")
        print(" The routine requires data  input from COMPOSITE and MSE routines")
        print("=================================================================")

        print("=================================================================")
        print(" More detailed information regarding the MSE_VAR module is in    ")
        print(" README_LEVEL_03.docx/README_LEVEL_03.pdf files under            ")
        print("  ~/diagnostics/ENSO_MSE/MSE_VAR/                                   ")
        print("=================================================================")

        if os.environ["ENSO_OBS"] == "1":
            print("=================================================================")
            print("  Calculation of Observational  Moist Static Energy Variances    ")
            print("=================================================================")
            os.system("python "+os.environ["POD_HOME"]+"/MSE_VAR/get_directories_OBS.py")
            os.system("python "+os.environ["POD_HOME"]+"/MSE_VAR/MSE_VAR_OBS.py")

        os.system("python "+os.environ["POD_HOME"]+"/MSE_VAR/get_directories.py")
        os.system("python "+os.environ["POD_HOME"]+"/MSE_VAR/MSE_VAR.py")

        print("=================================================================")
        print("         Moist Static Energy Variances  FINISHED                 ")
        print("=================================================================")

    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("MSE VARIANCE is NOT Executed as Expected!")
#####
# 4.  CMIP5 scatter plots
#
# ==================================================================================================
if os.environ["ENSO_SCATTER"] == "1":
    try:
        print("=================================================================")
        print(" Scripts is going to plot selected Scatter Plots                ")
        print(" The routine requires data input from COMPOSITE and MSE routines")
        print("=================================================================")

        print("=================================================================")
        print(" More detailed information regarding the SCATTER module is in    ")
        print(" README_LEVEL_04.docx/README_LEVEL_04.pdf files under            ")
        print(" ~/diagnostics/ENSO_MSE/SCATTER/                                    ")
        print("=================================================================")

        os.system("python "+os.environ["POD_HOME"]+"/SCATTER/check_input_files.py")
        os.system("python "+os.environ["POD_HOME"]+"/SCATTER/SCATTER.py")

        print("=================================================================")
        print("        Scatter Plot Routine   FINISHED                          ")
        print("=================================================================")

    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("MSE VARIANCE is NOT Executed as Expected!")

# ======================================================================
