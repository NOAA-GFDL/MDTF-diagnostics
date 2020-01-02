import os
import subprocess
import commands

#============================================================
# get_ncl_data  - call to get the input data 
#============================================================
def get_ncl_data(nclSourceFile):
    """get_ncl_data - call a nclPlotFile via subprocess call
        Arguments:
            get_ncl_data (string) - full path to ncl plotting file name
    """
    pipe = subprocess.Popen(['ncl {0}'.format(nclSourceFile)], shell=True, stdout=subprocess.PIPE)

    return 0

###########################
