# This file is part of the Wheeler_Kiladis module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

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
if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis")

if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis/model"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis/model")

if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS")

if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/netCDF"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/netCDF")

if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis/obs"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis/obs")

if not os.path.exists(os.environ["variab_dir"]+"/Wheeler_Kiladis/obs/netCDF"):
   os.makedirs(os.environ["variab_dir"]+"/Wheeler_Kiladis/obs/netCDF")


print("COMPUTING THE SPACE-TIME SPECTRA")

#============================================================
# Check data exists and Call NCL code
#============================================================
os.chdir(os.environ["DATADIR"])

#OLR

if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ["rlut_var"]+".day.nc"):
   os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ["rlut_var"]+".day.nc"
   os.environ["MVAR"] = os.environ["rlut_var"]
   os.environ["LEV"] = "sfc"
   print("file of "+os.environ["rlut_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
   generate_ncl_plots(os.environ["VARCODE"]+"/Wheeler_Kiladis/wkSpaceTime_driver.ncl")
else:  
   print("file of "+os.environ["rlut_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#Precipitation

if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ["pr_var"]+".day.nc"):
   os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ["pr_var"]+".day.nc"
   os.environ["MVAR"] = os.environ["pr_var"]
   os.environ["LEV"] = "sfc"
   print("file of "+os.environ["pr_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
   generate_ncl_plots(os.environ["VARCODE"]+"/Wheeler_Kiladis/wkSpaceTime_driver.ncl")
else:  
   print("file of "+os.environ["pr_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#Omega500

if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ["omega500_var"]+".day.nc"):
   os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ["omega500_var"]+".day.nc"
   os.environ["MVAR"] = os.environ["omega500_var"]
   os.environ["LEV"] = "500"
   print("file of "+os.environ["omega500_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
   generate_ncl_plots(os.environ["VARCODE"]+"/Wheeler_Kiladis/wkSpaceTime_driver.ncl")
else:  
   print("file of "+os.environ["omega500_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#U200

if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ["u200_var"]+".day.nc"):
   os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ["u200_var"]+".day.nc"
   os.environ["MVAR"] = os.environ["u200_var"]
   os.environ["LEV"] = "200"
   print("file of "+os.environ["u200_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
   generate_ncl_plots(os.environ["VARCODE"]+"/Wheeler_Kiladis/wkSpaceTime_driver.ncl")
else:  
   print("file of "+os.environ["u200_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#U850

if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ["u850_var"]+".day.nc"):
   os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ["u850_var"]+".day.nc"
   os.environ["MVAR"] = os.environ["u850_var"]
   os.environ["LEV"] = "850"
   print("file of "+os.environ["u850_var"]+" for Wheeler-Kiladis plots found, computing wave spectra")
   generate_ncl_plots(os.environ["VARCODE"]+"/Wheeler_Kiladis/wkSpaceTime_driver.ncl")
else:  
   print("file of "+os.environ["u850_var"]+" for Wheeler-Kiladis plots NOT found, skip computing wave spectra")

#============================================================
# set up template html file
#============================================================
if os.path.isfile( os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html")
   
os.system("cp "+os.environ["VARCODE"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/.")

os.system("cp "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html")

os.system("cp "+os.environ["VARCODE"]+"/Wheeler_Kiladis/MDTF_Documentation_Wavenumber-Frequency.pdf "+os.environ["variab_dir"]+"/Wheeler_Kiladis/.")

os.system("cat "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html")
os.system("cp "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html")
os.system("rm -f "+os.environ["variab_dir"]+"/tmp.html")

#============================================================
# Add line to top level HTML file (index.html)
#============================================================
a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep Wheeler_Kiladis")
if a != 0:
   os.system("echo '<H3><font color=navy>Wavenumber-Frequency Power Spectra (Wheeler and Kiladis) <A HREF=\"Wheeler_Kiladis/Wheeler_Kiladis.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# Rename PS files
#============================================================
files = os.listdir(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS")
a = 0
while a < len(files):
   file0 = files[a]
   file1 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["rlut_var"]+"-sfc/rlut/g")   
   file2 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["pr_var"]+"-sfc/pr/g")  
   file3 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["omega500_var"]+"-500/omega500/g") 
   file4 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u200_var"]+"-200/u200/g") 
   file5 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u850_var"]+"-850/u850/g")

   if file0 != file1:
      os.system("mv -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file0+" "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file1)

   if file0 != file2:
      os.system("mv -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file0+" "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file2)

   if file0 != file3:
      os.system("mv -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file0+" "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file3)

   if file0 != file4:
      os.system("mv -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file0+" "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file4)

   if file0 != file5:
      os.system("mv -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file0+" "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+file5)
 
   a = a+1

#============================================================
# Convert PS to png
#============================================================
files = os.listdir(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS")
a = 0
while a < len(files):
   file1 = os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS/"+files[a]
   file2 = os.environ["variab_dir"]+"/Wheeler_Kiladis/model/"+files[a]
   os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
   a = a+1
if os.environ["save_ps"] == "0":
   os.system("rm -rf "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS")
os.system("cp "+os.environ["VARDATA"]+"/Wheeler_Kiladis/*.gif "+os.environ["variab_dir"]+"/Wheeler_Kiladis/obs/.")
os.system("cp "+os.environ["VARDATA"]+"/Wheeler_Kiladis/*.png "+os.environ["variab_dir"]+"/Wheeler_Kiladis/obs/.")

# delete netCDF files if requested
if os.environ["save_nc"] == "0":    
   os.system("rm -rf "+os.environ["variab_dir"]+"/Wheeler_Kiladis/obs/netCDF")
   os.system("rm -rf "+os.environ["variab_dir"]+"/Wheeler_Kiladis/model/netCDF")
