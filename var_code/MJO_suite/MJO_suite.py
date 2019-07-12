# This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

#============================================================
# EOF of 500hPa Height Diagnostics
# Sample code to call NCL from python 
#============================================================

import os
import subprocess
# ------------------------------------------------------------------------
# Variables for mjo_diag (MJO propogation)

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#============================================================
print("Let us get started!!!")
def generate_ncl_plots(nclPlotFile):
   """generate_plots_call - call a nclPlotFile via subprocess call
   
   Arguments:
   nclPlotFile (string) - full path to ncl plotting file name
   """
   print("calling NCL")
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

#============================================================
# Set up directories
#============================================================
print("MJO suite using daily data")
if not os.path.exists(os.environ["variab_dir"]+"/MJO_suite/model"):
   os.makedirs(os.environ["variab_dir"]+"/MJO_suite/model")

if not os.path.exists(os.environ["variab_dir"]+"/MJO_suite/model/PS"):
   os.makedirs(os.environ["variab_dir"]+"/MJO_suite/model/PS")

if not os.path.exists(os.environ["variab_dir"]+"/MJO_suite/model/netCDF"):
   os.makedirs(os.environ["variab_dir"]+"/MJO_suite/model/netCDF")

if not os.path.exists(os.environ["variab_dir"]+"/MJO_suite/obs"):
   os.makedirs(os.environ["variab_dir"]+"/MJO_suite/obs")

if not os.path.exists(os.environ["variab_dir"]+"/MJO_suite/obs/netCDF"):
   os.makedirs(os.environ["variab_dir"]+"/MJO_suite/obs/netCDF")

#============================================================
# Call NCL code here
#============================================================
print("OBTAINING DAILY OUTPUT")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/daily_netcdf.ncl")

print("COMPUTING DAILY ANOMALIES")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/daily_anom.ncl")

print("COMPUTING MJO EOF")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_EOF.ncl")

print("MJO lag plots")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_lag_lat_lon.ncl")

print("MJO spectra")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_spectra.ncl")

if os.path.isfile( os.environ["variab_dir"]+"/MJO_suite/model/netCDF/MJO_PC_INDEX.nc"):
   print("WARNING: MJO_PC_INDEX.nc already exists!")
else:
   generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_EOF_cal.ncl")
   
print("MJO life cycle composite")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_life_cycle.ncl")
generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo_life_cycle_v2.ncl")

generate_ncl_plots(os.environ["VARCODE"]+"/MJO_suite/mjo.ncl")

#============================================================
# Copy Template HTML File to appropriate directory
#============================================================
if os.path.isfile( os.environ["variab_dir"]+"/MJO_suite/MJO_suite.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/MJO_suite/MJO_suite.html")
   
os.system("cp "+os.environ["VARCODE"]+"/MJO_suite/MJO_suite.html "+os.environ["variab_dir"]+"/MJO_suite/.")

os.system("cp "+os.environ["variab_dir"]+"/MJO_suite/MJO_suite.html "+os.environ["variab_dir"]+"/MJO_suite/tmp.html")
os.system("cp "+os.environ["VARCODE"]+"/MJO_suite/MDTF_Documentation_MJO_suite.pdf "+os.environ["variab_dir"]+"/MJO_suite/.")
os.system("cat "+os.environ["variab_dir"]+"/MJO_suite/MJO_suite.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/MJO_suite/tmp.html")
os.system("cp "+os.environ["variab_dir"]+"/MJO_suite/tmp.html "+os.environ["variab_dir"]+"/MJO_suite/MJO_suite.html")
os.system("rm -f "+os.environ["variab_dir"]+"/MJO_suite/tmp.html")

#============================================================
# Add to HTML File
#  This adds a line to the main html page (index.html)
#============================================================
a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep MJO_suite")
if a != 0:
   os.system("echo '<H3><font color=navy>MJO CLIVAR suite (NCAR) <A HREF=\"MJO_suite/MJO_suite.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# convert PS to png
#============================================================
files = os.listdir(os.environ["variab_dir"]+"/MJO_suite/model/PS")
a = 0
while a < len(files):
   file1 = os.environ["variab_dir"]+"/MJO_suite/model/PS/"+files[a]
   file2 = os.environ["variab_dir"]+"/MJO_suite/model/"+files[a]
   os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
   a = a+1
if os.environ["CLEAN"] == "1":
   os.system("rm -rf "+os.environ["variab_dir"]+"/MJO_suite/model/PS/")
os.system("cp "+os.environ["VARDATA"]+"/MJO_suite/*.gif "+os.environ["variab_dir"]+"/MJO_suite/obs/.")
os.system("cp "+os.environ["VARDATA"]+"/MJO_suite/*.png "+os.environ["variab_dir"]+"/MJO_suite/obs/.")
