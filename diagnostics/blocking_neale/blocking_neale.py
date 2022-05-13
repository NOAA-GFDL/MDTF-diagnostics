# This file is part of the blocking_neale module of the MDTF code package (see LICENSE.txt)

#============================================================
# Rich Neale's Blocking Code
# Sample code to call NCL from python 
#============================================================

import os
import subprocess
import time

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#============================================================
# DRBDBG want to change the name of this!
def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0].decode()
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

#============================================================
# Call NCL code here
#============================================================
if not os.path.exists(os.path.join(os.environ['DATADIR'], 'day')):
    os.makedirs(os.path.join(os.environ['DATADIR'], 'day'))


print("blocking_neale.py calling blocking.ncl")
generate_ncl_plots(os.environ["POD_HOME"]+"/blocking.ncl")
   
print("blocking_neale.py finished.")
