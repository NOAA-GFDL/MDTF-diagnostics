# This file is part of the EOF_500hPa module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

#============================================================
# EOF of 500hPa Height Diagnostics
# Sample code to call NCL from python 
#============================================================

import os
import subprocess

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

print "Entered "+__file__
filename1 = os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["zg_var"]+".mon.nc"
#filename2 = os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["ps_var"]+".mon.nc"
print "Looking for"+filename1
if not os.path.isfile( filename1 ):
   print ("ERROR missing file "+filename1)
#print "Looking for"+filename2
#if not os.path.isfile( filename2 ):
#   print ("ERROR missing file "+filename2)


#if os.path.isfile( filename1 ) & os.path.isfile( filename2 ):
#      print("height and surface pressure files found") 
if os.path.isfile( filename1): 
      print("geopotential height files found") 
      print("computing EOF of geopotential height anomalies of 500 hPa")
#============================================================
# Set up directories
#============================================================
      print("MAKE EOF PLOTS FROM MODEL MONTHLY DATA ")
      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model/PS"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model/PS")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model/netCDF")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/obs"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/obs")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/obs/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/obs/netCDF")

      print("computing EOF of geopotential height anomalies of 500 hPa")
#============================================================
# Set up directories
#============================================================
      print("MAKE EOF PLOTS FROM MODEL MONTHLY DATA ")
      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model/PS"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model/PS")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/model/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/model/netCDF")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/obs"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/obs")

      if not os.path.exists(os.environ["variab_dir"]+"/EOF_500hPa/obs/netCDF"):
         os.makedirs(os.environ["variab_dir"]+"/EOF_500hPa/obs/netCDF")

#============================================================
# Call NCL code here
#============================================================
      print("COMPUTING ANOMALIES")
      generate_ncl_plots(os.environ["VARCODE"]+"/EOF_500hPa/compute_anomalies.ncl")

      print(" N ATLANTIC EOF PLOT")
      generate_ncl_plots(os.environ["VARCODE"]+"/EOF_500hPa/eof_natlantic.ncl")

      print(" N PACIFIC EOF PLOT")
      generate_ncl_plots(os.environ["VARCODE"]+"/EOF_500hPa/eof_npacific.ncl")

#============================================================
# Copy Template HTML File to appropriate directory
#============================================================
      if os.path.isfile( os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html" ):
         os.system("rm -f "+os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html")
   
      os.system("cp "+os.environ["VARCODE"]+"/EOF_500hPa/EOF_500hPa.html "+os.environ["variab_dir"]+"/EOF_500hPa/.")
      os.system("cp "+os.environ["VARCODE"]+"/EOF_500hPa/MDTF_Documentation_EOF500.pdf "+os.environ["variab_dir"]+"/EOF_500hPa/.")
      os.system("cp "+os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html "+os.environ["variab_dir"]+"/EOF_500hPa/tmp.html")
      os.system("cat "+os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/EOF_500hPa/tmp.html")
      os.system("cp "+os.environ["variab_dir"]+"/EOF_500hPa/tmp.html "+os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html")
      os.system("rm -f "+os.environ["variab_dir"]+"/EOF_500hPa/tmp.html")

#============================================================
# Add to HTML File
#  This adds a line to the main html page (index.html)
#============================================================
      a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep EOF_500hPa")
      if a != 0:
         os.system("echo '<H3><font color=navy>EOF of geopotenitial height anomalies for 500 hPa <A HREF=\"EOF_500hPa/EOF_500hPa.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# convert PS to png
#============================================================
      files = os.listdir(os.environ["variab_dir"]+"/EOF_500hPa/model/PS")
      a = 0
      while a < len(files):
         file1 = os.environ["variab_dir"]+"/EOF_500hPa/model/PS/"+files[a]
         file2 = os.environ["variab_dir"]+"/EOF_500hPa/model/"+files[a]
         os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
         a = a+1
      if os.environ["save_ps"] == "0":
         os.system("rm -rf "+os.environ["variab_dir"]+"/EOF_500hPa/model/PS/")

      # delete netCDF files if requested
      if os.environ["save_nc"] == "0":    
         os.system("rm -rf "+os.environ["variab_dir"]+"/EOF_500hPa/obs/netCDF")
         os.system("rm -rf "+os.environ["variab_dir"]+"/EOF_500hPa/model/netCDF")

#============================================================
# Copy obs gifs into the expected location
#============================================================
      os.system("cp "+os.environ["VARDATA"]+"/EOF_500hPa/*.gif "+os.environ["variab_dir"]+"/EOF_500hPa/obs/.")


else:
      print("height and surface pressure files NOT found, skip EOF of geopotential height anomalies of 500 hPa")        
