# This file is part of the EOF_500hPa module of the MDTF code package (see LICENSE.txt)

#============================================================
# EOF of 500hPa Height Diagnostics
# Sample code to call NCL from python 
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
filename2 = os.environ["DATADIR"]+"/mon/"+os.environ["CASENAME"]+"."+os.environ["ps_var"]+".mon.nc"
print "Looking for"+filename1
if not os.path.isfile( filename1 ):
    print ("ERROR missing file "+filename1)
print "Looking for"+filename2
if not os.path.isfile( filename2 ):
    print ("ERROR missing file "+filename2)


if os.path.isfile( filename1 ) & os.path.isfile( filename2 ):
    print("height and surface pressure files found") 
    print("computing EOF of geopotential height anomalies of 500 hPa")

#============================================================
# Call NCL code here
#============================================================
    print("COMPUTING ANOMALIES")
    generate_ncl_plots(os.environ["POD_HOME"]+"/compute_anomalies.ncl")

    print(" N ATLANTIC EOF PLOT")
    generate_ncl_plots(os.environ["POD_HOME"]+"/eof_natlantic.ncl")

    print(" N PACIFIC EOF PLOT")
    generate_ncl_plots(os.environ["POD_HOME"]+"/eof_npacific.ncl")


else:
    print("height and surface pressure files NOT found, skip EOF of geopotential height anomalies of 500 hPa")        
