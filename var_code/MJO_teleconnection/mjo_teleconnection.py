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
#    /var_code/MJO_teleconnection
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
#     var_code/util/set_variables_CESM.py
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
import commands

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
   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/model"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/model")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/figures"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/figures")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/model/PS"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/model/PS")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/model/netCDF"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/model/netCDF")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/obs"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/obs")

   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/obs/netCDF"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/obs/netCDF")


   if not os.path.exists(os.environ["variab_dir"]+"/MJO_teleconnection/htmls"):
      os.makedirs(os.environ["variab_dir"]+"/MJO_teleconnection/htmls")

#======================================================================================
#      Calling a NCL script to calculate RMM index of a given model data
#======================================================================================
   os.environ["strtdy"] = os.environ["FIRSTYR"]+"0101"
   os.environ["lastdy"] = os.environ["LASTYR"] +"1231"

   os.chdir(os.environ["DATADIR"])

   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_RMM_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_geop_hgt_comp_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_prec_comp_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_U250_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_daig_Corr_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_EWR_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_fig1_MDTF.ncl")
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_teleconnection/mjo_diag_fig2_MDTF.ncl")
#============================================================
# set up template html file
#============================================================
   if os.path.isfile( os.environ["variab_dir"]+"/MJO_teleconnection/MJO_teleconnection.html" ):
      os.system("rm -f "+os.environ["variab_dir"]+"/MJO_teleconnection/MJO_teleconnection.html")

   os.system("cp "+os.environ["VARCODE"]+"/MJO_teleconnection/MJO_teleconnection.html "+os.environ["variab_dir"]+ "/MJO_teleconnection/")

   os.system("cp "+os.environ["VARCODE"]+"/MJO_teleconnection/MDTF_Documentation_MJO_teleconnection.pdf "+os.environ["variab_dir"]+"/MJO_teleconnection/.")
  
# 

   if os.path.isfile( os.environ["variab_dir"]+"/MJO_teleconnection/htmls/*.html" ):
      os.system("rm -f "+os.environ["variab_dir"]+"/MJO_teleconnection/htmls/*.html")
   os.system("cp "+os.environ["VARCODE"]+"/MJO_teleconnection/htmls/*.html "+os.environ["variab_dir"]+ "/MJO_teleconnection/htmls")
      

#============================================================
# Add line to top level HTML file (index.html)
#============================================================
   a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep MJO_teleconnection")
   if a != 0:
      os.system("echo '<H3><font color=navy>MJO Teleconnections Diagnostics, see Henderson et al., J. Climate, vol 30, No. 12, 4567-4587, 2017 <A HREF=\"MJO_teleconnection/MJO_teleconnection.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# convert eps to jpeg
#============================================================
   files = os.listdir(os.environ["variab_dir"]+"/MJO_teleconnection/figures")
   a = 0
   while a < len(files):
      file1 = os.environ["variab_dir"]+"/MJO_teleconnection/figures/"+files[a]
      file2 = os.environ["variab_dir"]+"/MJO_teleconnection/model/"+files[a]
      os.system("convert "+file1+" "+file2[:-3]+"jpeg")
      a = a+1

#============================================================
   print("-----------------------------------------------------------------------------")
   print("|----Execution of MJO Teleconnections diagnostics module is completed now----|")
   print("=============================================================================")
   print("Check: " + os.environ["variab_dir"])
   print( "now you can open index.html in browser to see the results " )
   print("-----------------------------------------------------------------------------")

else:
   print("Requested Input data file are not found, Please check input data directory ")
   print("check data directory and :" +os.environ["VARCODE"]+ "/util/set_variables_xxxx.py to set variable names" )  
   
