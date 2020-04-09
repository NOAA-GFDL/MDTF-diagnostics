# This file is part of the MJO_teleconnection module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ==============================================================================================
# mjo_teleconnection.py
# ----------------------------------------------------------------------------------------------
#                      MJO Teleconnection Diagnostic package
# ----------------------------------------------------------------------------------------------  
#   Version 1 : 23-Jan-2018 Bohar Singh (CSU)
#   Contributors: Stephaniea Henderson (CSU), Bohar Singh (CSU), 
#   PI: Eric maloney (CSU)
#
# ------------------------------------------------------------------------------------------------
#   This module analyze eleconnection patterns associated with Madden-Julian Oscillations (MJO)  
#   for a given model data and comapere it with  10 models from phase 5 of the Coupled 
#   Model Intercomparison Project (CMIP5) 
#
#   -----------------------------------------------------------------------------------------------   
#                     Currently consists of following functionalities:
#   -----------------------------------------------------------------------------------------------
#    (1) Calculation of RMM indices, RMM index for new model wiill be saved in 
#        wkdir/casename/MJO_teleconnection/model/netCDF in txt format (mjo_diag_RMM_MDTF.ncl)
#    (2) Z250 phase composite for all MJO phases (mjo_diag_geop_hgt_comp_MDTF.ncl)
#    (3) Pattern correlation with observation (ERA-I Z250) (mjo_daig_Corr_MDTF.ncl)
#    (4) precpitation (30S-30N) phase composite for all MJO phases (mjo_diag_prec_comp_MDTF.ncl)
#    (5) Extended winter wave numeber-frequency power spectrum of precipitation to get the 
#        to get ratio of eastward and westward propagation power (mjo_diag_EWR_MDTF.ncl)
#    (6) Area averaged DJF mean U250 error (model-observation) over Pacific ocean (15N-80N,120E-120W)
#        (mjo_diag_U250_MDTF.ncl)
#
#   -----------------------------------------------------------------------------------------------
#    All scripts of this package can be found under
#    /diagnostics/MJO_teleconnection
#    Observed data and precalculated 10 CMIP5 models data can be cound under
#    /obs_data/MJO_teleconnection
#
#   The following Python packages are required:
#    os,glob,json,Dataset,numpy,scipy,matplotlib
#    & networkx,warnings,numba, netcdf4
#   Use Anaconda:
#    These Python packages are already included in the standard installation
#
#   ------------------------------------------------------------------------------------------------------
#   The following 5 3-D (lat-lon-time) model fields are required:
#     (1) precipitation rate (units: mm/s = kg/m^2/s) or mm/day with appropriate conversion 
#     (2) Outgoing Longwave radiation (units: w/m2)
#     (3) U850 wind (units: m/s) 
#     (4) U250 wind (units: m/s) (Note: U250 wind is used instead of u200 for RMM index calculation)  
#     (5) Z250 (m)
#     
#     Please change the variable names and conversion factor according to your data before running
#     MJO teleconnection diagnostic at :
#     src/config_<model name>.json
#     Please provide each input variable into a single file
#
#   -------------------------------------------------------------------------------------------------------
#   Referece:  Henderson et. al 2017 J. Climate  vol. 30 (12) pp 4567-4587
# =========================================================================================================
# OPEN SOURCE COPYRIGHT Agreement TBA
# ======================================================================
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
        print("Calling ",nclPlotFile)
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

# HACK for merging in SPEAR code before we have general level extraction working
if '850' in os.environ.get('u850_var',''):
    print('\tDEBUG: assuming 3D u,v ({})'.format(os.environ['u850_var']))
    os.environ['MDTF_3D_UV'] = '1'
else:
    print('\tDEBUG: assuming 4D u,v ({})'.format(os.environ['u850_var']))
    os.environ['MDTF_3D_UV'] = '0'
if '250' in os.environ.get('z250_var',''):
    print('\tDEBUG: assuming 3D z ({})'.format(os.environ['z250_var']))
    os.environ['MDTF_3D_Z'] = '1'
else:
    print('\tDEBUG: assuming 4D z ({})'.format(os.environ['z250_var']))
    os.environ['MDTF_3D_Z'] = '0'


print("=======================================================================")
print("    Execution of MJO Teleconnection Diagnotics is started from here")
print("-----------------------------------------------------------------------")
os.environ["prec_file"] = os.environ["CASENAME"]+"."+os.environ["pr_var"]+".day.nc"
os.environ["olr_file"]  = os.environ["CASENAME"]+"."+os.environ["rlut_var"]+".day.nc"
os.environ["u850_file"] = os.environ["CASENAME"]+"."+os.environ["u850_var"]+".day.nc"
os.environ["u250_file"] = os.environ["CASENAME"]+"."+os.environ["u250_var"]+".day.nc"
os.environ["z250_file"] = os.environ["CASENAME"]+"."+os.environ["z250_var"]+".day.nc"


if os.path.isfile( os.environ["DATADIR"]+"/day/"+os.environ["prec_file"]) & os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ ["olr_file"]) & os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["u850_file"]) & os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["u250_file"]) & os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["z250_file"]):

    print("Following input data file are found ")
    print(os.environ["prec_file"])
    print(os.environ["olr_file"])
    print(os.environ["u850_file"])
    print(os.environ["u250_file"])
    print(os.environ["z250_file"])
    print("-----------------------------------------------------------------------")      
#===================================================================================
#                               Set up directories
#===================================================================================

    if not os.path.exists(os.environ["WK_DIR"]+"/htmls"):
        os.makedirs(os.environ["WK_DIR"]+"/htmls")

#======================================================================================
#      Calling a NCL script to calculate RMM index of a given model data
#======================================================================================
    os.environ["strtdy"] = os.environ["FIRSTYR"]+"0101"
    os.environ["lastdy"] = os.environ["LASTYR"] +"1231"

    os.chdir(os.environ["DATADIR"])

    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_RMM_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_geop_hgt_comp_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_prec_comp_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_U250_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_daig_Corr_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_EWR_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_fig1_MDTF.ncl")
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_diag_fig2_MDTF.ncl")
#============================================================
# copy additional html files
#============================================================

    if os.path.isfile( os.environ["WK_DIR"]+"/htmls/*.html" ):
        os.system("rm -f "+os.environ["WK_DIR"]+"/htmls/*.html")
    os.system("cp "+os.environ["POD_HOME"]+"/htmls/*.html "+os.environ["WK_DIR"]+ "/htmls")
      

#============================================================
    print("-----------------------------------------------------------------------------")
    print("|----Execution of MJO Teleconnections diagnostics module is completed now----|")
    print("=============================================================================")
    print("Check: " + os.environ["WK_DIR"])
    print( "now you can open index.html in browser to see the results " )
    print("-----------------------------------------------------------------------------")

else:
    print("Requested Input data file are not found, Please check input data directory ")
    print("check data directory and /util/config_XXX.json to set variable names" )  
   
