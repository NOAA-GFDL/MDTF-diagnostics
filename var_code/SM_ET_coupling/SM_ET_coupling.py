# This file is part of the SM_ET_coupling module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

#============================================================
# Coupling between soil moisture (SM) and evapotanspiration (ET) in summer
# Sample code to call R from python
# Code written by Alexis Berg
#
# This module calculates the correlations between SM and ET, as in Berg and Sheffield (2018), Fig.1a.
#
# Reference:
# Berg and Sheffield (2018), Soil moisture-evapotranspiration coupling in CMIP5 models: relationship with simulated climate and projections, Journal of Climate, 31(12), 4865-4878. 
#============================================================

import os
import subprocess

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#============================================================
def generate_R_plots(RPlotFile):
   """generate_plots_call - call a RPlotFile via subprocess call
   
   Arguments:
   RPlotFile (string) - full path to R plotting file name
   """
   # check if the RPlotFile exists - 
   # don't exit if it does not exists just print a warning.
   try:
      pipe = subprocess.Popen(['Rscript ' '--verbose ' '--vanilla {0}' .format(RPlotFile)]  , shell=True)#, stdout=subprocess.PIPE)
      output = pipe.communicate()[0]
      print('R routine {0} \n {1}'.format(RPlotFile,output))            
      while pipe.poll() is None:
         time.sleep(0.5)
   except OSError as e:
      print('WARNING',e.errno,e.strerror)

   return 0

if os.path.isfile( os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["mrsos_var"]+".mon.nc"):
      print("monthly soil moisture file found")

#if os.path.isfile( os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["mrsos_var"]+".mon.nc"):
#      print("monthly soil moisture file found")

#if os.path.isfile( os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["evspsbl_var"]+".mon.nc"):
#      print("monthly evapotranspiration file found")

      print("computing SM-ET coupling")

#============================================================
# Set up Directories
#============================================================
      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling")

      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling/model"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling/model")

      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling/model/PS"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling/model/PS")

      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling/model/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling/model/netCDF")

      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling/obs"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling/obs")

      if not os.path.exists(os.environ["variab_dir"]+"/SM_ET_coupling/obs/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/SM_ET_coupling/obs/netCDF")

#============================================================
# Call R code here
#============================================================
      print("--------- Starting SM_ET coupling generate figures (using R)----------------------------")
      if ( True ):
         generate_R_plots(os.environ["VARCODE"]+"/SM_ET_coupling/SM_ET_coupling.R")
      else:
         print("WARNING: For testing purposes, skipping SM_ET coupling figure generation")

      print("--------- Finished SM_ET coupling generate figures----------------------------")

#============================================================
# Copy over template html file
#============================================================

      if os.path.isfile( os.environ["variab_dir"]+"/SM_ET_coupling/SM_ET_coupling.html" ):
         os.system("rm -f "+os.environ["variab_dir"]+"/SM_ET_coupling/SM_ET_coupling.html")

      os.system("cp "+os.environ["VARCODE"]+"/SM_ET_coupling/SM_ET_coupling.html "+os.environ["variab_dir"]+"/SM_ET_coupling/.")

    #  os.system("cp "+os.environ["VARCODE"]+"/SM_ET_coupling/MDTF_Documentation_SM_ET_coupling.pdf "+os.environ["variab_dir"]+"/SM_ET_coupling/.")

      # move template html file
      os.system("cp "+os.environ["variab_dir"]+"/SM_ET_coupling/SM_ET_coupling.html "+os.environ["variab_dir"]+"/SM_ET_coupling/tmp.html")
      os.system("cat "+os.environ["variab_dir"]+"/SM_ET_coupling/SM_ET_coupling.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/SM_ET_coupling/tmp.html")
      os.system("cp "+os.environ["variab_dir"]+"/SM_ET_coupling/tmp.html "+os.environ["variab_dir"]+"/SM_ET_coupling/SM_ET_coupling.html")
      os.system("rm -f "+os.environ["variab_dir"]+"/SM_ET_coupling/tmp.html")

#============================================================
# Add a line to the top level HTML file (index.html)
#============================================================
      a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep SM_ET_coupling")
      if a != 0:
         os.system("echo '<H3><font color=navy> Coupling of Soil Moisture with Evapotranspiration <A HREF=\"SM_ET_coupling/SM_ET_coupling.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# convert PS to png
#============================================================
      files = os.listdir(os.environ["variab_dir"]+"/SM_ET_coupling/model/PS")
      a = 0
      while a < len(files):
         file1 = os.environ["variab_dir"]+"/SM_ET_coupling/model/PS/"+files[a]
         file2 = os.environ["variab_dir"]+"/SM_ET_coupling/model/"+files[a]
         os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
         a = a+1
      if os.environ["CLEAN"] == "1":
         os.system("rm -rf "+os.environ["variab_dir"]+"/SM_ET_coupling/model/PS/")

      os.system("cp "+os.environ["VARDATA"]+"/SM_ET_coupling/*.png "+os.environ["variab_dir"]+"/SM_ET_coupling/obs/.")


      print("--------- Finished SM_ET coupling webpage generation ----------------------------")
else:
      print("Monthly precipitation file NOT found, skip SM-ET coupling")            
