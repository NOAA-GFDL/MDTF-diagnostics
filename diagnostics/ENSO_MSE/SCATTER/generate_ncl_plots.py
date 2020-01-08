import os
import subprocess
import commands

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#  make the default plots  in NCL
#============================================================
def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
        Arguments:
            nclPlotFile (string) - full path to ncl plotting file name
    """

    # check if the nclPlotFile exists -
    # don't exit if it does not exists just print a warning.
    pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    # print( output ) 

    return 0

## print os.environ["POD_HOME"]
