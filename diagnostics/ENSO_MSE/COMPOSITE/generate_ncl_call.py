import os
import subprocess
import commands
import time

#============================================================
# generate_ncl_call - call a nclroutine via subprocess call
#============================================================
def generate_ncl_call( nclroutine):
    """generate_plots_call - call a nclPlotFile via subprocess call
        Arguments:
            nclPlotFile (string) - full path to ncl plotting file name
    """

    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclroutine)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
####      print out the NCL messages
#      print('NCL routine {0} \n {1}'.format(nclroutine,output))
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

## print os.environ["POD_HOME"]
