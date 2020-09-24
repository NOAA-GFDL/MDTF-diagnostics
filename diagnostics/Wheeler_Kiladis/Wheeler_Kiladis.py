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
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

print("COMPUTING THE SPACE-TIME SPECTRA")

#============================================================
# Check data exists and Call NCL code
#============================================================
os.chdir(os.environ["DATADIR"])  # inputdata

#OLR

#orig
varlist = ["u200_var","u850_var","omega500_var","rlut_var","pr_var"]
#test  varlist = ["omega500_var"]


for var in varlist:
   print("starting var "+var)
   if os.path.isfile(os.environ["DATADIR"]+"/day/"+os.environ["CASENAME"]+"."+os.environ[var]+".day.nc"):
       os.environ["file_WK"] = os.environ["CASENAME"]+"."+os.environ[var]+".day.nc"
       os.environ["MVAR"] = os.environ[var]
       #print("file of "+os.environ[var]+" for Wheeler-Kiladis plots found, computing wave spectra")
       generate_ncl_plots(os.environ["POD_HOME"]+"/wkSpaceTime_driver.ncl")
   else:  
       print("WARNING: file not found ("+os.environ[var]+") skipping wave spectra computation")


#============================================================
# Rename PS files ; drb needs to use varlist also!
#============================================================
files = os.listdir(os.environ["WK_DIR"]+"/model/PS")
a = 0
while a < len(files):
    file0 = files[a]
    file1 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["rlut_var"]+"/rlut/g")   
    file2 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["pr_var"]+"/pr/g")  
    file3 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["omega500_var"]+"/omega500/g") 
    file4 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u200_var"]+"/u200/g") 
    file5 = commands.getoutput("echo "+file0+"|sed -e s/"+os.environ["u850_var"]+"/u850/g")

    if file0 != file1:
        os.system("mv -f "+os.environ["WK_DIR"]+"/model/PS/"+file0+" "+os.environ["WK_DIR"]+"/model/PS/"+file1)

    if file0 != file2:
        os.system("mv -f "+os.environ["WK_DIR"]+"/model/PS/"+file0+" "+os.environ["WK_DIR"]+"/model/PS/"+file2)

    if file0 != file3:
        os.system("mv -f "+os.environ["WK_DIR"]+"/model/PS/"+file0+" "+os.environ["WK_DIR"]+"/model/PS/"+file3)

    if file0 != file4:
        os.system("mv -f "+os.environ["WK_DIR"]+"/model/PS/"+file0+" "+os.environ["WK_DIR"]+"/model/PS/"+file4)

    if file0 != file5:
        os.system("mv -f "+os.environ["WK_DIR"]+"/model/PS/"+file0+" "+os.environ["WK_DIR"]+"/model/PS/"+file5)
 
    a = a+1
