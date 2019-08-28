# This file is part of the MJO_prop_amp module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# This script is not used by the diagnostic package (mdtf.py) in anyway
#   but only serves as a reference for MDTF members (developers of diagnostic modules)
# The following sections of code are exact replications of the last section of code
#   from each example diagnostic modules included in the code package
#   for finalizing the htmls


### EOF_500hPa (EOF_500hPa.py) ###
#============================================================
# Copy Template HTML File to appropriate directory
#============================================================
if os.path.isfile( os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/EOF_500hPa/EOF_500hPa.html")
   
os.system("cp "+os.environ["VARCODE"]+"/EOF_500hPa/EOF_500hPa.html "+os.environ["variab_dir"]+"/EOF_500hPa/.")

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
os.system("cp "+os.environ["VARDATA"]+"/EOF_500hPa/*.gif "+os.environ["variab_dir"]+"/EOF_500hPa/obs/.")



### Wheeler_Kiladis (Wheeler_Kiladis.py) ###
#============================================================
# set up template html file
#============================================================
if os.path.isfile( os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html")
   
os.system("cp "+os.environ["VARCODE"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/.")

os.system("cp "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html")
os.system("cat "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html")
os.system("cp "+os.environ["variab_dir"]+"/Wheeler_Kiladis/tmp.html "+os.environ["variab_dir"]+"/Wheeler_Kiladis/Wheeler_Kiladis.html")
os.system("rm -f "+os.environ["variab_dir"]+"/tmp.html")

#============================================================
# Add line to top level HTML file (index.html)
#============================================================
a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep Wheeler_Kiladis")
if a != 0:
   os.system("echo '<H3><font color=navy>Wavenumber-Frequency Power Spectra, see Wheeler and Kiladis, JAS, vol 56, 374-399, 1999 <A HREF=\"Wheeler_Kiladis/Wheeler_Kiladis.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# Rename PS files
#============================================================
files = os.listdir(os.environ["variab_dir"]+"/Wheeler_Kiladis/model/PS")
a = 0
while a < len(files):
   file0 = files[a]
   file1 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["rlut_var"]+"/rlut/g")   
   file2 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["pr_var"]+"/pr/g")  
   file3 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["omega500_var"]+"/omega500/g") 
   file4 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u200_var"]+"/u200/g") 
   file5 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u850_var"]+"/u850/g")

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



### precip_diurnal_cycle (precip_diurnal_cycle.py) ###
#============================================================
# Copy over template html file
#============================================================
if os.path.isfile( os.environ["variab_dir"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html")

os.system("cp "+os.environ["VARCODE"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html "+os.environ["variab_dir"]+"/precip_diurnal_cycle/.")

# move template html file
os.system("cp "+os.environ["variab_dir"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html "+os.environ["variab_dir"]+"/precip_diurnal_cycle/tmp.html")
os.system("cat "+os.environ["variab_dir"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/precip_diurnal_cycle/tmp.html")
os.system("cp "+os.environ["variab_dir"]+"/precip_diurnal_cycle/tmp.html "+os.environ["variab_dir"]+"/precip_diurnal_cycle/precip_diurnal_cycle.html")
os.system("rm -f "+os.environ["variab_dir"]+"/precip_diurnal_cycle/tmp.html")

#============================================================
# Add a line to the top level HTML file (index.html)
#============================================================
a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep precip_diurnal_cycle")
if a != 0:
   os.system("echo '<H3><font color=navy>Diurnal Cycle of Precipitation, diurnal cycle of precipitation by the model simulation is compared with TRMM observations, see Gervais et al., J. Climate, 5219-5239, 2014 <A HREF=\"precip_diurnal_cycle/precip_diurnal_cycle.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

#============================================================
# convert PS to png
#============================================================
files = os.listdir(os.environ["variab_dir"]+"/precip_diurnal_cycle/model/PS")
a = 0
while a < len(files):
   file1 = os.environ["variab_dir"]+"/precip_diurnal_cycle/model/PS/"+files[a]
   file2 = os.environ["variab_dir"]+"/precip_diurnal_cycle/model/"+files[a]
   os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
   a = a+1
if os.environ["save_ps"] == "0":
   os.system("rm -rf "+os.environ["variab_dir"]+"/precip_diurnal_cycle/model/PS/")
os.system("cp "+os.environ["VARDATA"]+"/precip_diurnal_cycle/*.png "+os.environ["variab_dir"]+"/precip_diurnal_cycle/obs/.")



### convective_transition_diag (convective_transition_diag.py) ###
# ======================================================================   
#  Copy & modify the template html   
# ======================================================================
# Copy template html (and delete old html if necessary)
if os.path.isfile( os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html" ):
   os.system("rm -f "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")

os.system("cp "+os.environ["VARCODE"]+"/convective_transition_diag/convective_transition_diag.html "+os.environ["variab_
dir"]+"/convective_transition_diag/.")

# Replace keywords in the copied html template if different bulk temperature or resolution are used
if os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] == "2":
   os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/_tave\./_qsat_int\./g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
os.system("mv "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")
if os.environ["RES"] != "1.00":
   os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/_res\=1\.00_/_res\="+os.environ["RES"]+"_/g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
   os.system("mv "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")

# Replace CASENAME so that the figures are correctly linked through the html
os.system("cp "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
os.system("cp "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")
os.system("rm -f "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")

a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep convective_transition_diag")
if a != 0:
   os.system("echo '<H3><font color=navy>Convective transition diagnostics <A HREF=\"convective_transition_diag/convective_transition_diag.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

# Convert PS to png
if os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/model"):
   files = os.listdir(os.environ["variab_dir"]+"/convective_transition_diag/model/PS")
   a = 0
   while a < len(files):
      file1 = os.environ["variab_dir"]+"/convective_transition_diag/model/PS/"+files[a]
      file2 = os.environ["variab_dir"]+"/convective_transition_diag/model/"+files[a]
      os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
      a = a+1
   if os.environ["save_ps"] == "0":
      os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/model/PS")
if os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/obs"):
   files = os.listdir(os.environ["variab_dir"]+"/convective_transition_diag/obs/PS")
   a = 0
   while a < len(files):
      file1 = os.environ["variab_dir"]+"/convective_transition_diag/obs/PS/"+files[a]
      file2 = os.environ["variab_dir"]+"/convective_transition_diag/obs/"+files[a]
      os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
      a = a+1
   if os.environ["save_ps"] == "0":
      os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/obs/PS")
